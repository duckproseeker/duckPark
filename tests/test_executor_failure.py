from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.core.models import RunRecord, RunStatus
from app.executor.sim_controller import SimController
from app.storage.artifact_store import ArtifactStore
from app.storage.run_store import RunStore
from app.utils.time_utils import now_utc


VALID_DESCRIPTOR = {
    "version": 1,
    "scenario_name": "empty_drive",
    "map_name": "Town01",
    "weather": {"preset": "ClearNoon"},
    "sync": {"enabled": True, "fixed_delta_seconds": 0.05},
    "ego_vehicle": {
        "blueprint": "vehicle.tesla.model3",
        "spawn_point": {
            "x": 230.0,
            "y": 195.0,
            "z": 0.5,
            "roll": 0.0,
            "pitch": 0.0,
            "yaw": 90.0,
        },
    },
    "traffic": {"enabled": False, "num_vehicles": 0, "num_walkers": 0},
    "sensors": {"enabled": False},
    "termination": {"timeout_seconds": 10, "success_condition": "timeout"},
    "recorder": {"enabled": False},
    "metadata": {"author": "test", "tags": ["executor"], "description": "executor failure"},
}


class FailingCarlaClient:
    def __init__(self, host: str, port: int, timeout_seconds: float, traffic_manager_port: int) -> None:
        self._spawn_count = 0

    def connect(self) -> None:
        raise RuntimeError("connect failed for test")

    def spawned_actor_count(self) -> int:
        return self._spawn_count

    def cleanup(self) -> None:
        return



def test_executor_failure_transitions_to_failed() -> None:
    settings = get_settings()
    run_store = RunStore(settings.runs_root)
    artifact_store = ArtifactStore(settings.artifacts_root)

    run_id = "run_test_failure"
    run_dir = artifact_store.init_run(run_id)

    run = RunRecord(
        run_id=run_id,
        status=RunStatus.QUEUED,
        created_at=now_utc(),
        updated_at=now_utc(),
        scenario_name="empty_drive",
        map_name="Town01",
        descriptor=VALID_DESCRIPTOR,
        artifact_dir=str(run_dir),
    )
    run_store.create(run)
    artifact_store.write_status(run)

    controller = SimController(
        settings=settings,
        run_store=run_store,
        artifact_store=artifact_store,
        client_factory=FailingCarlaClient,
    )
    controller.execute_run(run_id)

    run_after = run_store.get(run_id)
    assert run_after.status == RunStatus.FAILED
    assert run_after.error_reason is not None
    assert "connect failed for test" in run_after.error_reason

    assert (Path(run_after.artifact_dir) / "metrics.json").exists()
