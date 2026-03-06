from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from app.core.errors import ConflictError, ValidationError
from app.core.models import EventLevel, RunEvent, RunRecord, RunStatus
from app.orchestrator.queue import FileCommandQueue
from app.scenario.registry import BUILTIN_SCENARIOS
from app.scenario.validators import load_descriptor_from_yaml, validate_descriptor
from app.storage.artifact_store import ArtifactStore
from app.storage.run_store import RunStore
from app.utils.time_utils import now_utc


class RunManager:
    """Control-plane orchestrator: create/list/query runs and issue lifecycle commands."""

    def __init__(
        self,
        run_store: RunStore,
        artifact_store: ArtifactStore,
        command_queue: FileCommandQueue,
    ) -> None:
        self._run_store = run_store
        self._artifact_store = artifact_store
        self._command_queue = command_queue

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

    def _persist_status(self, run: RunRecord) -> None:
        self._artifact_store.write_status(run)

    def create_run(
        self,
        descriptor_payload: dict[str, Any] | None = None,
        descriptor_path: str | None = None,
    ) -> RunRecord:
        if descriptor_payload is None and descriptor_path is None:
            raise ValidationError("必须提供 descriptor 或 descriptor_path")

        try:
            if descriptor_path is not None:
                descriptor = load_descriptor_from_yaml(Path(descriptor_path))
            else:
                assert descriptor_payload is not None
                descriptor = validate_descriptor(descriptor_payload)
        except (ValueError, PydanticValidationError) as exc:
            raise ValidationError(f"场景描述校验失败: {exc}") from exc

        if descriptor.scenario_name not in BUILTIN_SCENARIOS:
            raise ValidationError(
                f"未知场景: '{descriptor.scenario_name}'。"
                f"可用场景: {sorted(BUILTIN_SCENARIOS.keys())}"
            )

        run_id = f"run_{now_utc().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        artifact_dir = self._artifact_store.init_run(run_id)

        run = RunRecord(
            run_id=run_id,
            status=RunStatus.CREATED,
            created_at=now_utc(),
            updated_at=now_utc(),
            scenario_name=descriptor.scenario_name,
            map_name=descriptor.map_name,
            descriptor=descriptor.to_dict(),
            artifact_dir=str(artifact_dir),
        )
        self._run_store.create(run)
        self._artifact_store.write_config_snapshot(run_id, descriptor.to_dict())
        self._persist_status(run)

        self._emit_event(
            run_id,
            "RUN_CREATED",
            "运行已创建并完成 descriptor 校验",
            payload={
                "scenario_name": descriptor.scenario_name,
                "map_name": descriptor.map_name,
            },
        )
        return run

    def start_run(self, run_id: str) -> RunRecord:
        run = self._run_store.get(run_id)
        if run.status != RunStatus.CREATED:
            raise ConflictError(f"Run {run_id} 仅能从 CREATED 启动，当前状态为 {run.status.value}")

        run = self._run_store.transition(run_id, RunStatus.QUEUED)
        self._persist_status(run)
        command = self._command_queue.enqueue_start(run_id)

        self._emit_event(
            run_id,
            "RUN_QUEUED",
            "运行已进入队列，等待 executor 执行",
            payload={"command_id": command.command_id},
        )
        return run

    def stop_run(self, run_id: str) -> RunRecord:
        run = self._run_store.get(run_id)

        if run.status in {RunStatus.CREATED, RunStatus.QUEUED}:
            run = self._run_store.transition(run_id, RunStatus.CANCELED, set_ended_at=True)
            self._persist_status(run)
            self._emit_event(run_id, "SCENARIO_STOP_REQUESTED", "运行尚未开始，已取消")
            self._emit_event(run_id, "SCENARIO_COMPLETED", "运行在启动前被停止")
            return run

        if run.status in {
            RunStatus.STARTING,
            RunStatus.RUNNING,
            RunStatus.PAUSED,
            RunStatus.STOPPING,
        }:
            run = self._run_store.mark_stop_requested(run_id)
            self._persist_status(run)
            self._emit_event(run_id, "SCENARIO_STOP_REQUESTED", "收到停止请求")
            return run

        raise ConflictError(f"Run {run_id} 在状态 {run.status.value} 下不可停止")

    def cancel_run(self, run_id: str) -> RunRecord:
        run = self._run_store.get(run_id)

        if run.status in {RunStatus.CREATED, RunStatus.QUEUED}:
            run = self._run_store.transition(run_id, RunStatus.CANCELED, set_ended_at=True)
            self._persist_status(run)
            self._emit_event(run_id, "SCENARIO_STOP_REQUESTED", "运行尚未开始，已取消")
            self._emit_event(run_id, "SCENARIO_COMPLETED", "运行在启动前被取消")
            return run

        if run.status in {
            RunStatus.STARTING,
            RunStatus.RUNNING,
            RunStatus.PAUSED,
            RunStatus.STOPPING,
        }:
            run = self._run_store.mark_stop_requested(run_id, cancel_requested=True)
            self._persist_status(run)
            self._emit_event(run_id, "SCENARIO_STOP_REQUESTED", "收到取消请求")
            return run

        raise ConflictError(f"Run {run_id} 在状态 {run.status.value} 下不可取消")

    def get_run(self, run_id: str) -> RunRecord:
        return self._run_store.get(run_id)

    def list_runs(self, status: str | None = None) -> list[RunRecord]:
        if status is None:
            return self._run_store.list()

        try:
            parsed_status = RunStatus(status)
        except ValueError as exc:
            raise ValidationError(f"无效的状态过滤值: {status}") from exc

        return self._run_store.list(status=parsed_status)

    def get_events(self, run_id: str) -> list[dict[str, Any]]:
        _ = self._run_store.get(run_id)
        return self._artifact_store.read_events(run_id)
