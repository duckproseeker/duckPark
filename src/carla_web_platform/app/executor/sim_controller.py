from __future__ import annotations

import logging
import time
import traceback
from collections.abc import Callable
from typing import Any

from app.core.config import Settings
from app.core.models import EventLevel, RunEvent, RunStatus
from app.executor.carla_client import CarlaClient
from app.executor.recorder import RecorderManager
from app.executor.scenario_adapter import ScenarioAdapter
from app.executor.telemetry import TelemetryCollector
from app.scenario.runtime import ScenarioRuntimeContext
from app.scenario.validators import validate_descriptor
from app.storage.artifact_store import ArtifactStore
from app.storage.run_store import RunStore
from app.utils.time_utils import now_utc

logger = logging.getLogger(__name__)


class SimController:
    """Execution plane: own CARLA lifecycle and single tick control authority."""

    def __init__(
        self,
        settings: Settings,
        run_store: RunStore,
        artifact_store: ArtifactStore,
        client_factory: Callable[[str, int, float, int], CarlaClient] = CarlaClient,
    ) -> None:
        self._settings = settings
        self._run_store = run_store
        self._artifact_store = artifact_store
        self._client_factory = client_factory
        self._scenario_adapter = ScenarioAdapter()
        self._recorder = RecorderManager()

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

    def execute_run(self, run_id: str) -> None:
        run = self._run_store.get(run_id)
        descriptor = validate_descriptor(run.descriptor)

        if run.status != RunStatus.QUEUED:
            logger.warning("Skip run %s because status=%s", run_id, run.status)
            return

        if run.cancel_requested:
            self._transition(run_id, RunStatus.CANCELED, set_ended_at=True)
            self._emit_event(run_id, "SCENARIO_COMPLETED", "运行在执行前被取消")
            return

        telemetry = TelemetryCollector(
            run_id, descriptor.scenario_name, descriptor.map_name
        )
        carla_client: CarlaClient | None = None
        context: ScenarioRuntimeContext | None = None
        failure_reason: str | None = None
        final_status: RunStatus = RunStatus.COMPLETED

        try:
            self._transition(run_id, RunStatus.STARTING)
            self._emit_event(run_id, "RUN_STARTING", "executor 开始启动运行")

            if not descriptor.sync.enabled:
                raise RuntimeError(
                    "sync.enabled must be true; executor keeps single tick authority"
                )

            carla_client = self._client_factory(
                self._settings.carla_host,
                self._settings.carla_port,
                self._settings.carla_timeout_seconds,
                self._settings.traffic_manager_port,
            )
            carla_client.connect()
            self._emit_event(run_id, "CARLA_CONNECTED", "已连接 CARLA")

            carla_client.load_map(descriptor.map_name)
            self._emit_event(
                run_id,
                "MAP_LOADED",
                "地图加载完成",
                payload={"map_name": descriptor.map_name},
            )

            carla_client.set_weather(descriptor.weather.preset)
            carla_client.configure_world_sync(True, descriptor.sync.fixed_delta_seconds)
            self._emit_event(
                run_id,
                "WORLD_SYNC_ENABLED",
                "World 已启用 synchronous mode",
                payload={"fixed_delta_seconds": descriptor.sync.fixed_delta_seconds},
            )

            if descriptor.traffic.enabled:
                carla_client.configure_tm_sync(True)
                self._emit_event(
                    run_id, "TM_SYNC_ENABLED", "Traffic Manager 已启用同步模式"
                )

            ego_spawn = carla_client.spawn_ego_vehicle(
                descriptor.ego_vehicle.blueprint,
                descriptor.ego_vehicle.spawn_point.model_dump(mode="python"),
            )
            ego_vehicle = ego_spawn.actor
            self._emit_event(
                run_id,
                "EGO_SPAWNED",
                "Ego 车辆生成成功",
                payload={
                    "blueprint": descriptor.ego_vehicle.blueprint,
                    "spawn_source": ego_spawn.source,
                    "requested_spawn_point": ego_spawn.requested_spawn_point,
                    "resolved_spawn_point": ego_spawn.resolved_spawn_point,
                    "distance_to_requested_m": ego_spawn.distance_to_requested_m,
                    "fallback_index": ego_spawn.fallback_index,
                },
            )

            context = ScenarioRuntimeContext(
                run_id=run_id,
                descriptor=descriptor,
                carla_client=carla_client,
                ego_vehicle=ego_vehicle,
            )
            self._scenario_adapter.setup(context)

            self._recorder.start(
                run_id, descriptor, carla_client, self._artifact_store.run_dir(run_id)
            )

            self._transition(run_id, RunStatus.RUNNING, set_started_at=True)
            self._emit_event(run_id, "SCENARIO_STARTED", "场景执行开始")

            timeout_seconds = descriptor.termination.timeout_seconds
            max_ticks = int(timeout_seconds / descriptor.sync.fixed_delta_seconds)
            viewer_friendly_sleep = 0.0
            if descriptor.debug.viewer_friendly:
                # Debug mode only: slightly slow down wall-clock speed for easier manual observation.
                viewer_friendly_sleep = max(
                    0.0, min(descriptor.sync.fixed_delta_seconds * 0.5, 0.05)
                )
                self._emit_event(
                    run_id,
                    "DEBUG_VIEWER_FRIENDLY_ENABLED",
                    "已启用 viewer_friendly 调试模式",
                    payload={"sleep_seconds_per_tick": viewer_friendly_sleep},
                )

            for tick_count in range(max_ticks):
                latest = self._run_store.get(run_id)
                if latest.stop_requested or latest.cancel_requested:
                    self._transition(run_id, RunStatus.STOPPING)
                    self._emit_event(run_id, "RUN_STOPPING", "运行进入 STOPPING")
                    break

                tick_result = carla_client.tick()
                telemetry.on_tick(tick_result.frame, tick_result.sim_time)
                self._scenario_adapter.on_tick(
                    context,
                    tick_count=tick_count,
                    sim_time=tick_result.sim_time,
                )
                if viewer_friendly_sleep > 0.0:
                    time.sleep(viewer_friendly_sleep)

            latest = self._run_store.get(run_id)
            if latest.cancel_requested:
                final_status = RunStatus.CANCELED
            elif latest.stop_requested and latest.status == RunStatus.STOPPING:
                final_status = RunStatus.COMPLETED
            else:
                final_status = RunStatus.COMPLETED

            self._emit_event(
                run_id,
                "SCENARIO_COMPLETED",
                "场景执行循环结束",
                payload={"final_status": final_status.value},
            )
        except Exception as exc:  # noqa: BLE001
            failure_reason = str(exc)
            final_status = RunStatus.FAILED
            logger.error("Run %s failed:\n%s", run_id, traceback.format_exc())
            self._emit_event(
                run_id,
                "RUN_FAILED",
                "运行因异常失败",
                payload={"error": failure_reason},
                level=EventLevel.ERROR,
            )
        finally:
            self._emit_event(run_id, "CLEANUP_STARTED", "开始清理资源")

            if context is not None:
                try:
                    self._scenario_adapter.teardown(context)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Scenario teardown failed for run %s: %s", run_id, exc
                    )

            spawned_count = 0
            if carla_client is not None:
                try:
                    self._recorder.stop(carla_client)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Recorder stop failed for run %s: %s", run_id, exc)

                try:
                    spawned_count = carla_client.spawned_actor_count()
                    carla_client.cleanup()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("CARLA cleanup failed for run %s: %s", run_id, exc)

            self._emit_event(run_id, "CLEANUP_FINISHED", "资源清理完成")

            metrics = telemetry.finalize(
                final_status=final_status,
                failure_reason=failure_reason,
                spawned_actors_count=spawned_count,
            )
            self._artifact_store.write_metrics(metrics)

            run_after = self._run_store.get(run_id)
            if run_after.status in {
                RunStatus.COMPLETED,
                RunStatus.CANCELED,
                RunStatus.FAILED,
            }:
                self._artifact_store.write_status(run_after)
            elif final_status == RunStatus.FAILED:
                self._transition(
                    run_id,
                    RunStatus.FAILED,
                    error_reason=failure_reason,
                    set_ended_at=True,
                )
            else:
                if (
                    run_after.status == RunStatus.STOPPING
                    and final_status == RunStatus.CANCELED
                ):
                    self._transition(run_id, RunStatus.CANCELED, set_ended_at=True)
                else:
                    self._transition(run_id, RunStatus.COMPLETED, set_ended_at=True)
