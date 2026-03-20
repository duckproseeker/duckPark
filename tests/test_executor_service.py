from __future__ import annotations

from app.core.config import get_settings
from app.core.models import RunRecord, RunStatus
from app.executor.service import ExecutorService
from app.storage.artifact_store import ArtifactStore
from app.storage.run_store import RunStore
from app.utils.time_utils import now_utc


VALID_DESCRIPTOR = {
    "version": 1,
    "scenario_name": "town10_autonomous_demo",
    "map_name": "Town10HD_Opt",
    "weather": {"preset": "ClearNoon"},
    "sync": {"enabled": False, "fixed_delta_seconds": 0.1},
    "ego_vehicle": {
        "blueprint": "vehicle.lincoln.mkz_2017",
        "spawn_point": {
            "x": 10.0,
            "y": 20.0,
            "z": 0.5,
            "roll": 0.0,
            "pitch": 0.0,
            "yaw": 90.0,
        },
    },
    "traffic": {"enabled": False, "num_vehicles": 0, "num_walkers": 0},
    "sensors": {"enabled": False},
    "termination": {"timeout_seconds": 30, "success_condition": "manual_stop"},
    "recorder": {"enabled": False},
    "metadata": {"author": "test", "tags": ["executor"], "description": "executor test"},
}


def test_executor_service_recovers_interrupted_runs_on_startup() -> None:
    settings = get_settings()
    run_store = RunStore(settings.runs_root)
    artifact_store = ArtifactStore(settings.artifacts_root)

    interrupted_run_id = f"run_executor_recover_{now_utc().strftime('%Y%m%d%H%M%S%f')}"
    interrupted_run_dir = artifact_store.init_run(interrupted_run_id)
    interrupted_run = RunRecord(
        run_id=interrupted_run_id,
        status=RunStatus.RUNNING,
        created_at=now_utc(),
        updated_at=now_utc(),
        started_at=now_utc(),
        scenario_name="town10_autonomous_demo",
        map_name="Town10HD_Opt",
        descriptor=VALID_DESCRIPTOR,
        artifact_dir=str(interrupted_run_dir),
        execution_backend="native",
        scenario_source={"provider": "native", "launch_mode": "native_descriptor"},
    )
    run_store.create(interrupted_run)
    artifact_store.write_status(interrupted_run)

    completed_run_id = f"run_executor_keep_{now_utc().strftime('%Y%m%d%H%M%S%f')}"
    completed_run_dir = artifact_store.init_run(completed_run_id)
    completed_run = RunRecord(
        run_id=completed_run_id,
        status=RunStatus.COMPLETED,
        created_at=now_utc(),
        updated_at=now_utc(),
        started_at=now_utc(),
        ended_at=now_utc(),
        scenario_name="town10_autonomous_demo",
        map_name="Town10HD_Opt",
        descriptor=VALID_DESCRIPTOR,
        artifact_dir=str(completed_run_dir),
        execution_backend="native",
        scenario_source={"provider": "native", "launch_mode": "native_descriptor"},
    )
    run_store.create(completed_run)
    artifact_store.write_status(completed_run)

    service = ExecutorService()
    service._recover_interrupted_runs()

    interrupted_after = run_store.get(interrupted_run_id)
    assert interrupted_after.status == RunStatus.FAILED
    assert "executor 服务重启" in (interrupted_after.error_reason or "")

    metrics = artifact_store.read_metrics(interrupted_run_id)
    assert metrics is not None
    assert metrics["final_status"] == "FAILED"

    events = artifact_store.read_events(interrupted_run_id)
    event_types = {event["event_type"] for event in events}
    assert "RUN_RECOVERED_AFTER_EXECUTOR_RESTART" in event_types

    completed_after = run_store.get(completed_run_id)
    assert completed_after.status == RunStatus.COMPLETED
