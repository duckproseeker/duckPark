from __future__ import annotations

from app.core.config import get_settings


def test_get_settings_loads_env_local_relative_to_project_root(
    tmp_path, monkeypatch
) -> None:
    project_root = tmp_path / "env_project"
    (project_root / "external" / "scenario_runner").mkdir(parents=True, exist_ok=True)
    (project_root / "external" / "carla").mkdir(parents=True, exist_ok=True)
    (project_root / ".env.local").write_text(
        "\n".join(
            [
                'CARLA_HOST="192.168.1.25"',
                "CARLA_PORT=2100",
                "export TRAFFIC_MANAGER_PORT=8110",
                "RUNS_ROOT=./custom/runs",
                "COMMANDS_ROOT=./custom/commands",
                "ARTIFACTS_ROOT=./custom/artifacts",
                "SCENARIO_RUNNER_ROOT=./external/scenario_runner",
                "SCENARIO_RUNNER_CARLA_ROOT=./external/carla",
            ]
        ),
        encoding="utf-8",
    )

    for key in [
        "CARLA_HOST",
        "CARLA_PORT",
        "TRAFFIC_MANAGER_PORT",
        "RUNS_ROOT",
        "COMMANDS_ROOT",
        "ARTIFACTS_ROOT",
        "SCENARIO_RUNNER_ROOT",
        "SCENARIO_RUNNER_CARLA_ROOT",
    ]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("PROJECT_ROOT", str(project_root))
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.carla_host == "192.168.1.25"
    assert settings.carla_port == 2100
    assert settings.traffic_manager_port == 8110
    assert settings.runs_root == project_root / "custom" / "runs"
    assert settings.commands_root == project_root / "custom" / "commands"
    assert settings.artifacts_root == project_root / "custom" / "artifacts"
    assert settings.scenario_runner_root == project_root / "external" / "scenario_runner"
    assert settings.scenario_runner_carla_root == project_root / "external" / "carla"
