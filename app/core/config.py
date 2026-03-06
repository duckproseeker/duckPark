from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    service_name: str
    api_host: str
    api_port: int
    carla_host: str
    carla_port: int
    carla_timeout_seconds: float
    traffic_manager_port: int
    command_poll_interval_seconds: float
    runs_root: Path
    commands_root: Path
    artifacts_root: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_root = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[2]))

    runs_root = Path(os.getenv("RUNS_ROOT", project_root / "run_data" / "runs"))
    commands_root = Path(
        os.getenv("COMMANDS_ROOT", project_root / "run_data" / "commands")
    )
    artifacts_root = Path(os.getenv("ARTIFACTS_ROOT", project_root / "artifacts"))

    return Settings(
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
        commands_root=commands_root,
        artifacts_root=artifacts_root,
    )
