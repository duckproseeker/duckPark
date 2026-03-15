from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree

from fastapi.testclient import TestClient

from app.api.main import app
from app.core.config import get_settings
from app.orchestrator.queue import FileCommandQueue
from app.scenario.official_runner import (
    build_scenario_runner_pythonpath,
    scenario_runner_runtime_issues,
)


def _write_fake_carla_pythonapi(carla_root: Path) -> None:
    agents_root = carla_root / "PythonAPI" / "carla" / "agents" / "navigation"
    agents_root.mkdir(parents=True, exist_ok=True)
    (agents_root.parent / "__init__.py").write_text("", encoding="utf-8")
    (agents_root / "__init__.py").write_text("", encoding="utf-8")
    dist_root = carla_root / "PythonAPI" / "carla" / "dist"
    dist_root.mkdir(parents=True, exist_ok=True)
    (dist_root / "carla-0.9.16-py3.9-linux-x86_64.egg").write_text("", encoding="utf-8")


def _write_fake_flat_carla_repo(carla_root: Path) -> None:
    agents_root = carla_root / "agents" / "navigation"
    agents_root.mkdir(parents=True, exist_ok=True)
    (carla_root / "agents" / "__init__.py").write_text("", encoding="utf-8")
    (agents_root / "__init__.py").write_text("", encoding="utf-8")


def test_scenario_catalog_and_environment_endpoints() -> None:
    client = TestClient(app)

    catalog_resp = client.get("/scenarios/catalog")
    assert catalog_resp.status_code == 200
    items = catalog_resp.json()["data"]["items"]
    assert len(items) >= 5
    assert all(item["execution_support"] == "scenario_runner" for item in items)
    assert all(item["execution_backend"] == "scenario_runner" for item in items)
    assert all("launch_capabilities" in item for item in items)
    assert any(item["scenario_id"] == "free_drive_sensor_collection" for item in items)
    assert any(item["scenario_id"] == "osc_follow_leading_vehicle" for item in items)
    assert any(item["scenario_id"] == "osc_lane_change_simple" for item in items)
    assert any(item["scenario_id"] == "osc_pedestrian_crossing_front" for item in items)

    env_resp = client.get("/scenarios/environment-presets")
    assert env_resp.status_code == 200
    env_items = env_resp.json()["data"]["items"]
    assert any(item["preset_id"] == "clear_day" for item in env_items)


def test_sensor_profiles_endpoint_reads_yaml(tmp_path: Path) -> None:
    settings = get_settings()
    sensor_root = settings.sensor_profiles_root
    sensor_root.mkdir(parents=True, exist_ok=True)
    profile_path = sensor_root / "test_profile.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "profile_name: test_profile",
                "display_name: Test Profile",
                "description: test sensors",
                "sensors:",
                "  - id: FrontRGB",
                "    type: sensor.camera.rgb",
                "    x: 1.0",
                "    y: 0.0",
                "    z: 1.5",
                "    width: 1280",
                "    height: 720",
                "    fov: 90.0",
            ]
        ),
        encoding="utf-8",
    )

    client = TestClient(app)
    resp = client.get("/scenarios/sensor-profiles")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["profile_name"] == "test_profile"
    assert "raw_yaml" in items[0]


