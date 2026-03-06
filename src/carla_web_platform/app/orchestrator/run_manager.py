from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.models import EventLevel, RunEvent, RunRecord, RunStatus
from app.orchestrator.queue import FileCommandQueue
from app.scenario.registry import BUILTIN_SCENARIOS
from app.scenario.validators import load_descriptor_from_yaml, validate_descriptor
from app.storage.artifact_store import ArtifactStore
from app.storage.run_store import RunStore
from app.utils.time_utils import now_utc


class RunManager:
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
            raise ValidationError("Either descriptor payload or descriptor_path is required")

        try:
            if descriptor_path is not None:
                descriptor = load_descriptor_from_yaml(Path(descriptor_path))
            else:
                assert descriptor_payload is not None
                descriptor = validate_descriptor(descriptor_payload)
        except (ValueError, PydanticValidationError) as exc:
            raise ValidationError(str(exc)) from exc

        if descriptor.scenario_name not in BUILTIN_SCENARIOS:
            raise ValidationError(
                f"Unknown scenario_name '{descriptor.scenario_name}'. "
                f"Available: {sorted(BUILTIN_SCENARIOS.keys())}"
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
            "Run created with validated scenario descriptor",
            payload={
                "scenario_name": descriptor.scenario_name,
                "map_name": descriptor.map_name,
            },
        )
        return run

    def start_run(self, run_id: str) -> RunRecord:
        run = self._run_store.get(run_id)
        if run.status != RunStatus.CREATED:
            raise ConflictError(f"Run {run_id} can only be started from CREATED. Current={run.status}")

        run = self._run_store.transition(run_id, RunStatus.QUEUED)
        self._persist_status(run)
        command = self._command_queue.enqueue_start(run_id)

        self._emit_event(
            run_id,
            "RUN_QUEUED",
            "Run queued for executor",
            payload={"command_id": command.command_id},
        )
        return run

    def stop_run(self, run_id: str) -> RunRecord:
        run = self._run_store.get(run_id)

        if run.status in {RunStatus.CREATED, RunStatus.QUEUED}:
            run = self._run_store.transition(run_id, RunStatus.CANCELED, set_ended_at=True)
            self._persist_status(run)
            self._emit_event(run_id, "SCENARIO_STOP_REQUESTED", "Stop requested before execution")
            self._emit_event(run_id, "SCENARIO_COMPLETED", "Run canceled before start")
            return run

        if run.status in {RunStatus.STARTING, RunStatus.RUNNING, RunStatus.PAUSED, RunStatus.STOPPING}:
            run = self._run_store.mark_stop_requested(run_id)
            self._persist_status(run)
            self._emit_event(run_id, "SCENARIO_STOP_REQUESTED", "Stop requested by API")
            return run

        raise ConflictError(f"Run {run_id} cannot be stopped from state {run.status}")

    def cancel_run(self, run_id: str) -> RunRecord:
        run = self._run_store.get(run_id)

        if run.status in {RunStatus.CREATED, RunStatus.QUEUED}:
            run = self._run_store.transition(run_id, RunStatus.CANCELED, set_ended_at=True)
            self._persist_status(run)
            self._emit_event(run_id, "SCENARIO_STOP_REQUESTED", "Cancel requested before execution")
            self._emit_event(run_id, "SCENARIO_COMPLETED", "Run canceled before start")
            return run

        if run.status in {RunStatus.STARTING, RunStatus.RUNNING, RunStatus.PAUSED, RunStatus.STOPPING}:
            run = self._run_store.mark_stop_requested(run_id, cancel_requested=True)
            self._persist_status(run)
            self._emit_event(run_id, "SCENARIO_STOP_REQUESTED", "Cancel requested by API")
            return run

        raise ConflictError(f"Run {run_id} cannot be canceled from state {run.status}")

    def get_run(self, run_id: str) -> RunRecord:
        return self._run_store.get(run_id)

    def list_runs(self, status: str | None = None) -> list[RunRecord]:
        if status is None:
            return self._run_store.list()

        try:
            parsed_status = RunStatus(status)
        except ValueError as exc:
            raise ValidationError(f"Invalid status filter: {status}") from exc

        return self._run_store.list(status=parsed_status)

    def get_events(self, run_id: str) -> list[dict[str, Any]]:
        _ = self._run_store.get(run_id)
        return self._artifact_store.read_events(run_id)
