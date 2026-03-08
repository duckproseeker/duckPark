from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path
    service_name: str
    api_host: str
    api_port: int
    carla_host: str
    carla_port: int
    carla_timeout_seconds: float
    traffic_manager_port: int
    command_poll_interval_seconds: float
    runs_root: Path
    captures_root: Path
    commands_root: Path
    executor_root: Path
    controls_root: Path
    artifacts_root: Path
    capture_artifacts_root: Path
    gateways_root: Path
    projects_root: Path
    benchmark_definitions_root: Path
    benchmark_tasks_root: Path
    reports_root: Path
    report_artifacts_root: Path
    sensor_profiles_root: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_root = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[2]))

    runs_root = Path(os.getenv("RUNS_ROOT", project_root / "run_data" / "runs"))
    captures_root = Path(os.getenv("CAPTURES_ROOT", project_root / "run_data" / "captures"))
    commands_root = Path(
        os.getenv("COMMANDS_ROOT", project_root / "run_data" / "commands")
    )
    executor_root = Path(os.getenv("EXECUTOR_ROOT", project_root / "run_data" / "executor"))
    controls_root = Path(os.getenv("CONTROLS_ROOT", project_root / "run_data" / "controls"))
    artifacts_root = Path(os.getenv("ARTIFACTS_ROOT", project_root / "artifacts"))
    capture_artifacts_root = Path(
        os.getenv("CAPTURE_ARTIFACTS_ROOT", artifacts_root / "captures")
    )
    gateways_root = Path(os.getenv("GATEWAYS_ROOT", project_root / "run_data" / "gateways"))
    projects_root = Path(os.getenv("PROJECTS_ROOT", project_root / "run_data" / "projects"))
    benchmark_definitions_root = Path(
        os.getenv(
            "BENCHMARK_DEFINITIONS_ROOT",
            project_root / "run_data" / "benchmark_definitions",
        )
    )
    benchmark_tasks_root = Path(
        os.getenv(
            "BENCHMARK_TASKS_ROOT", project_root / "run_data" / "benchmark_tasks"
        )
    )
    reports_root = Path(os.getenv("REPORTS_ROOT", project_root / "run_data" / "reports"))
    report_artifacts_root = Path(
        os.getenv("REPORT_ARTIFACTS_ROOT", artifacts_root / "reports")
    )
    sensor_profiles_root = Path(
        os.getenv("SENSOR_PROFILES_ROOT", project_root / "configs" / "sensors")
    )

    return Settings(
        project_root=project_root,
        service_name=os.getenv("SERVICE_NAME", "carla-sim-control-mvp"),
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8000")),
        carla_host=os.getenv("CARLA_HOST", "carla-server"),
        carla_port=int(os.getenv("CARLA_PORT", "2000")),
        carla_timeout_seconds=float(os.getenv("CARLA_TIMEOUT_SECONDS", "10.0")),
        traffic_manager_port=int(os.getenv("TRAFFIC_MANAGER_PORT", "8010")),
        command_poll_interval_seconds=float(
            os.getenv("COMMAND_POLL_INTERVAL_SECONDS", "1.0")
        ),
        runs_root=runs_root,
        captures_root=captures_root,
        commands_root=commands_root,
        executor_root=executor_root,
        controls_root=controls_root,
        artifacts_root=artifacts_root,
        capture_artifacts_root=capture_artifacts_root,
        gateways_root=gateways_root,
        projects_root=projects_root,
        benchmark_definitions_root=benchmark_definitions_root,
        benchmark_tasks_root=benchmark_tasks_root,
        reports_root=reports_root,
        report_artifacts_root=report_artifacts_root,
        sensor_profiles_root=sensor_profiles_root,
    )