def test_sensor_profiles_save_endpoint_writes_yaml(tmp_path: Path) -> None:
    settings = get_settings()
    client = TestClient(app)

    payload = {
        "profile_name": "vehicle_sedan_alpha",
        "display_name": "Sedan Alpha",
        "description": "车型 Alpha 的前向采集模板",
        "vehicle_model": "vehicle.lincoln.mkz_2017",
        "metadata": {"category": "ops", "source": "duckpark"},
        "sensors": [
            {
                "id": "FrontRGB",
                "type": "sensor.camera.rgb",
                "x": 1.65,
                "y": 0.0,
                "z": 1.72,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
                "width": 1920,
                "height": 1080,
                "fov": 100.0,
            },
            {
                "id": "RoofLidar",
                "type": "sensor.lidar.ray_cast",
                "x": 0.15,
                "y": 0.0,
                "z": 2.05,
                "channels": 64,
                "range": 85.0,
                "points_per_second": 600000,
                "rotation_frequency": 10.0,
            },
        ],
    }

    resp = client.put(
        f"/scenarios/sensor-profiles/{payload['profile_name']}",
        json=payload,
    )
    assert resp.status_code == 200, resp.text
    saved = resp.json()["data"]
    assert saved["profile_name"] == "vehicle_sedan_alpha"
    assert saved["vehicle_model"] == "vehicle.lincoln.mkz_2017"
    assert saved["metadata"]["category"] == "ops"
    assert len(saved["sensors"]) == 2

    saved_path = settings.sensor_profiles_root / "vehicle_sedan_alpha.yaml"
    assert saved_path.exists()
    saved_text = saved_path.read_text(encoding="utf-8")
    assert "vehicle_model: vehicle.lincoln.mkz_2017" in saved_text
    assert "id: FrontRGB" in saved_text
    assert "id: RoofLidar" in saved_text

    list_resp = client.get("/scenarios/sensor-profiles")
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]["items"]
    item = next(
        entry for entry in items if entry["profile_name"] == "vehicle_sedan_alpha"
    )
    assert item["display_name"] == "Sedan Alpha"
    assert item["vehicle_model"] == "vehicle.lincoln.mkz_2017"


def test_scenario_catalog_marks_official_runner_items_when_environment_present(
    tmp_path: Path, monkeypatch
) -> None:
    scenario_runner_root = tmp_path / "scenario_runner"
    (scenario_runner_root / "srunner" / "examples").mkdir(parents=True, exist_ok=True)
    (scenario_runner_root / "scenario_runner.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    (
        scenario_runner_root / "srunner" / "examples" / "FollowLeadingVehicle.xosc"
    ).write_text(
        "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                "<OpenSCENARIO>",
                '  <ParameterDeclarations><ParameterDeclaration name="leadingSpeed" parameterType="double" value="2.0"/></ParameterDeclarations>',
                '  <RoadNetwork><LogicFile filepath="Town01"/></RoadNetwork>',
                "  <Entities>",
                '    <ScenarioObject name="hero"><Vehicle name="vehicle.lincoln.mkz_2017" vehicleCategory="car"/></ScenarioObject>',
                '    <ScenarioObject name="adversary"><Vehicle name="vehicle.tesla.model3" vehicleCategory="car"/></ScenarioObject>',
                "  </Entities>",
                "  <Storyboard>",
                '    <Story name="Story"><Act name="Act"><ManeuverGroup maximumExecutionCount="1"><Actors selectTriggeringEntities="false"><EntityRef entityRef="adversary"/></Actors><Maneuver name="Maneuver"><Event name="LeadingVehicleKeepsVelocity" priority="overwrite"/></Maneuver></ManeuverGroup></Act></Story>',
                "  </Storyboard>",
                "</OpenSCENARIO>",
            ]
        ),
        encoding="utf-8",
    )
    carla_root = tmp_path / "carla"
    _write_fake_carla_pythonapi(carla_root)

    monkeypatch.setenv("SCENARIO_RUNNER_ROOT", str(scenario_runner_root))
    monkeypatch.setenv("SCENARIO_RUNNER_CARLA_ROOT", str(carla_root))
    get_settings.cache_clear()

    client = TestClient(app)
    catalog_resp = client.get("/scenarios/catalog")
    assert catalog_resp.status_code == 200
    items = catalog_resp.json()["data"]["items"]
    official_item = next(
        item for item in items if item["scenario_id"] == "osc_follow_leading_vehicle"
    )
    free_drive_item = next(
        item for item in items if item["scenario_id"] == "free_drive_sensor_collection"
    )
    assert official_item["execution_support"] == "scenario_runner"
    assert official_item["execution_backend"] == "scenario_runner"
    assert official_item["category"] == "vehicle_following"
    assert official_item["default_map_name"] == "Town01"
    assert official_item["parameter_declarations"][0]["name"] == "leadingSpeed"
    assert official_item["parameter_schema"][0]["field"] == "leadingSpeed"
    assert official_item["parameter_schema"][0]["type"] == "number"
    assert official_item["parameter_schema"][0]["default"] == 2.0
    assert official_item["launch_capabilities"]["map_editable"] is False
    assert free_drive_item["launch_capabilities"]["map_editable"] is True
    assert free_drive_item["launch_capabilities"]["sensor_profile_editable"] is True
    assert free_drive_item["parameter_schema"][0]["field"] == "targetSpeedMps"


