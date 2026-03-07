from __future__ import annotations

from pathlib import Path

import pytest

from app.api.routes_gateways import get_gateway_registry
from app.api.routes_runs import get_artifact_store, get_run_manager
from app.core.config import get_settings


@pytest.fixture(autouse=True)
def reset_settings_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "project"
    (project_root / "run_data" / "runs").mkdir(parents=True, exist_ok=True)
    (project_root / "run_data" / "commands").mkdir(parents=True, exist_ok=True)
    (project_root / "artifacts").mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("RUNS_ROOT", str(project_root / "run_data" / "runs"))
    monkeypatch.setenv("COMMANDS_ROOT", str(project_root / "run_data" / "commands"))
    monkeypatch.setenv("ARTIFACTS_ROOT", str(project_root / "artifacts"))
    monkeypatch.setenv("GATEWAYS_ROOT", str(project_root / "run_data" / "gateways"))

    get_settings.cache_clear()
    get_run_manager.cache_clear()
    get_artifact_store.cache_clear()
    get_gateway_registry.cache_clear()

    yield

    get_settings.cache_clear()
    get_run_manager.cache_clear()
    get_artifact_store.cache_clear()
    get_gateway_registry.cache_clear()
