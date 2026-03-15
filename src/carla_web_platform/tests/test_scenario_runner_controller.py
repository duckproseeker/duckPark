from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from app.core.config import get_settings
from app.executor.scenario_runner_controller import ScenarioRunnerController
from app.orchestrator.queue import FileCommandQueue
from app.orchestrator.run_manager import RunManager
from app.storage.artifact_store import ArtifactStore
from app.storage.gateway_store import GatewayStore
from app.storage.run_store import RunStore


def _write_fake_runner_environment(
    root: Path,
    *,
    write_results: bool = True,
    result_filename: str = "results.json",
    result_payload: dict[str, object] | None = None,
    exit_code: int = 0,
) -> tuple[Path, Path]:
    scenario_runner_root = root / "scenario_runner"
    (scenario_runner_root / "srunner" / "examples").mkdir(parents=True, exist_ok=True)
    result_lines = []
    if write_results:
        payload = result_payload or {"status": "ok"}
        result_lines.append(
            f"(output_dir / {result_filename!r}).write_text(json.dumps({payload!r}), encoding='utf-8')"
        )
    (scenario_runner_root / "scenario_runner.py").write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json",
                "import pathlib",
                "import sys",
                "import time",
                "args = sys.argv[1:]",
                "output_dir = pathlib.Path(args[args.index('--outputDir') + 1])",
                "output_dir.mkdir(parents=True, exist_ok=True)",
                "print('fake scenario runner start', flush=True)",
                "time.sleep(0.1)",
                *result_lines,
                "print('fake scenario runner complete', flush=True)",
                f"sys.exit({exit_code})",
            ]
        ),
        encoding="utf-8",
    )
    (
        scenario_runner_root / "srunner" / "examples" / "FollowLeadingVehicle.xosc"
    ).write_text(
        "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                "<OpenSCENARIO>",
                '  <RoadNetwork><LogicFile filepath="Town01"/></RoadNetwork>',
                "  <Entities>",
                '    <ScenarioObject name="hero"><Vehicle name="vehicle.lincoln.mkz_2017" vehicleCategory="car"/></ScenarioObject>',
                '    <ScenarioObject name="adversary"><Vehicle name="vehicle.tesla.model3" vehicleCategory="car"/></ScenarioObject>',
                "  </Entities>",
                "  <Storyboard/>",
                "</OpenSCENARIO>",
            ]
        ),
        encoding="utf-8",
    )
    carla_root = root / "carla"
    agents_root = carla_root / "PythonAPI" / "carla" / "agents" / "navigation"
    agents_root.mkdir(parents=True, exist_ok=True)
    (agents_root.parent / "__init__.py").write_text("", encoding="utf-8")
    (agents_root / "__init__.py").write_text("", encoding="utf-8")
    dist_root = carla_root / "PythonAPI" / "carla" / "dist"
    dist_root.mkdir(parents=True, exist_ok=True)
    (
        dist_root / "carla-0.9.16-py3.9-linux-x86_64.egg"
    ).write_text("", encoding="utf-8")
    return scenario_runner_root, carla_root