def test_launch_endpoint_generates_per_run_spec_and_xosc(
    tmp_path: Path, monkeypatch
) -> None:
    scenario_runner_root = tmp_path / "scenario_runner"
    (scenario_runner_root / "srunner" / "examples").mkdir(parents=True, exist_ok=True)
    (scenario_runner_root / "scenario_runner.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    (
        scenario_runner_root / "srunner" / "examples" / "FollowLeadingVehicle.xosc"
    ).write_text(
        "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                "<OpenSCENARIO>",
                '  <ParameterDeclarations><ParameterDeclaration name="leadingSpeed" parameterType="double" value="2.0"/></ParameterDeclarations>',
                "  <RoadNetwork><LogicFile filepath=\"Town01\"/></RoadNetwork>",
                "  <Storyboard>",
                "    <Init>",
                "      <Actions>",
                "        <GlobalAction>",
                "          <EnvironmentAction>",
                "            <Environment name=\"TemplateEnvironment\">",
                "              <TimeOfDay animation=\"false\" dateTime=\"2020-01-01T12:00:00\"/>",
                "              <Weather cloudState=\"free\">",
                "                <Sun azimuth=\"0\" elevation=\"1.0\" intensity=\"1.0\"/>",
                "                <Fog visualRange=\"100000.0\"/>",
                "                <Precipitation precipitationType=\"dry\" intensity=\"0.0\"/>",
                "              </Weather>",
                "              <RoadCondition frictionScaleFactor=\"1.0\"/>",
                "            </Environment>",
                "          </EnvironmentAction>",
                "        </GlobalAction>",
                "      </Actions>",
                "    </Init>",
                "    <Story name=\"Story\">",
                "      <Act name=\"Act\">",
                "        <ManeuverGroup name=\"ManeuverGroup\" maximumExecutionCount=\"1\">",
                "          <Actors selectTriggeringEntities=\"false\">",
                "            <EntityRef entityRef=\"adversary\"/>",
                "          </Actors>",
                "          <Maneuver name=\"Maneuver\">",
                "            <Event name=\"LeadingVehicleKeepsVelocity\" priority=\"overwrite\">",
                "              <Action name=\"LeadingVehicleKeepsVelocity\">",
                "                <PrivateAction>",
                "                  <LongitudinalAction>",
                "                    <SpeedAction>",
                "                      <SpeedActionDynamics dynamicsShape=\"step\" value=\"20\" dynamicsDimension=\"distance\"/>",
                "                      <SpeedActionTarget>",
                "                        <AbsoluteTargetSpeed value=\"$leadingSpeed\"/>",
                "                      </SpeedActionTarget>",
                "                    </SpeedAction>",
                "                  </LongitudinalAction>",
                "                </PrivateAction>",
                "              </Action>",
                "              <StartTrigger>",
                "                <ConditionGroup>",
                "                  <Condition name=\"StartConditionLeadingVehicleKeepsVelocity\" delay=\"0\" conditionEdge=\"rising\">",
                "                    <ByEntityCondition>",
                "                      <TriggeringEntities triggeringEntitiesRule=\"any\">",
                "                        <EntityRef entityRef=\"hero\"/>",
                "                      </TriggeringEntities>",
                "                      <EntityCondition>",
                "                        <RelativeDistanceCondition entityRef=\"adversary\" relativeDistanceType=\"longitudinal\" value=\"40.0\" freespace=\"true\" rule=\"lessThan\"/>",
                "                      </EntityCondition>",
                "                    </ByEntityCondition>",
                "                  </Condition>",
                "                </ConditionGroup>",
                "              </StartTrigger>",
                "            </Event>",
                "          </Maneuver>",
                "        </ManeuverGroup>",
                "        <StopTrigger>",
                "          <ConditionGroup>",
                "            <Condition name=\"EndCondition\" delay=\"0\" conditionEdge=\"rising\">",
                "              <ByEntityCondition>",
                "                <TriggeringEntities triggeringEntitiesRule=\"any\">",
                "                  <EntityRef entityRef=\"hero\"/>",
                "                </TriggeringEntities>",
                "                <EntityCondition>",
                "                  <TraveledDistanceCondition value=\"200.0\"/>",
                "                </EntityCondition>",
                "              </ByEntityCondition>",
                "            </Condition>",
                "          </ConditionGroup>",
                "        </StopTrigger>",
                "      </Act>",
                "    </Story>",
                "  </Storyboard>",
                "</OpenSCENARIO>",
            ]
        ),
        encoding="utf-8",
    )
    carla_root = tmp_path / "carla"
    _write_fake_carla_pythonapi(carla_root)

    monkeypatch.setenv("SCENARIO_RUNNER_ROOT", str(scenario_runner_root))
    monkeypatch.setenv("SCENARIO_RUNNER_CARLA_ROOT", str(carla_root))
    get_settings.cache_clear()

    client = TestClient(app)
    resp = client.post(
        "/scenarios/launch",
        json={
            "scenario_id": "osc_follow_leading_vehicle",
            "map_name": "Town03",
            "weather": {
                "preset": "HardRainNoon",
                "precipitation": 85.0,
                "fog_density": 20.0,
            },
            "traffic": {"num_vehicles": 6, "num_walkers": 2},
            "template_params": {"leadingSpeed": 5.5},
            "timeout_seconds": 45,
            "auto_start": False,
            "metadata": {
                "author": "api-test",
                "description": "launch route",
                "tags": ["smoke"],
            },
        },
    )

    assert resp.status_code == 200, resp.text
    payload = resp.json()["data"]
    assert payload["status"] == "CREATED"
    assert payload["map_name"] == "Town01"
    assert payload["weather"]["preset"] == "HardRainNoon"
    assert payload["weather"]["precipitation"] == 85.0
    assert payload["traffic"]["num_vehicles"] == 6
    assert payload["traffic"]["num_walkers"] == 2
    assert payload["scenario_source"]["version"] == "generated"

    generated_xosc_path = Path(payload["scenario_source"]["generated_xosc_path"])
    generated_spec_path = Path(payload["scenario_source"]["generated_spec_path"])
    assert generated_xosc_path.exists()
    assert generated_spec_path.exists()

    spec_payload = json.loads(generated_spec_path.read_text(encoding="utf-8"))
    assert spec_payload["descriptor"]["map_name"] == "Town01"
    assert spec_payload["descriptor"]["traffic"]["num_vehicles"] == 6
    assert spec_payload["descriptor"]["traffic"]["num_walkers"] == 2
    assert spec_payload["descriptor"]["termination"]["timeout_seconds"] == 45
    assert spec_payload["launch_request"]["scenario_id"] == "osc_follow_leading_vehicle"
    assert spec_payload["resolved_template_params"] == {"leadingSpeed": 5.5}

    generated_root = ElementTree.parse(generated_xosc_path).getroot()
    parameter_declaration = generated_root.find(
        "./ParameterDeclarations/ParameterDeclaration[@name='leadingSpeed']"
    )
    assert parameter_declaration is not None
    assert parameter_declaration.attrib["value"] == "5.5"
    hero_controller_module = generated_root.find(
        "./Storyboard/Init/Actions/Private[@entityRef='hero']/PrivateAction/ControllerAction/"
        "AssignControllerAction/Controller/Properties/Property[@name='module']"
    )
    assert hero_controller_module is not None
    assert hero_controller_module.attrib["value"].endswith(
        "app/scenario/controllers/duckpark_autopilot.py"
    )
    traffic_manager_port = generated_root.find(
        "./Storyboard/Init/Actions/Private[@entityRef='hero']/PrivateAction/ControllerAction/"
        "AssignControllerAction/Controller/Properties/Property[@name='traffic_manager_port']"
    )
    assert traffic_manager_port is not None
    assert traffic_manager_port.attrib["value"] == "8010"
    target_speed = generated_root.find(
        "./Storyboard/Init/Actions/Private[@entityRef='hero']/PrivateAction/ControllerAction/"
        "AssignControllerAction/Controller/Properties/Property[@name='target_speed_mps']"
    )
    assert target_speed is not None
    assert target_speed.attrib["value"] == "10.0"
    adversary_controller_module = generated_root.find(
        "./Storyboard/Init/Actions/Private[@entityRef='adversary']/PrivateAction/ControllerAction/"
        "AssignControllerAction/Controller/Properties/Property[@name='module']"
    )
    assert adversary_controller_module is not None
    assert adversary_controller_module.attrib["value"].endswith(
        "app/scenario/controllers/duckpark_autopilot.py"
    )
    adversary_target_speed = generated_root.find(
        "./Storyboard/Init/Actions/Private[@entityRef='adversary']/PrivateAction/ControllerAction/"
        "AssignControllerAction/Controller/Properties/Property[@name='target_speed_mps']"
    )
    assert adversary_target_speed is not None
    assert adversary_target_speed.attrib["value"] == "5.5"
    adversary_override = generated_root.find(
        "./Storyboard/Init/Actions/Private[@entityRef='adversary']/PrivateAction/ControllerAction/"
        "OverrideControllerValueAction"
    )
    assert adversary_override is not None
    start_condition = generated_root.find(
        ".//Event[@name='LeadingVehicleKeepsVelocity']/StartTrigger/ConditionGroup/Condition/ByValueCondition/SimulationTimeCondition"
    )
    assert start_condition is not None
    assert start_condition.attrib["value"] == "1.0"
    assert start_condition.attrib["rule"] == "greaterThan"
    speed_dynamics = generated_root.find(
        ".//Event[@name='LeadingVehicleKeepsVelocity']"
        "/Action/PrivateAction/LongitudinalAction/SpeedAction/SpeedActionDynamics"
    )
    assert speed_dynamics is not None
    assert speed_dynamics.attrib["dynamicsDimension"] == "time"
    assert speed_dynamics.attrib["value"] == "1.0"
    wait_start_condition = generated_root.find(
        ".//Event[@name='LeadingVehicleWaits']/StartTrigger/ConditionGroup/Condition/ByValueCondition/SimulationTimeCondition"
    )
    if wait_start_condition is not None:
        assert wait_start_condition.attrib["value"] == "75.0"
        assert wait_start_condition.attrib["rule"] == "greaterThan"
    timeout_condition = generated_root.find(
        "./Storyboard/Story/Act/StopTrigger/ConditionGroup/Condition/ByValueCondition/SimulationTimeCondition"
    )
    assert timeout_condition is not None
    assert timeout_condition.attrib["value"] == "45.0"
    assert timeout_condition.attrib["rule"] == "greaterThan"
    logic_file = generated_root.find("./RoadNetwork/LogicFile")
    assert logic_file is not None
    assert logic_file.attrib["filepath"] == "Town01"

    assert FileCommandQueue(get_settings().commands_root).count_pending() == 0


