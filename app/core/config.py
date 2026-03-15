from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _resolve_path(value: str | Path, *, base_dir: Path | None = None) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute() and base_dir is not None:
        path = base_dir / path
    return path


def _existing_path(value: str | None, *, base_dir: Path | None = None) -> Path | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    path = _resolve_path(normalized, base_dir=base_dir)
    return path if path.exists() else None


def _first_existing_path(*candidates: Path) -> Path | None:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _path_from_env(name: str, default: Path, *, base_dir: Path) -> Path:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return _resolve_path(raw.strip(), base_dir=base_dir)


def _normalize_env_value(value: str) -> str:
    normalized = value.strip()
    if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {'"', "'"}:
        return normalized[1:-1]
    if " #" in normalized:
        return normalized.split(" #", 1)[0].rstrip()
    return normalized


def _load_env_file(env_file: Path) -> None:
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        os.environ.setdefault(key, _normalize_env_value(value))


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
    scenario_builds_root: Path
    sensor_profiles_root: Path
    scenario_runner_root: Path | None
    scenario_runner_carla_root: Path | None
    scenario_runner_python: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    default_project_root = Path(__file__).resolve().parents[2]
    project_root = _resolve_path(
        os.getenv("PROJECT_ROOT", str(default_project_root)),
        base_dir=Path.cwd(),
    )
    _load_env_file(project_root / ".env.local")
    project_root = _resolve_path(
        os.getenv("PROJECT_ROOT", str(default_project_root)),
        base_dir=Path.cwd(),
    )

    runs_root = _path_from_env("RUNS_ROOT", project_root / "run_data" / "runs", base_dir=project_root)
    captures_root = _path_from_env(
        "CAPTURES_ROOT", project_root / "run_data" / "captures", base_dir=project_root
    )
    commands_root = _path_from_env(
        "COMMANDS_ROOT", project_root / "run_data" / "commands", base_dir=project_root
    )
    executor_root = _path_from_env(
        "EXECUTOR_ROOT", project_root / "run_data" / "executor", base_dir=project_root
    )
    controls_root = _path_from_env(
        "CONTROLS_ROOT", project_root / "run_data" / "controls", base_dir=project_root
    )
    artifacts_root = _path_from_env(
        "ARTIFACTS_ROOT", project_root / "artifacts", base_dir=project_root
    )
    capture_artifacts_root = _path_from_env(
        "CAPTURE_ARTIFACTS_ROOT", artifacts_root / "captures", base_dir=project_root
    )
    gateways_root = _path_from_env(
        "GATEWAYS_ROOT", project_root / "run_data" / "gateways", base_dir=project_root
    )
    projects_root = _path_from_env(
        "PROJECTS_ROOT", project_root / "run_data" / "projects", base_dir=project_root
    )
    benchmark_definitions_root = _path_from_env(
        "BENCHMARK_DEFINITIONS_ROOT",
        project_root / "run_data" / "benchmark_definitions",
        base_dir=project_root,
    )
    benchmark_tasks_root = _path_from_env(
        "BENCHMARK_TASKS_ROOT",
        project_root / "run_data" / "benchmark_tasks",
        base_dir=project_root,
    )
    reports_root = _path_from_env(
        "REPORTS_ROOT", project_root / "run_data" / "reports", base_dir=project_root
    )
    report_artifacts_root = _path_from_env(
        "REPORT_ARTIFACTS_ROOT", artifacts_root / "reports", base_dir=project_root
    )
    scenario_builds_root = _path_from_env(
        "SCENARIO_BUILDS_ROOT",
        project_root / "run_data" / "scenario_builds",
        base_dir=project_root,
    )
    sensor_profiles_root = _path_from_env(
        "SENSOR_PROFILES_ROOT", project_root / "configs" / "sensors", base_dir=project_root
    )
    scenario_runner_root = _existing_path(
        os.getenv("SCENARIO_RUNNER_ROOT"), base_dir=project_root
    ) or _first_existing_path(
        project_root / "external" / "scenario_runner",
        Path("/ros2_ws/carla_workspace/scenario_runner"),
        Path("/workspace/scenario_runner"),
    )
    scenario_runner_carla_root = _existing_path(
        os.getenv("SCENARIO_RUNNER_CARLA_ROOT"),
        base_dir=project_root,
    )
    if scenario_runner_carla_root is None and scenario_runner_root is not None:
        scenario_runner_carla_root = _first_existing_path(
            scenario_runner_root.parent / "carla",
            Path("/ros2_ws/carla_workspace/carla"),
            Path("/workspace/carla"),
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
        scenario_builds_root=scenario_builds_root,
        sensor_profiles_root=sensor_profiles_root,
        scenario_runner_root=scenario_runner_root,
        scenario_runner_carla_root=scenario_runner_carla_root,
        scenario_runner_python=os.getenv("SCENARIO_RUNNER_PYTHON", "python3"),
    )