def test_scenario_runner_controller_executes_fake_runner(
    tmp_path: Path, monkeypatch
) -> None:
    scenario_runner_root, carla_root = _write_fake_runner_environment(tmp_path)
    monkeypatch.setenv("SCENARIO_RUNNER_ROOT", str(scenario_runner_root))
    monkeypatch.setenv("SCENARIO_RUNNER_CARLA_ROOT", str(carla_root))
    get_settings.cache_clear()

    settings = get_settings()
    run_store = RunStore(settings.runs_root)
    artifact_store = ArtifactStore(settings.artifacts_root)
    command_queue = FileCommandQueue(settings.commands_root)
    manager = RunManager(
        run_store=run_store,
        artifact_store=artifact_store,
        command_queue=command_queue,
        gateway_store=GatewayStore(settings.gateways_root),
    )
    controller = ScenarioRunnerController(
        settings=settings,
        run_store=run_store,
        artifact_store=artifact_store,
    )

    descriptor = {
        "version": 1,
        "scenario_name": "osc_follow_leading_vehicle",
        "map_name": "Town01",
        "weather": {"preset": "ScenarioRunnerManaged"},
        "sync": {"enabled": True, "fixed_delta_seconds": 0.05},
        "ego_vehicle": {
            "blueprint": "vehicle.lincoln.mkz_2017",
            "spawn_point": {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
            },
        },
        "traffic": {"enabled": False, "num_vehicles": 0, "num_walkers": 0},
        "sensors": {"enabled": False, "sensors": []},
        "termination": {"timeout_seconds": 30, "success_condition": "scenario_runner"},
        "recorder": {"enabled": False},
        "debug": {"viewer_friendly": False},
        "metadata": {"author": "test", "tags": ["scenario_runner"], "description": "test"},
    }

    run = manager.create_run(descriptor_payload=descriptor)
    run_store.transition(run.run_id, run.status.__class__.QUEUED)
    controller.execute_run(run.run_id)

    final_run = run_store.get(run.run_id)
    assert final_run.execution_backend == "scenario_runner"
    assert final_run.status.value == "COMPLETED"

    metrics_path = artifact_store.run_dir(run.run_id) / "metrics.json"
    assert metrics_path.exists()
    metrics_payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics_payload["final_status"] == "COMPLETED"

    result_path = artifact_store.run_dir(run.run_id) / "outputs" / "scenario_runner" / "results.json"
    assert result_path.exists()


def test_scenario_runner_controller_accepts_timestamped_summary_json(
    tmp_path: Path, monkeypatch
) -> None:
    scenario_runner_root, carla_root = _write_fake_runner_environment(
        tmp_path,
        result_filename="FollowLeadingVehicle2026-03-15-18-52-33.json",
        result_payload={"scenario": "FollowLeadingVehicle", "success": True, "criteria": []},
    )
    monkeypatch.setenv("SCENARIO_RUNNER_ROOT", str(scenario_runner_root))
    monkeypatch.setenv("SCENARIO_RUNNER_CARLA_ROOT", str(carla_root))
    get_settings.cache_clear()

    settings = get_settings()
    run_store = RunStore(settings.runs_root)
    artifact_store = ArtifactStore(settings.artifacts_root)
    command_queue = FileCommandQueue(settings.commands_root)
    manager = RunManager(
        run_store=run_store,
        artifact_store=artifact_store,
        command_queue=command_queue,
        gateway_store=GatewayStore(settings.gateways_root),
    )
    controller = ScenarioRunnerController(
        settings=settings,
        run_store=run_store,
        artifact_store=artifact_store,
    )

    descriptor = {
        "version": 1,
        "scenario_name": "osc_follow_leading_vehicle",
        "map_name": "Town01",
        "weather": {"preset": "ScenarioRunnerManaged"},
        "sync": {"enabled": True, "fixed_delta_seconds": 0.05},
        "ego_vehicle": {
            "blueprint": "vehicle.lincoln.mkz_2017",
            "spawn_point": {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
            },
        },
        "traffic": {"enabled": False, "num_vehicles": 0, "num_walkers": 0},
        "sensors": {"enabled": False, "sensors": []},
        "termination": {"timeout_seconds": 30, "success_condition": "scenario_runner"},
        "recorder": {"enabled": False},
        "debug": {"viewer_friendly": False},
        "metadata": {"author": "test", "tags": ["scenario_runner"], "description": "test"},
    }

    run = manager.create_run(descriptor_payload=descriptor)
    run_store.transition(run.run_id, run.status.__class__.QUEUED)
    controller.execute_run(run.run_id)

    final_run = run_store.get(run.run_id)
    assert final_run.status.value == "COMPLETED"
    assert final_run.error_reason is None

    metrics_path = artifact_store.run_dir(run.run_id) / "metrics.json"
    metrics_payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics_payload["final_status"] == "COMPLETED"

    result_path = (
        artifact_store.run_dir(run.run_id)
        / "outputs"
        / "scenario_runner"
        / "FollowLeadingVehicle2026-03-15-18-52-33.json"
    )
    assert result_path.exists()