def test_launch_endpoint_generates_python_scenario_config_and_sensor_descriptor(
    tmp_path: Path, monkeypatch
) -> None:
    scenario_runner_root = tmp_path / "scenario_runner"
    (scenario_runner_root / "srunner" / "examples").mkdir(parents=True, exist_ok=True)
    (scenario_runner_root / "scenario_runner.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    carla_root = tmp_path / "carla"
    _write_fake_carla_pythonapi(carla_root)

    monkeypatch.setenv("SCENARIO_RUNNER_ROOT", str(scenario_runner_root))
    monkeypatch.setenv("SCENARIO_RUNNER_CARLA_ROOT", str(carla_root))
    monkeypatch.setenv("SENSOR_PROFILES_ROOT", str(tmp_path / "sensors"))
    get_settings.cache_clear()

    settings = get_settings()
    sensor_root = settings.sensor_profiles_root
    sensor_root.mkdir(parents=True, exist_ok=True)
    (sensor_root / "front_rgb.yaml").write_text(
        "\n".join(
            [
                "profile_name: front_rgb",
                "display_name: Front RGB",
                "description: front rgb",
                "sensors:",
                "  - id: FrontRGB",
                "    type: sensor.camera.rgb",
                "    x: 1.5",
                "    y: 0.0",
                "    z: 1.7",
                "    width: 1280",
                "    height: 720",
                "    fov: 90.0",
            ]
        ),
        encoding="utf-8",
    )

    client = TestClient(app)
    resp = client.post(
        "/scenarios/launch",
        json={
            "scenario_id": "free_drive_sensor_collection",
            "map_name": "Town05",
            "weather": {
                "preset": "CloudySunset",
                "cloudiness": 65.0,
                "sun_altitude_angle": 18.0,
            },
            "traffic": {"num_vehicles": 14, "num_walkers": 6},
            "sensor_profile_name": "front_rgb",
            "template_params": {"targetSpeedMps": 7.5},
            "timeout_seconds": 90,
            "auto_start": False,
        },
    )

    assert resp.status_code == 200, resp.text
    payload = resp.json()["data"]
    assert payload["map_name"] == "Town05"
    assert payload["scenario_source"]["launch_mode"] == "python_scenario"
    assert payload["sensors"]["enabled"] is True
    assert payload["sensors"]["profile_name"] == "front_rgb"
    assert payload["sensors"]["sensors"][0]["type"] == "sensor.camera.rgb"
    assert isinstance(payload["traffic"]["seed"], int)
    assert payload["traffic"]["seed"] >= 0

    config_path = Path(payload["scenario_source"]["generated_config_path"])
    spec_path = Path(payload["scenario_source"]["generated_spec_path"])
    assert config_path.exists()
    assert spec_path.exists()

    config_root = ElementTree.parse(config_path).getroot()
    scenario_node = config_root.find("./scenario")
    assert scenario_node is not None
    assert scenario_node.attrib["type"] == "DuckparkFreeDrive"
    assert scenario_node.attrib["town"] == "Town05"
    ego_vehicle = scenario_node.find("./ego_vehicle")
    assert ego_vehicle is not None
    assert ego_vehicle.attrib["random_location"] == "true"
    free_drive = scenario_node.find("./duckpark_free_drive")
    assert free_drive is not None
    assert free_drive.attrib["target_speed_mps"] == "7.5"
    assert free_drive.attrib["timeout_seconds"] == "90"
    assert free_drive.attrib["roaming_seed"] == str(payload["traffic"]["seed"])

    spec_payload = json.loads(spec_path.read_text(encoding="utf-8"))
    assert spec_payload["descriptor"]["map_name"] == "Town05"
    assert spec_payload["descriptor"]["traffic"]["num_vehicles"] == 14
    assert spec_payload["descriptor"]["traffic"]["num_walkers"] == 6
    assert spec_payload["descriptor"]["traffic"]["seed"] == payload["traffic"]["seed"]
    assert spec_payload["descriptor"]["traffic"]["injection_mode"] == "carla_api_near_ego"
    assert spec_payload["descriptor"]["sensors"]["profile_name"] == "front_rgb"
    assert spec_payload["launch_request"]["traffic"]["seed"] == payload["traffic"]["seed"]
    assert spec_payload["resolved_template_params"] == {"targetSpeedMps": 7.5}


def test_launch_endpoint_can_auto_queue_run(tmp_path: Path, monkeypatch) -> None:
    scenario_runner_root = tmp_path / "scenario_runner"
    (scenario_runner_root / "srunner" / "examples").mkdir(parents=True, exist_ok=True)
    (scenario_runner_root / "scenario_runner.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    (
        scenario_runner_root / "srunner" / "examples" / "FollowLeadingVehicle.xosc"
    ).write_text(
        '<?xml version="1.0" encoding="UTF-8"?><OpenSCENARIO><RoadNetwork><LogicFile filepath="Town01"/></RoadNetwork><Storyboard/></OpenSCENARIO>',
        encoding="utf-8",
    )
    carla_root = tmp_path / "carla"
    _write_fake_carla_pythonapi(carla_root)

    monkeypatch.setenv("SCENARIO_RUNNER_ROOT", str(scenario_runner_root))
    monkeypatch.setenv("SCENARIO_RUNNER_CARLA_ROOT", str(carla_root))
    get_settings.cache_clear()

    client = TestClient(app)
    resp = client.post(
        "/scenarios/launch",
        json={"scenario_id": "osc_follow_leading_vehicle", "auto_start": True},
    )

    assert resp.status_code == 200
    payload = resp.json()["data"]
    assert payload["status"] == "QUEUED"
    assert FileCommandQueue(get_settings().commands_root).count_pending() == 1


def test_launch_endpoint_rejects_unknown_template_params(
    tmp_path: Path, monkeypatch
) -> None:
    scenario_runner_root = tmp_path / "scenario_runner"
    (scenario_runner_root / "srunner" / "examples").mkdir(parents=True, exist_ok=True)
    (scenario_runner_root / "scenario_runner.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    (
        scenario_runner_root / "srunner" / "examples" / "FollowLeadingVehicle.xosc"
    ).write_text(
        '<?xml version="1.0" encoding="UTF-8"?><OpenSCENARIO><ParameterDeclarations><ParameterDeclaration name="leadingSpeed" parameterType="double" value="2.0"/></ParameterDeclarations><RoadNetwork><LogicFile filepath="Town01"/></RoadNetwork><Storyboard/></OpenSCENARIO>',
        encoding="utf-8",
    )
    carla_root = tmp_path / "carla"
    _write_fake_carla_pythonapi(carla_root)

    monkeypatch.setenv("SCENARIO_RUNNER_ROOT", str(scenario_runner_root))
    monkeypatch.setenv("SCENARIO_RUNNER_CARLA_ROOT", str(carla_root))
    get_settings.cache_clear()

    client = TestClient(app)
    resp = client.post(
        "/scenarios/launch",
        json={
            "scenario_id": "osc_follow_leading_vehicle",
            "template_params": {"unknownField": 1},
            "auto_start": False,
        },
    )

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "VALIDATION_ERROR"
    assert "unknownField" in resp.json()["detail"]["message"]


def test_scenario_runner_pythonpath_includes_agents_and_carla_egg(
    tmp_path: Path, monkeypatch
) -> None:
    scenario_runner_root = tmp_path / "scenario_runner"
    (scenario_runner_root / "srunner" / "examples").mkdir(parents=True, exist_ok=True)
    (scenario_runner_root / "scenario_runner.py").write_text(
        "#!/usr/bin/env python3\n", encoding="utf-8"
    )
    carla_root = tmp_path / "carla"
    _write_fake_carla_pythonapi(carla_root)

    monkeypatch.setenv("SCENARIO_RUNNER_ROOT", str(scenario_runner_root))
    monkeypatch.setenv("SCENARIO_RUNNER_CARLA_ROOT", str(carla_root))
    get_settings.cache_clear()

    entries = build_scenario_runner_pythonpath()
    issues = scenario_runner_runtime_issues()

    assert any(entry.endswith("scenario_runner") for entry in entries)
    assert any(entry.endswith("scenario_runner/srunner") for entry in entries)
    assert any(
        entry.endswith("carla-0.9.16-py3.9-linux-x86_64.egg") for entry in entries
    )
    assert any(entry.endswith("PythonAPI/carla") for entry in entries)
    assert issues == []


def test_scenario_runner_pythonpath_supports_flat_carla_repo_layout(
    tmp_path: Path, monkeypatch
) -> None:
    from app.scenario import official_runner

    scenario_runner_root = tmp_path / "scenario_runner"
    (scenario_runner_root / "srunner" / "examples").mkdir(parents=True, exist_ok=True)
    (scenario_runner_root / "scenario_runner.py").write_text(
        "#!/usr/bin/env python3\n", encoding="utf-8"
    )
    carla_root = tmp_path / "carla"
    _write_fake_flat_carla_repo(carla_root)

    monkeypatch.setenv("SCENARIO_RUNNER_ROOT", str(scenario_runner_root))
    monkeypatch.setenv("SCENARIO_RUNNER_CARLA_ROOT", str(carla_root))
    monkeypatch.setattr(
        official_runner,
        "_module_available",
        lambda module_name: module_name == "carla",
    )
    get_settings.cache_clear()

    entries = build_scenario_runner_pythonpath()
    issues = scenario_runner_runtime_issues()

    assert any(entry.endswith("scenario_runner") for entry in entries)
    assert any(entry.endswith("scenario_runner/srunner") for entry in entries)
    assert any(entry.endswith("/carla") for entry in entries)
    assert not any(entry.endswith("/carla/source") for entry in entries)
    assert issues == []
