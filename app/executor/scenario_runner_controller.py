from __future__ import annotations

import json
import logging
import os
import selectors
import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.core.models import EventLevel, RunEvent, RunMetrics, RunStatus
from app.executor.carla_client import CarlaClient
from app.executor.sensor_recorder import SensorRecorder, SensorRecorderResult
from app.scenario.official_runner import (
    build_scenario_runner_pythonpath,
    resolve_official_xosc_path,
    scenario_runner_ready,
    scenario_runner_runtime_issues,
)
from app.scenario.validators import validate_descriptor
from app.storage.artifact_store import ArtifactStore
from app.storage.run_store import RunStore
from app.utils.time_utils import now_utc

logger = logging.getLogger(__name__)


class ScenarioRunnerController:
    """Execution path backed by the official ScenarioRunner process."""

    def __init__(
        self,
        settings: Settings,
        run_store: RunStore,
        artifact_store: ArtifactStore,
        heartbeat_callback: Callable[[str], None] | None = None,
    ) -> None:
        self._settings = settings
        self._run_store = run_store
        self._artifact_store = artifact_store
        self._heartbeat_callback = heartbeat_callback

    def _emit_event(
        self,
        run_id: str,
        event_type: str,
        message: str,
        payload: dict[str, Any] | None = None,
        level: EventLevel = EventLevel.INFO,
    ) -> None:
        event = RunEvent(
            timestamp=now_utc(),
            run_id=run_id,
            level=level,
            event_type=event_type,
            message=message,
            payload=payload or {},
        )
        self._artifact_store.append_event(event)
        self._artifact_store.append_run_log(
            run_id,
            f"[{event.timestamp.isoformat()}] {event.level.value} {event.event_type} {event.message}",
        )

    def _transition(
        self,
        run_id: str,
        target: RunStatus,
        error_reason: str | None = None,
        set_started_at: bool = False,
        set_ended_at: bool = False,
    ) -> None:
        run = self._run_store.transition(
            run_id,
            target,
            error_reason=error_reason,
            set_started_at=set_started_at,
            set_ended_at=set_ended_at,
        )
        self._artifact_store.write_status(run)

    def _notify_running_heartbeat(self, run_id: str) -> None:
        if self._heartbeat_callback is not None:
            self._heartbeat_callback(run_id)

    def _resolve_runtime_xosc_path(self, scenario_source: dict[str, Any]) -> Path:
        missing_path: str | None = None
        for key in ("generated_xosc_path", "resolved_xosc_path"):
            candidate = str(scenario_source.get(key) or "").strip()
            if not candidate:
                continue
            path = Path(candidate)
            if path.exists():
                return path
            missing_path = candidate

        relative_xosc_path = str(
            scenario_source.get("relative_xosc_path")
            or scenario_source.get("source_file")
            or ""
        ).strip()
        if relative_xosc_path:
            xosc_path = resolve_official_xosc_path(relative_xosc_path, self._settings)
            if xosc_path is not None:
                return xosc_path
            missing_path = relative_xosc_path

        if missing_path is not None:
            raise RuntimeError(f"找不到 OpenSCENARIO 文件: {missing_path}")
        raise RuntimeError("run 缺少 OpenSCENARIO 文件路径")

    def _resolve_runtime_config_path(self, scenario_source: dict[str, Any]) -> Path:
        for key in ("generated_config_path", "config_path"):
            candidate = str(scenario_source.get(key) or "").strip()
            if not candidate:
                continue
            path = Path(candidate)
            if path.exists():
                return path
        raise RuntimeError("run 缺少 Python Scenario 配置文件路径")

    def _build_runtime(
        self,
        run_id: str,
        run: Any,
        descriptor: Any,
    ) -> tuple[list[str], Path, dict[str, str]]:
        if not scenario_runner_ready(self._settings):
            issues = scenario_runner_runtime_issues(self._settings)
            raise RuntimeError(
                "ScenarioRunner 环境未就绪: " + "; ".join(issues)
            )

        scenario_source = run.scenario_source or {}
        launch_mode = str(scenario_source.get("launch_mode") or "openscenario").strip() or "openscenario"

        scenario_runner_root = self._settings.scenario_runner_root
        assert scenario_runner_root is not None
        scenario_runner_script = scenario_runner_root / "scenario_runner.py"
        if not scenario_runner_script.exists():
            raise RuntimeError(f"找不到 scenario_runner.py: {scenario_runner_script}")

        frame_rate = max(1, round(1.0 / descriptor.sync.fixed_delta_seconds))
        output_dir = self._artifact_store.run_dir(run_id) / "outputs" / "scenario_runner"
        output_dir.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        pythonpath_entries = build_scenario_runner_pythonpath(self._settings)
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = os.pathsep.join(
            [*pythonpath_entries, *([existing_pythonpath] if existing_pythonpath else [])]
        )

        command = [
            self._settings.scenario_runner_python,
            str(scenario_runner_script),
            "--host",
            self._settings.carla_host,
            "--port",
            str(self._settings.carla_port),
            "--trafficManagerPort",
            str(self._settings.traffic_manager_port),
            "--timeout",
            str(self._settings.carla_timeout_seconds),
            "--sync",
            "--frameRate",
            str(frame_rate),
            "--output",
            "--json",
            "--outputDir",
            str(output_dir),
            "--reloadWorld",
        ]
        if launch_mode == "python_scenario":
            scenario_class = str(scenario_source.get("scenario_class") or "").strip()
            if not scenario_class:
                raise RuntimeError("run 缺少 Python Scenario class")
            config_path = self._resolve_runtime_config_path(scenario_source)
            additional_scenario_path = str(
                scenario_source.get("additional_scenario_path") or ""
            ).strip()
            if not additional_scenario_path:
                raise RuntimeError("run 缺少 additional_scenario_path")
            command[2:2] = [
                "--scenario",
                scenario_class,
                "--configFile",
                str(config_path),
                "--additionalScenario",
                additional_scenario_path,
            ]
        else:
            xosc_path = self._resolve_runtime_xosc_path(scenario_source)
            command[2:2] = ["--openscenario", str(xosc_path)]
        return command, output_dir, env

    def _spawn_background_traffic(self, run_id: str, descriptor: Any) -> CarlaClient | None:
        requested_vehicle_count = max(0, int(descriptor.traffic.num_vehicles))
        requested_walker_count = max(0, int(descriptor.traffic.num_walkers))
        if requested_vehicle_count == 0 and requested_walker_count == 0:
            return None

        self._emit_event(
            run_id,
            "BACKGROUND_TRAFFIC_STARTING",
            "正在补充背景交通参与者",
            payload={
                "requested_vehicle_count": requested_vehicle_count,
                "requested_walker_count": requested_walker_count,
                "traffic_manager_port": self._settings.traffic_manager_port,
            },
        )

        background_timeout_seconds = min(
            float(self._settings.carla_timeout_seconds),
            5.0,
        )
        background_tm_port = self._settings.traffic_manager_port
        last_error: Exception | None = None
        client: CarlaClient | None = None
        spawned_vehicles: list[Any] = []
        spawned_walkers: list[Any] = []

        for attempt in range(3):
            client = CarlaClient(
                self._settings.carla_host,
                self._settings.carla_port,
                background_timeout_seconds,
                background_tm_port,
            )
            try:
                time.sleep(2.0 if attempt == 0 else 1.5)
                self._notify_running_heartbeat(run_id)
                client.connect()
                spawned_vehicles = (
                    client.spawn_traffic_vehicles(requested_vehicle_count, autopilot=True)
                    if requested_vehicle_count > 0
                    else []
                )
                spawned_walkers = (
                    client.spawn_traffic_walkers(requested_walker_count)
                    if requested_walker_count > 0
                    else []
                )
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                client.cleanup()
                client = None
                error_text = str(exc).lower()
                if "bind error" in error_text and attempt < 2:
                    self._artifact_store.append_run_log(
                        run_id,
                        "[scenario_runner] WARNING background traffic tm not ready; retrying",
                    )
                    continue
                self._artifact_store.append_run_log(
                    run_id,
                    f"[scenario_runner] WARNING background traffic failed: {exc}",
                )
                self._emit_event(
                    run_id,
                    "BACKGROUND_TRAFFIC_FAILED",
                    "背景交通补充失败，场景将继续执行",
                    payload={"error": str(exc)},
                    level=EventLevel.WARNING,
                )
                return None

        if client is None:
            self._artifact_store.append_run_log(
                run_id,
                f"[scenario_runner] WARNING background traffic failed: {last_error}",
            )
            self._emit_event(
                run_id,
                "BACKGROUND_TRAFFIC_FAILED",
                "背景交通补充失败，场景将继续执行",
                payload={"error": str(last_error) if last_error is not None else "unknown"},
                level=EventLevel.WARNING,
            )
            return None

        self._emit_event(
            run_id,
            "BACKGROUND_TRAFFIC_READY",
            "背景交通参与者已注入运行世界",
            payload={
                "requested_vehicle_count": requested_vehicle_count,
                "spawned_vehicle_count": len(spawned_vehicles),
                "requested_walker_count": requested_walker_count,
                "spawned_walker_count": len(spawned_walkers),
                "traffic_manager_port": background_tm_port,
            },
        )
        return client

    def _start_sensor_recording(
        self, run_id: str, descriptor: Any
    ) -> tuple[SensorRecorder | None, SensorRecorderResult | None]:
        if not getattr(descriptor.sensors, "enabled", False) or not descriptor.sensors.sensors:
            return None, None

        recorder = SensorRecorder(
            host=self._settings.carla_host,
            port=self._settings.carla_port,
            timeout_seconds=self._settings.carla_timeout_seconds,
            output_root=self._artifact_store.run_dir(run_id) / "outputs" / "sensors",
        )
        self._emit_event(
            run_id,
            "SENSOR_RECORDING_STARTING",
            "正在挂载传感器并准备采集",
            payload={
                "profile_name": descriptor.sensors.profile_name,
                "sensor_count": len(descriptor.sensors.sensors),
            },
        )
        result = recorder.start(descriptor)
        self._emit_event(
            run_id,
            "SENSOR_RECORDING_READY",
            "传感器采集已开始",
            payload={
                "profile_name": result.profile_name,
                "sensor_count": result.sensor_count,
                "output_root": str(result.output_root),
            },
        )
        return recorder, result

    def _append_process_output(self, run_id: str, process: subprocess.Popen[str]) -> None:
        self._append_process_output_with_callback(run_id, process, line_callback=None)

    def _append_process_output_with_callback(
        self,
        run_id: str,
        process: subprocess.Popen[str],
        line_callback: Callable[[str], None] | None = None,
    ) -> None:
        stdout = process.stdout
        if stdout is None:
            return

        selector = selectors.DefaultSelector()
        selector.register(stdout, selectors.EVENT_READ)
        last_heartbeat_monotonic = 0.0
        try:
            while True:
                latest = self._run_store.get(run_id)
                if latest.stop_requested or latest.cancel_requested:
                    self._transition(run_id, RunStatus.STOPPING)
                    self._emit_event(run_id, "RUN_STOPPING", "官方 ScenarioRunner 收到停止请求")
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    return

                if process.poll() is not None:
                    break

                now = time.monotonic()
                if now - last_heartbeat_monotonic >= 1.0:
                    self._notify_running_heartbeat(run_id)
                    last_heartbeat_monotonic = now

                for key, _ in selector.select(timeout=0.3):
                    line = key.fileobj.readline()
                    if line:
                        self._notify_running_heartbeat(run_id)
                        if line_callback is not None:
                            line_callback(line.rstrip())
                        self._artifact_store.append_run_log(
                            run_id, f"[scenario_runner] {line.rstrip()}"
                        )

            for line in stdout:
                if line:
                    self._notify_running_heartbeat(run_id)
                    if line_callback is not None:
                        line_callback(line.rstrip())
                    self._artifact_store.append_run_log(
                        run_id, f"[scenario_runner] {line.rstrip()}"
                    )
        finally:
            selector.close()

    def _load_summary_payload(
        self, output_dir: Path
    ) -> tuple[Path | None, dict[str, Any] | None]:
        candidate_paths = sorted(
            output_dir.glob("*.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for path in candidate_paths:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                return path, payload
        return None, None

    @staticmethod
    def _summary_failure_reason(summary_payload: dict[str, Any]) -> str | None:
        success = summary_payload.get("success")
        if success is not False:
            return None

        failed_criteria: list[str] = []
        criteria = summary_payload.get("criteria")
        if isinstance(criteria, list):
            for item in criteria:
                if not isinstance(item, dict):
                    continue
                if item.get("success", True):
                    continue
                name = str(item.get("name") or "").strip()
                if name:
                    failed_criteria.append(name)

        if failed_criteria:
            return "scenario_runner reported unsuccessful criteria: " + ", ".join(
                failed_criteria
            )
        return "scenario_runner reported success=false"

    def execute_run(self, run_id: str) -> None:
        run = self._run_store.get(run_id)
        if run.status != RunStatus.QUEUED:
            logger.warning("Skip scenario_runner run %s because status=%s", run_id, run.status)
            return

        if run.cancel_requested:
            self._transition(run_id, RunStatus.CANCELED, set_ended_at=True)
            self._emit_event(run_id, "SCENARIO_COMPLETED", "运行在执行前被取消")
            return

        final_status = RunStatus.COMPLETED
        failure_reason: str | None = None
        metrics = RunMetrics(
            run_id=run_id,
            scenario_name=run.scenario_name,
            map_name=run.map_name,
            start_time=now_utc(),
        )
        wall_start = time.monotonic()
        process: subprocess.Popen[str] | None = None
        background_traffic_client: CarlaClient | None = None
        background_traffic_thread: threading.Thread | None = None
        sensor_recorder: SensorRecorder | None = None
        sensor_thread: threading.Thread | None = None
        sensor_recorder_error: str | None = None

        try:
            descriptor = validate_descriptor(run.descriptor)
            self._transition(run_id, RunStatus.STARTING)
            self._emit_event(run_id, "RUN_STARTING", "官方 ScenarioRunner 准备启动")

            command, output_dir, env = self._build_runtime(run_id, run, descriptor)
            self._emit_event(
                run_id,
                "SCENARIO_RUNNER_COMMAND_READY",
                "官方 ScenarioRunner 命令已构建",
                payload={
                    "command": command,
                    "output_dir": str(output_dir),
                    "execution_backend": run.execution_backend,
                },
            )

            process = subprocess.Popen(
                command,
                cwd=str(self._settings.scenario_runner_root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            self._transition(run_id, RunStatus.RUNNING, set_started_at=True)
            self._notify_running_heartbeat(run_id)
            self._emit_event(run_id, "SCENARIO_STARTED", "官方 ScenarioRunner 已启动")

            if getattr(descriptor.sensors, "enabled", False) and descriptor.sensors.sensors:
                def _sensor_worker() -> None:
                    nonlocal sensor_recorder, sensor_recorder_error
                    try:
                        sensor_recorder, _ = self._start_sensor_recording(run_id, descriptor)
                    except Exception as exc:  # noqa: BLE001
                        sensor_recorder_error = str(exc)
                        self._artifact_store.append_run_log(
                            run_id,
                            f"[scenario_runner] ERROR sensor recorder failed: {exc}",
                        )
                        self._emit_event(
                            run_id,
                            "SENSOR_RECORDING_FAILED",
                            "传感器采集启动失败",
                            payload={"error": str(exc)},
                            level=EventLevel.ERROR,
                        )

                sensor_thread = threading.Thread(
                    target=_sensor_worker,
                    name=f"sensor-recorder-{run_id}",
                    daemon=True,
                )
                sensor_thread.start()

            background_traffic_requested = bool(
                int(descriptor.traffic.num_vehicles) > 0
                or int(descriptor.traffic.num_walkers) > 0
            )
            background_traffic_ready = threading.Event()

            if background_traffic_requested:

                def _background_traffic_worker() -> None:
                    nonlocal background_traffic_client
                    if not background_traffic_ready.wait(timeout=20.0):
                        return
                    background_traffic_client = self._spawn_background_traffic(
                        run_id, descriptor
                    )

                background_traffic_thread = threading.Thread(
                    target=_background_traffic_worker,
                    name=f"background-traffic-{run_id}",
                    daemon=True,
                )
                background_traffic_thread.start()

            def _on_process_line(line: str) -> None:
                if not background_traffic_requested or background_traffic_ready.is_set():
                    return
                normalized = line.lower()
                if (
                    "preparing scenario" in normalized
                    or "scenariomanager: running scenario" in normalized
                ):
                    background_traffic_ready.set()

            self._append_process_output_with_callback(
                run_id,
                process,
                line_callback=_on_process_line,
            )
            return_code = process.wait()
            summary_path, summary_payload = self._load_summary_payload(output_dir)
            if sensor_thread is not None:
                sensor_thread.join(timeout=2.0)
            if background_traffic_thread is not None:
                background_traffic_thread.join(timeout=2.0)

            latest = self._run_store.get(run_id)
            if latest.cancel_requested:
                final_status = RunStatus.CANCELED
            elif latest.stop_requested and latest.status == RunStatus.STOPPING:
                final_status = RunStatus.COMPLETED
            elif sensor_recorder_error is not None:
                final_status = RunStatus.FAILED
                failure_reason = f"sensor recorder failed: {sensor_recorder_error}"
            elif return_code != 0:
                final_status = RunStatus.FAILED
                failure_reason = f"scenario_runner exited with code {return_code}"
            elif summary_payload is None or summary_path is None:
                final_status = RunStatus.FAILED
                failure_reason = (
                    "scenario_runner exited without result summary JSON; "
                    "run likely failed before producing outputs"
                )
                self._artifact_store.append_run_log(
                    run_id,
                    "[scenario_runner] ERROR no summary JSON found after process exit",
                )
            else:
                self._emit_event(
                    run_id,
                    "SCENARIO_RESULTS_READY",
                    "ScenarioRunner 结果摘要已生成",
                    payload={
                        "summary_path": str(summary_path),
                        "success": summary_payload.get("success"),
                    },
                )
                failure_reason = self._summary_failure_reason(summary_payload)
                if failure_reason is not None:
                    final_status = RunStatus.FAILED
        except Exception as exc:  # noqa: BLE001
            final_status = RunStatus.FAILED
            failure_reason = str(exc)
            self._artifact_store.append_run_log(run_id, f"[scenario_runner] ERROR {exc}")
            self._emit_event(
                run_id,
                "SCENARIO_FAILED",
                "官方 ScenarioRunner 执行失败",
                payload={"error": str(exc)},
                level=EventLevel.ERROR,
            )
        finally:
            if sensor_recorder is not None:
                try:
                    sensor_recorder.stop()
                    self._emit_event(
                        run_id,
                        "SENSOR_RECORDING_STOPPED",
                        "传感器采集已停止",
                    )
                except Exception as exc:  # noqa: BLE001
                    self._artifact_store.append_run_log(
                        run_id,
                        f"[scenario_runner] WARNING sensor recorder cleanup failed: {exc}",
                    )
            if background_traffic_client is not None:
                try:
                    background_traffic_client.cleanup()
                except Exception as exc:  # noqa: BLE001
                    self._artifact_store.append_run_log(
                        run_id,
                        f"[scenario_runner] WARNING background traffic cleanup failed: {exc}",
                    )
            metrics.end_time = now_utc()
            metrics.final_status = final_status
            metrics.failure_reason = failure_reason
            metrics.wall_time = time.monotonic() - wall_start
            self._artifact_store.write_metrics(metrics)

            if final_status == RunStatus.FAILED:
                self._transition(
                    run_id,
                    RunStatus.FAILED,
                    error_reason=failure_reason,
                    set_ended_at=True,
                )
                self._emit_event(
                    run_id,
                    "SCENARIO_COMPLETED",
                    "官方 ScenarioRunner 结束，结果为 FAILED",
                    payload={"error_reason": failure_reason},
                    level=EventLevel.ERROR,
                )
            elif final_status == RunStatus.CANCELED:
                self._transition(run_id, RunStatus.CANCELED, set_ended_at=True)
                self._emit_event(run_id, "SCENARIO_COMPLETED", "运行已取消")
            else:
                self._transition(run_id, RunStatus.COMPLETED, set_ended_at=True)
                self._emit_event(run_id, "SCENARIO_COMPLETED", "官方 ScenarioRunner 执行完成")

            run_after = self._run_store.get(run_id)
            self._artifact_store.write_status(run_after)