def test_scenario_runner_controller_fails_when_summary_json_missing(
    tmp_path: Path, monkeypatch
) -> None:
    scenario_runner_root, carla_root = _write_fake_runner_environment(
        tmp_path, write_results=False
    )
    monkeypatch.setenv("SCENARIO_RUNNER_ROOT", str(scenario_runner_root))
    monkeypatch.setenv("SCENARIO_RUNNER_CARLA_ROOT", str(carla_root))
    get_settings.cache_clear()

    settings = get_settings()
    run_store = RunStore(settings.runs_root)
    artifact_store = ArtifactStore(settings.artifacts_root)
    command_queue = FileCommandQueue(settings.commands_root)
    manager = RunManager(
        run_store=run_store,
        artifact_store=artifact_store,
        command_queue=command_queue,
        gateway_store=GatewayStore(settings.gateways_root),
    )
    controller = ScenarioRunnerController(
        settings=settings,
        run_store=run_store,
        artifact_store=artifact_store,
    )

    descriptor = {
        "version": 1,
        "scenario_name": "osc_follow_leading_vehicle",
        "map_name": "Town01",
        "weather": {"preset": "ScenarioRunnerManaged"},
        "sync": {"enabled": True, "fixed_delta_seconds": 0.05},
        "ego_vehicle": {
            "blueprint": "vehicle.lincoln.mkz_2017",
            "spawn_point": {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
            },
        },
        "traffic": {"enabled": False, "num_vehicles": 0, "num_walkers": 0},
        "sensors": {"enabled": False, "sensors": []},
        "termination": {"timeout_seconds": 30, "success_condition": "scenario_runner"},
        "recorder": {"enabled": False},
        "debug": {"viewer_friendly": False},
        "metadata": {"author": "test", "tags": ["scenario_runner"], "description": "test"},
    }

    run = manager.create_run(descriptor_payload=descriptor)
    run_store.transition(run.run_id, run.status.__class__.QUEUED)
    controller.execute_run(run.run_id)

    final_run = run_store.get(run.run_id)
    assert final_run.status.value == "FAILED"
    assert final_run.error_reason is not None
    assert "summary JSON" in final_run.error_reason

    metrics_path = artifact_store.run_dir(run.run_id) / "metrics.json"
    metrics_payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics_payload["final_status"] == "FAILED"


