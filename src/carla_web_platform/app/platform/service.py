from __future__ import annotations

import json
import uuid
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.core.errors import ValidationError
from app.core.models import (
    BenchmarkTaskMatrixEntry,
    BenchmarkTaskRecord,
    BenchmarkTaskStatus,
    ReportRecord,
    ReportStatus,
    RunRecord,
)
from app.hil.evaluation_profiles import list_evaluation_profiles
from app.orchestrator.run_manager import RunManager
from app.scenario.environment_presets import list_environment_presets
from app.scenario.library import list_scenario_catalog
from app.scenario.maps import display_map_name, prefer_optimized_map_request
from app.scenario.sensor_profiles import load_sensor_profiles
from app.storage.artifact_store import ArtifactStore
from app.storage.benchmark_definition_store import BenchmarkDefinitionStore
from app.storage.benchmark_task_store import BenchmarkTaskStore
from app.storage.gateway_store import GatewayStore
from app.storage.project_store import ProjectStore
from app.storage.report_store import ReportStore
from app.storage.run_store import RunStore
from app.utils.file_utils import ensure_dir
from app.utils.time_utils import now_utc


def _clone_json(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def _average(values: list[float | None]) -> float | None:
    valid = [value for value in values if isinstance(value, float | int)]
    if not valid:
        return None
    return sum(valid) / len(valid)


def _metric_number(source: dict[str, Any] | None, keys: list[str]) -> float | None:
    if not source:
        return None

    for key in keys:
        value = source.get(key)
        if isinstance(value, float | int):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                continue

    lowered_keys = {key.lower() for key in keys}
    for key, value in source.items():
        if key.lower() not in lowered_keys:
            continue
        if isinstance(value, float | int):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                continue
    return None


def _derive_task_status(runs: list[RunRecord]) -> BenchmarkTaskStatus:
    if not runs:
        return BenchmarkTaskStatus.CREATED

    statuses = {run.status.value for run in runs}
    if statuses == {"CREATED"}:
        return BenchmarkTaskStatus.CREATED
    active_statuses = {"CREATED", "QUEUED", "STARTING", "RUNNING", "PAUSED", "STOPPING"}
    if statuses & active_statuses:
        return BenchmarkTaskStatus.RUNNING

    if statuses == {"COMPLETED"}:
        return BenchmarkTaskStatus.COMPLETED
    if statuses <= {"FAILED"}:
        return BenchmarkTaskStatus.FAILED
    if statuses <= {"CANCELED"}:
        return BenchmarkTaskStatus.CANCELED
    if statuses & {"FAILED", "CANCELED"}:
        return BenchmarkTaskStatus.PARTIAL_FAILED
    return BenchmarkTaskStatus.CREATED


class PlatformService:
    def __init__(
        self,
        *,
        project_store: ProjectStore,
        benchmark_definition_store: BenchmarkDefinitionStore,
        benchmark_task_store: BenchmarkTaskStore,
        report_store: ReportStore,
        run_store: RunStore,
        run_manager: RunManager,
        artifact_store: ArtifactStore,
        gateway_store: GatewayStore,
        sensor_profiles_root: Path,
        report_artifacts_root: Path,
    ) -> None:
        self._project_store = project_store
        self._benchmark_definition_store = benchmark_definition_store
        self._benchmark_task_store = benchmark_task_store
        self._report_store = report_store
        self._run_store = run_store
        self._run_manager = run_manager
        self._artifact_store = artifact_store
        self._gateway_store = gateway_store
        self._sensor_profiles_root = sensor_profiles_root
        self._report_artifacts_root = ensure_dir(report_artifacts_root)

    def list_projects(self):
        return self._project_store.list()

    def get_project(self, project_id: str):
        return self._project_store.get(project_id)

    def list_benchmark_definitions(self):
        return self._benchmark_definition_store.list()

    def get_benchmark_definition(self, benchmark_definition_id: str):
        return self._benchmark_definition_store.get(benchmark_definition_id)

    def _scenario_catalog_index(self) -> dict[str, dict[str, Any]]:
        return {item["scenario_id"]: item for item in list_scenario_catalog()}

    def _environment_preset_index(self) -> dict[str, dict[str, Any]]:
        return {item["preset_id"]: item for item in list_environment_presets()}

    def _sensor_profile_index(self) -> dict[str, dict[str, Any]]:
        return {
            item["profile_name"]: item
            for item in load_sensor_profiles(self._sensor_profiles_root)
        }

    def _evaluation_profile_index(self) -> dict[str, dict[str, Any]]:
        return {item["profile_name"]: item for item in list_evaluation_profiles()}

    def _sync_task(self, task: BenchmarkTaskRecord) -> BenchmarkTaskRecord:
        before = task.model_dump(mode="json")
        runs = [self._run_store.get(run_id) for run_id in task.run_ids]
        counts = Counter(run.status.value for run in runs)
        task.counts_by_status = dict(counts)
        task.planned_run_count = len(task.run_ids)
        task.status = _derive_task_status(runs)

        started_times = [run.started_at for run in runs if run.started_at is not None]
        ended_times = [run.ended_at for run in runs if run.ended_at is not None]
        task.started_at = min(started_times) if started_times else None
        task.ended_at = (
            max(ended_times)
            if ended_times and all(run.ended_at is not None for run in runs)
            else None
        )
        task.summary = self._build_task_summary(task, runs)
        after = task.model_dump(mode="json")
        if after != before:
            return self._benchmark_task_store.save(task)
        return task

    def _build_task_summary(
        self, task: BenchmarkTaskRecord, runs: list[RunRecord]
    ) -> dict[str, Any]:
        metrics_payloads = [
            self._artifact_store.read_metrics(run.run_id) or {} for run in runs
        ]
        fps_values = []
        for metrics in metrics_payloads:
            current_tick = metrics.get("current_tick")
            wall_time = metrics.get("wall_time")
            if isinstance(current_tick, int) and isinstance(
                wall_time, float | int
            ) and wall_time > 0:
                fps_values.append(float(current_tick) / float(wall_time))

        terminal_runs = [
            run for run in runs if run.status.value in {"COMPLETED", "FAILED", "CANCELED"}
        ]
        completed_runs = [run for run in runs if run.status.value == "COMPLETED"]
        anomaly_runs = [
            run for run in runs if run.status.value in {"FAILED", "CANCELED"}
        ]

        gateway_metrics: dict[str, Any] = {}
        if task.hil_config and task.hil_config.get("gateway_id"):
            try:
                gateway = self._gateway_store.get(str(task.hil_config["gateway_id"]))
                gateway_metrics = gateway.metrics
            except Exception:
                gateway_metrics = {}

        scenario_breakdown: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"total_runs": 0, "completed": 0, "failed": 0, "canceled": 0}
        )
        for run in runs:
            entry = scenario_breakdown[run.scenario_name]
            entry["total_runs"] += 1
            if run.status.value == "COMPLETED":
                entry["completed"] += 1
            elif run.status.value == "FAILED":
                entry["failed"] += 1
            elif run.status.value == "CANCELED":
                entry["canceled"] += 1

        return {
            "counts": {
                "total_runs": len(runs),
                "created_runs": len([run for run in runs if run.status.value == "CREATED"]),
                "queued_runs": len([run for run in runs if run.status.value == "QUEUED"]),
                "completed_runs": len(completed_runs),
                "failed_runs": len([run for run in runs if run.status.value == "FAILED"]),
                "canceled_runs": len([run for run in runs if run.status.value == "CANCELED"]),
                "running_runs": len(
                    [
                        run
                        for run in runs
                        if run.status.value
                        in {"STARTING", "RUNNING", "PAUSED", "STOPPING"}
                    ]
                ),
            },
            "metrics": {
                "fps": _average(fps_values),
                "latency_ms": _metric_number(
                    gateway_metrics,
                    ["avg_latency_ms", "latency_ms", "p95_latency_ms"],
                ),
                "map": _metric_number(gateway_metrics, ["map50", "mAP", "map"]),
                "power_w": _metric_number(
                    gateway_metrics,
                    ["power_w", "soc_power_w", "board_power_w", "total_power_w"],
                ),
                "temperature_c": _metric_number(
                    gateway_metrics,
                    ["temperature_c", "soc_temp_c", "cpu_temp_c", "board_temp_c"],
                ),
                "frame_drop_rate": _metric_number(
                    gateway_metrics, ["frame_drop_rate", "drop_rate"]
                ),
                "pass_rate": (
                    (len(completed_runs) / len(terminal_runs)) * 100
                    if terminal_runs
                    else None
                ),
                "anomaly_rate": (
                    (len(anomaly_runs) / len(runs)) * 100 if runs else None
                ),
            },
            "scenario_breakdown": scenario_breakdown,
            "gateway_snapshot": gateway_metrics,
        }

    def list_benchmark_tasks(
        self, project_id: str | None = None, status: str | None = None
    ) -> list[BenchmarkTaskRecord]:
        items = [self._sync_task(item) for item in self._benchmark_task_store.list()]
        if project_id is not None:
            items = [item for item in items if item.project_id == project_id]
        if status is not None:
            items = [item for item in items if item.status.value == status]
        return sorted(items, key=lambda item: item.updated_at, reverse=True)

    def get_benchmark_task(self, benchmark_task_id: str) -> BenchmarkTaskRecord:
        return self._sync_task(self._benchmark_task_store.get(benchmark_task_id))

    def create_benchmark_task(
        self,
        *,
        project_id: str,
        benchmark_definition_id: str,
        dut_model: str | None,
        scenario_matrix: list[dict[str, str]],
        hil_config: dict[str, Any] | None,
        evaluation_profile_name: str | None,
        auto_start: bool,
    ) -> BenchmarkTaskRecord:
        if not scenario_matrix:
            raise ValidationError("scenario_matrix 至少需要 1 条组合")

        project = self._project_store.get(project_id)
        definition = self._benchmark_definition_store.get(benchmark_definition_id)
        if project.project_id not in definition.project_ids:
            raise ValidationError(
                f"项目 {project_id} 不在基准任务 {benchmark_definition_id} 的适用范围内"
            )

        if hil_config and hil_config.get("gateway_id"):
            self._gateway_store.get(str(hil_config["gateway_id"]))

        evaluation_profile = None
        resolved_evaluation_profile_name = (
            evaluation_profile_name or definition.default_evaluation_profile_name
        )
        if resolved_evaluation_profile_name:
            evaluation_profile = self._evaluation_profile_index().get(
                resolved_evaluation_profile_name
            )
            if evaluation_profile is None:
                raise ValidationError(
                    f"未知评测协议: {resolved_evaluation_profile_name}"
                )

        scenario_catalog = self._scenario_catalog_index()
        environment_presets = self._environment_preset_index()
        sensor_profiles = self._sensor_profile_index()
        normalized_dut_model = dut_model.strip() if dut_model and dut_model.strip() else None

        now = now_utc()
        benchmark_task_id = f"task_{now.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        created_run_ids: list[str] = []
        normalized_matrix: list[BenchmarkTaskMatrixEntry] = []

        for row in scenario_matrix:
            scenario_id = str(row["scenario_id"]).strip()
            environment_preset_id = str(row["environment_preset_id"]).strip()
            sensor_profile_name = str(row["sensor_profile_name"]).strip()
            requested_map_name = str(row["map_name"]).strip()

            scenario = scenario_catalog.get(scenario_id)
            if scenario is None:
                raise ValidationError(f"未知场景: {scenario_id}")
            if scenario.get("execution_support") != "native":
                raise ValidationError(f"场景 {scenario_id} 当前不可由本地 executor 执行")

            environment_preset = environment_presets.get(environment_preset_id)
            if environment_preset is None:
                raise ValidationError(f"未知环境预设: {environment_preset_id}")

            sensor_profile = sensor_profiles.get(sensor_profile_name)
            if sensor_profile is None:
                raise ValidationError(f"未知传感器模板: {sensor_profile_name}")

            resolved_map_name = prefer_optimized_map_request(
                requested_map_name or str(scenario["default_map_name"])
            )
            descriptor = _clone_json(scenario["descriptor_template"])
            descriptor["map_name"] = resolved_map_name
            descriptor["weather"] = environment_preset["weather"]
            descriptor["sensors"] = {
                "enabled": True,
                "profile_name": sensor_profile["profile_name"],
                "config_yaml_path": sensor_profile["source_path"],
                "sensors": sensor_profile["sensors"],
            }

            metadata = dict(descriptor.get("metadata") or {})
            existing_tags = list(metadata.get("tags") or [])
            metadata["author"] = "chip-benchmark-platform"
            metadata["dut_model"] = normalized_dut_model
            metadata["description"] = (
                " / ".join(
                    part
                    for part in [
                        project.name,
                        normalized_dut_model,
                        scenario["display_name"],
                        display_map_name(resolved_map_name),
                    ]
                    if part
                )
            )
            metadata["tags"] = list(
                dict.fromkeys(
                    [
                        *existing_tags,
                        f"project:{project.project_id}",
                        f"benchmark:{definition.benchmark_definition_id}",
                        f"task:{benchmark_task_id}",
                        f"scenario:{scenario['scenario_name']}",
                    ]
                )
            )
            descriptor["metadata"] = metadata

            run = self._run_manager.create_run(
                descriptor_payload=descriptor,
                hil_config=hil_config,
                evaluation_profile=evaluation_profile,
            )
            created_run_ids.append(run.run_id)

            normalized_matrix.append(
                BenchmarkTaskMatrixEntry(
                    scenario_id=scenario["scenario_id"],
                    scenario_name=scenario["scenario_name"],
                    scenario_display_name=scenario["display_name"],
                    requested_map_name=requested_map_name,
                    resolved_map_name=resolved_map_name,
                    display_map_name=display_map_name(resolved_map_name),
                    environment_preset_id=environment_preset["preset_id"],
                    environment_name=environment_preset["display_name"],
                    sensor_profile_name=sensor_profile["profile_name"],
                )
            )

        if auto_start:
            for run_id in created_run_ids:
                self._run_manager.start_run(run_id)

        task = BenchmarkTaskRecord(
            benchmark_task_id=benchmark_task_id,
            project_id=project.project_id,
            project_name=project.name,
            dut_model=normalized_dut_model,
            benchmark_definition_id=definition.benchmark_definition_id,
            benchmark_name=definition.name,
            planned_run_count=len(created_run_ids),
            counts_by_status={"CREATED": len(created_run_ids)},
            run_ids=created_run_ids,
            scenario_matrix=normalized_matrix,
            hil_config=hil_config,
            evaluation_profile_name=resolved_evaluation_profile_name,
            auto_start=auto_start,
            created_at=now,
            updated_at=now,
        )
        self._benchmark_task_store.create(task)
        return self.get_benchmark_task(benchmark_task_id)

    def list_reports(
        self, benchmark_task_id: str | None = None
    ) -> list[ReportRecord]:
        items = self._report_store.list()
        if benchmark_task_id is not None:
            items = [
                item for item in items if item.benchmark_task_id == benchmark_task_id
            ]
        return sorted(items, key=lambda item: item.updated_at, reverse=True)

    def get_report(self, report_id: str) -> ReportRecord:
        return self._report_store.get(report_id)

    def export_report(self, benchmark_task_id: str) -> ReportRecord:
        task = self.get_benchmark_task(benchmark_task_id)
        now = now_utc()
        report_id = f"report_{now.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        artifact_dir = ensure_dir(self._report_artifacts_root / report_id)
        json_path = artifact_dir / "report.json"
        markdown_path = artifact_dir / "report.md"

        report_payload = {
            "report_id": report_id,
            "benchmark_task_id": task.benchmark_task_id,
            "project_id": task.project_id,
            "project_name": task.project_name,
            "dut_model": task.dut_model,
            "benchmark_definition_id": task.benchmark_definition_id,
            "benchmark_name": task.benchmark_name,
            "status": task.status.value,
            "created_at_utc": now.isoformat(),
            "summary": task.summary,
            "run_ids": task.run_ids,
            "scenario_matrix": [
                item.model_dump(mode="json") for item in task.scenario_matrix
            ],
        }

        with json_path.open("w", encoding="utf-8") as handle:
            json.dump(report_payload, handle, ensure_ascii=False, indent=2)

        metrics = task.summary.get("metrics", {})
        counts = task.summary.get("counts", {})
        markdown_lines = [
            f"# {task.project_name} / {task.benchmark_name}",
            "",
            f"- 报告 ID: `{report_id}`",
            f"- 任务 ID: `{task.benchmark_task_id}`",
            f"- DUT 型号: `{task.dut_model or '未登记'}`",
            f"- 状态: `{task.status.value}`",
            f"- 计划运行数: `{counts.get('total_runs', task.planned_run_count)}`",
            f"- 已完成: `{counts.get('completed_runs', 0)}`",
            f"- 失败: `{counts.get('failed_runs', 0)}`",
            f"- 取消: `{counts.get('canceled_runs', 0)}`",
            "",
            "## 核心指标",
            "",
            f"- FPS: `{metrics.get('fps')}`",
            f"- 延迟(ms): `{metrics.get('latency_ms')}`",
            f"- mAP: `{metrics.get('map')}`",
            f"- 功耗(W): `{metrics.get('power_w')}`",
            f"- 温度(°C): `{metrics.get('temperature_c')}`",
            f"- 场景通过率(%): `{metrics.get('pass_rate')}`",
            f"- 异常率(%): `{metrics.get('anomaly_rate')}`",
            "",
            "## 场景矩阵",
            "",
        ]
        for entry in task.scenario_matrix:
            markdown_lines.append(
                f"- {entry.scenario_display_name}: {entry.display_map_name} / {entry.environment_name} / {entry.sensor_profile_name}"
            )

        with markdown_path.open("w", encoding="utf-8") as handle:
            handle.write("\n".join(markdown_lines))
            handle.write("\n")

        report = ReportRecord(
            report_id=report_id,
            benchmark_task_id=task.benchmark_task_id,
            project_id=task.project_id,
            benchmark_definition_id=task.benchmark_definition_id,
            dut_model=task.dut_model,
            title=" / ".join(
                part
                for part in [task.project_name, task.dut_model or "未登记 DUT", task.benchmark_name]
                if part
            ),
            status=ReportStatus.READY,
            artifact_dir=str(artifact_dir),
            json_path=str(json_path),
            markdown_path=str(markdown_path),
            summary=task.summary,
            created_at=now,
            updated_at=now,
        )
        self._report_store.create(report)
        return report