def test_scenario_runner_controller_prefers_generated_xosc_path(
    tmp_path: Path, monkeypatch
) -> None:
    scenario_runner_root, carla_root = _write_fake_runner_environment(tmp_path)
    generated_xosc_path = tmp_path / "generated" / "scenario.xosc"
    generated_xosc_path.parent.mkdir(parents=True, exist_ok=True)
    generated_xosc_path.write_text(
        "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                "<OpenSCENARIO>",
                '  <RoadNetwork><LogicFile filepath="Town05"/></RoadNetwork>',
                "  <Storyboard/>",
                "</OpenSCENARIO>",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("SCENARIO_RUNNER_ROOT", str(scenario_runner_root))
    monkeypatch.setenv("SCENARIO_RUNNER_CARLA_ROOT", str(carla_root))
    get_settings.cache_clear()

    settings = get_settings()
    run_store = RunStore(settings.runs_root)
    artifact_store = ArtifactStore(settings.artifacts_root)
    command_queue = FileCommandQueue(settings.commands_root)
    manager = RunManager(
        run_store=run_store,
        artifact_store=artifact_store,
        command_queue=command_queue,
        gateway_store=GatewayStore(settings.gateways_root),
    )
    controller = ScenarioRunnerController(
        settings=settings,
        run_store=run_store,
        artifact_store=artifact_store,
    )

    descriptor = {
        "version": 1,
        "scenario_name": "osc_follow_leading_vehicle",
        "map_name": "Town05",
        "weather": {"preset": "ClearNoon"},
        "sync": {"enabled": True, "fixed_delta_seconds": 0.05},
        "ego_vehicle": {
            "blueprint": "vehicle.lincoln.mkz_2017",
            "spawn_point": {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
            },
        },
        "traffic": {"enabled": False, "num_vehicles": 0, "num_walkers": 0},
        "sensors": {"enabled": False, "sensors": []},
        "termination": {"timeout_seconds": 30, "success_condition": "scenario_runner"},
        "recorder": {"enabled": False},
        "debug": {"viewer_friendly": False},
        "metadata": {"author": "test", "tags": ["scenario_runner"], "description": "test"},
    }

    run = manager.create_run(
        descriptor_payload=descriptor,
        scenario_source={
            "provider": "scenario_runner",
            "version": "generated",
            "generated_xosc_path": str(generated_xosc_path),
            "resolved_xosc_path": str(generated_xosc_path),
        },
    )
    run_store.transition(run.run_id, run.status.__class__.QUEUED)
    controller.execute_run(run.run_id)

    final_run = run_store.get(run.run_id)
    assert final_run.status.value == "COMPLETED"

    command_ready_event = next(
        event
        for event in artifact_store.read_events(run.run_id)
        if event["event_type"] == "SCENARIO_RUNNER_COMMAND_READY"
    )
    command = command_ready_event["payload"]["command"]
    assert str(generated_xosc_path) in command


def test_scenario_runner_controller_supports_python_scenario_runtime(
    tmp_path: Path, monkeypatch
) -> None:
    scenario_runner_root, carla_root = _write_fake_runner_environment(tmp_path)
    generated_config_path = tmp_path / "generated" / "scenario.xml"
    generated_config_path.parent.mkdir(parents=True, exist_ok=True)
    generated_config_path.write_text(
        "<scenarios><scenario name='DuckparkFreeDrive_test' type='DuckparkFreeDrive' town='Town03'/></scenarios>",
        encoding="utf-8",
    )
    additional_scenario_path = tmp_path / "duckpark_free_drive.py"
    additional_scenario_path.write_text(
        "class DuckparkFreeDrive:\n    pass\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("SCENARIO_RUNNER_ROOT", str(scenario_runner_root))
    monkeypatch.setenv("SCENARIO_RUNNER_CARLA_ROOT", str(carla_root))
    get_settings.cache_clear()

    settings = get_settings()
    run_store = RunStore(settings.runs_root)
    artifact_store = ArtifactStore(settings.artifacts_root)
    command_queue = FileCommandQueue(settings.commands_root)
    manager = RunManager(
        run_store=run_store,
        artifact_store=artifact_store,
        command_queue=command_queue,
        gateway_store=GatewayStore(settings.gateways_root),
    )
    controller = ScenarioRunnerController(
        settings=settings,
        run_store=run_store,
        artifact_store=artifact_store,
    )

    descriptor = {
        "version": 1,
        "scenario_name": "free_drive_sensor_collection",
        "map_name": "Town03",
        "weather": {"preset": "ClearNoon"},
        "sync": {"enabled": True, "fixed_delta_seconds": 0.05},
        "ego_vehicle": {
            "blueprint": "vehicle.lincoln.mkz_2017",
            "spawn_point": {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
            },
        },
        "traffic": {"enabled": False, "num_vehicles": 0, "num_walkers": 0},
        "sensors": {"enabled": False, "sensors": []},
        "termination": {"timeout_seconds": 30, "success_condition": "timeout"},
        "recorder": {"enabled": False},
        "debug": {"viewer_friendly": False},
        "metadata": {"author": "test", "tags": ["scenario_runner"], "description": "test"},
    }

    run = manager.create_run(
        descriptor_payload=descriptor,
        scenario_source={
            "provider": "scenario_runner",
            "version": "generated",
            "launch_mode": "python_scenario",
            "scenario_class": "DuckparkFreeDrive",
            "generated_config_path": str(generated_config_path),
            "additional_scenario_path": str(additional_scenario_path),
        },
    )
    run_store.transition(run.run_id, run.status.__class__.QUEUED)
    controller.execute_run(run.run_id)

    final_run = run_store.get(run.run_id)
    assert final_run.status.value == "COMPLETED"

    command_ready_event = next(
        event
        for event in artifact_store.read_events(run.run_id)
        if event["event_type"] == "SCENARIO_RUNNER_COMMAND_READY"
    )
    command = command_ready_event["payload"]["command"]
    assert "--scenario" in command
    assert "DuckparkFreeDrive" in command
    assert "--configFile" in command
    assert str(generated_config_path) in command
    assert "--additionalScenario" in command
    assert str(additional_scenario_path) in command


def test_background_traffic_retries_bind_error_on_primary_tm_port(
    tmp_path: Path, monkeypatch
) -> None:
    scenario_runner_root, carla_root = _write_fake_runner_environment(tmp_path)
    monkeypatch.setenv("SCENARIO_RUNNER_ROOT", str(scenario_runner_root))
    monkeypatch.setenv("SCENARIO_RUNNER_CARLA_ROOT", str(carla_root))
    get_settings.cache_clear()

    settings = get_settings()
    run_store = RunStore(settings.runs_root)
    artifact_store = ArtifactStore(settings.artifacts_root)
    controller = ScenarioRunnerController(
        settings=settings,
        run_store=run_store,
        artifact_store=artifact_store,
    )
    artifact_store.run_dir("tm-port-test").mkdir(parents=True, exist_ok=True)

    captured: dict[str, int] = {"attempts": 0}

    class FakeLocation:
        def distance(self, other):
            _ = other
            return 0.0

    class FakeHeroActor:
        def get_location(self):
            return FakeLocation()

    class FakeCarlaClient:
        def __init__(self, host, port, timeout_seconds, traffic_manager_port):
            _ = (host, port, timeout_seconds)
            captured["traffic_manager_port"] = traffic_manager_port

        def connect(self):
            captured["attempts"] += 1
            if captured["attempts"] == 1:
                raise RuntimeError("bind error")
            return None

        def apply_traffic_seed(self, seed):
            captured["seed"] = seed

        def find_actor_by_role_name(self, role_name):
            captured["role_name"] = role_name
            return FakeHeroActor()

        def actor_transform_to_dict(self, actor):
            _ = actor
            return {"x": 1.0, "y": 2.0, "z": 0.5, "roll": 0.0, "pitch": 0.0, "yaw": 90.0}

        def spawn_traffic_vehicles(
            self, count, autopilot=True, *, seed=None, anchor_spawn_point=None
        ):
            _ = autopilot
            captured["vehicle_seed"] = seed
            captured["anchor_spawn_point"] = anchor_spawn_point
            return [object()] * count

        def spawn_traffic_walkers(
            self, count, *, seed=None, anchor_location=None, max_radius_m=None
        ):
            captured["walker_seed"] = seed
            captured["walker_anchor"] = anchor_location is not None
            captured["walker_radius"] = max_radius_m
            return [object()] * count

        def cleanup(self):
            return None

    monkeypatch.setattr(
        "app.executor.scenario_runner_controller.CarlaClient",
        FakeCarlaClient,
    )
    monkeypatch.setattr(
        "app.executor.scenario_runner_controller.time.sleep",
        lambda _: None,
    )

    descriptor = SimpleNamespace(
        traffic=SimpleNamespace(
            num_vehicles=2,
            num_walkers=1,
            seed=17,
            injection_mode="carla_api_near_ego",
        )
    )

    controller._spawn_background_traffic("tm-port-test", descriptor)

    assert captured["traffic_manager_port"] == settings.traffic_manager_port
    assert captured["attempts"] == 2
    assert captured["seed"] == 17
    assert captured["role_name"] == "hero"
    assert captured["vehicle_seed"] == 17
    assert captured["walker_seed"] == 18
    assert captured["anchor_spawn_point"]["x"] == 1.0
    assert captured["walker_anchor"] is True
    assert captured["walker_radius"] == 80.0


def test_background_traffic_falls_back_when_stdout_trigger_is_missing(
    tmp_path: Path, monkeypatch
) -> None:
    scenario_runner_root, carla_root = _write_fake_runner_environment(tmp_path)
    monkeypatch.setenv("SCENARIO_RUNNER_ROOT", str(scenario_runner_root))
    monkeypatch.setenv("SCENARIO_RUNNER_CARLA_ROOT", str(carla_root))
    get_settings.cache_clear()

    settings = get_settings()
    run_store = RunStore(settings.runs_root)
    artifact_store = ArtifactStore(settings.artifacts_root)
    command_queue = FileCommandQueue(settings.commands_root)
    manager = RunManager(
        run_store=run_store,
        artifact_store=artifact_store,
        command_queue=command_queue,
        gateway_store=GatewayStore(settings.gateways_root),
    )
    controller = ScenarioRunnerController(
        settings=settings,
        run_store=run_store,
        artifact_store=artifact_store,
    )

    captured: dict[str, object] = {}

    def fake_spawn_background_traffic(run_id: str, descriptor: object) -> None:
        captured["run_id"] = run_id
        captured["vehicles"] = descriptor.traffic.num_vehicles
        captured["walkers"] = descriptor.traffic.num_walkers
        return None

    monkeypatch.setattr(
        controller,
        "_spawn_background_traffic",
        fake_spawn_background_traffic,
    )
    monkeypatch.setattr(
        "app.executor.scenario_runner_controller.threading.Event.wait",
        lambda self, timeout=None: False,
    )

    descriptor = {
        "version": 1,
        "scenario_name": "free_drive_sensor_collection",
        "map_name": "Town03",
        "weather": {"preset": "ClearNoon"},
        "sync": {"enabled": True, "fixed_delta_seconds": 0.05},
        "ego_vehicle": {
            "blueprint": "vehicle.lincoln.mkz_2017",
            "spawn_point": {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
            },
        },
        "traffic": {"enabled": True, "num_vehicles": 2, "num_walkers": 1, "seed": 21},
        "sensors": {"enabled": False, "sensors": []},
        "termination": {"timeout_seconds": 30, "success_condition": "timeout"},
        "recorder": {"enabled": False},
        "debug": {"viewer_friendly": False},
        "metadata": {"author": "test", "tags": ["scenario_runner"], "description": "test"},
    }

    run = manager.create_run(
        descriptor_payload=descriptor,
        scenario_source={
            "provider": "scenario_runner",
            "version": "generated",
            "launch_mode": "python_scenario",
            "scenario_class": "DuckparkFreeDrive",
            "generated_config_path": str(tmp_path / "generated.xml"),
            "additional_scenario_path": str(tmp_path / "duckpark_free_drive.py"),
        },
    )
    Path(run.scenario_source["generated_config_path"]).write_text(
        "<scenarios><scenario name='DuckparkFreeDrive' type='DuckparkFreeDrive' town='Town03'/></scenarios>",
        encoding="utf-8",
    )
    Path(run.scenario_source["additional_scenario_path"]).write_text(
        "class DuckparkFreeDrive:\n    pass\n",
        encoding="utf-8",
    )

    run_store.transition(run.run_id, run.status.__class__.QUEUED)
    controller.execute_run(run.run_id)

    assert captured["run_id"] == run.run_id
    assert captured["vehicles"] == 2
    assert captured["walkers"] == 1

    event_types = [
        event["event_type"] for event in artifact_store.read_events(run.run_id)
    ]
    assert "BACKGROUND_TRAFFIC_TRIGGER_FALLBACK" in event_types
