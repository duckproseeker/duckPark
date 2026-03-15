from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import app
from app.core.config import get_settings


def _write_fake_carla_pythonapi(carla_root) -> None:
    agents_root = carla_root / "PythonAPI" / "carla" / "agents" / "navigation"
    agents_root.mkdir(parents=True, exist_ok=True)
    (agents_root.parent / "__init__.py").write_text("", encoding="utf-8")
    (agents_root / "__init__.py").write_text("", encoding="utf-8")
    dist_root = carla_root / "PythonAPI" / "carla" / "dist"
    dist_root.mkdir(parents=True, exist_ok=True)
    (dist_root / "carla-0.9.16-py3.9-linux-x86_64.egg").write_text("", encoding="utf-8")


VALID_DESCRIPTOR = {
    "version": 1,
    "scenario_name": "osc_follow_leading_vehicle",
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
    "metadata": {"author": "test", "tags": ["api"], "description": "api test"},
}


def test_create_start_stop_run() -> None:
    client = TestClient(app)

    create_resp = client.post("/runs", json={"descriptor": VALID_DESCRIPTOR})
    assert create_resp.status_code == 200
    run_id = create_resp.json()["data"]["run_id"]

    start_resp = client.post(f"/runs/{run_id}/start")
    assert start_resp.status_code == 200
    assert start_resp.json()["data"]["status"] == "QUEUED"
    assert "created_at_utc" in start_resp.json()["data"]
    assert "updated_at_utc" in start_resp.json()["data"]
    assert "started_at_utc" in start_resp.json()["data"]
    assert "sim_time" in start_resp.json()["data"]
    assert "executed_tick_count" in start_resp.json()["data"]
    assert "achieved_tick_rate_hz" in start_resp.json()["data"]
    assert "wall_elapsed_seconds" in start_resp.json()["data"]

    stop_resp = client.post(f"/runs/{run_id}/stop")
    assert stop_resp.status_code == 200
    assert stop_resp.json()["data"]["status"] == "CANCELED"

    get_resp = client.get(f"/runs/{run_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["status"] == "CANCELED"
    assert "started_at_utc" in get_resp.json()["data"]
    assert "ended_at_utc" in get_resp.json()["data"]

    events_resp = client.get(f"/runs/{run_id}/events")
    assert events_resp.status_code == 200
    assert len(events_resp.json()["data"]) >= 2


def test_create_run_with_hil_config_and_evaluation_profile() -> None:
    client = TestClient(app)

    register_resp = client.post(
        "/gateways/register",
        json={
            "gateway_id": "rpi5-x1301-01",
            "name": "bench-a",
            "capabilities": {
                "video_input_modes": ["hdmi_x1301", "frame_stream"],
                "dut_output_modes": ["uvc_gadget"],
            },
        },
    )
    assert register_resp.status_code == 200

    create_resp = client.post(
        "/runs",
        json={
            "descriptor": VALID_DESCRIPTOR,
            "hil_config": {
                "mode": "camera_open_loop",
                "gateway_id": "rpi5-x1301-01",
                "video_source": "hdmi_x1301",
                "dut_input_mode": "uvc_camera",
                "result_ingest_mode": "http_push",
            },
            "evaluation_profile": {
                "profile_name": "yolo_open_loop_v1",
                "metrics": ["precision", "recall"],
                "iou_threshold": 0.5,
                "classes": ["car"],
            },
        },
    )
    assert create_resp.status_code == 200

    run_id = create_resp.json()["data"]["run_id"]
    get_resp = client.get(f"/runs/{run_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["hil_config"]["gateway_id"] == "rpi5-x1301-01"
    assert (
        get_resp.json()["data"]["evaluation_profile"]["profile_name"]
        == "yolo_open_loop_v1"
    )


def test_get_run_environment_for_scenario_runner_run() -> None:
    client = TestClient(app)

    create_resp = client.post("/runs", json={"descriptor": VALID_DESCRIPTOR})
    assert create_resp.status_code == 200
    run_id = create_resp.json()["data"]["run_id"]

    get_resp = client.get(f"/runs/{run_id}/environment")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["descriptor_weather"]["preset"] == "ClearNoon"
    assert get_resp.json()["data"]["runtime_control"]["weather"] is None
    assert get_resp.json()["data"]["runtime_control"]["debug"] is None


def test_run_viewer_info_on_created_run() -> None:
    client = TestClient(app)

    create_resp = client.post("/runs", json={"descriptor": VALID_DESCRIPTOR})
    assert create_resp.status_code == 200
    run_id = create_resp.json()["data"]["run_id"]

    viewer_resp = client.get(f"/runs/{run_id}/viewer")
    assert viewer_resp.status_code == 200
    payload = viewer_resp.json()["data"]
    assert payload["available"] is False
    assert len(payload["views"]) >= 2
    assert payload["snapshot_url"].endswith("/viewer/frame")
    assert payload["stream_ws_path"].endswith("/ws/runs/" + run_id + "/viewer")
    assert payload["playback_interval_ms"] >= payload["stream_interval_ms"]
    assert payload["stream_buffer_min_frames"] >= 1
    assert payload["stream_buffer_max_frames"] > payload["stream_buffer_min_frames"]

    frame_resp = client.get(f"/runs/{run_id}/viewer/frame")
    assert frame_resp.status_code == 409


def test_update_run_environment_rejects_official_runner_run(
    tmp_path, monkeypatch
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
                '  <RoadNetwork><LogicFile filepath="Town01"/></RoadNetwork>',
                "  <Entities>",
                '    <ScenarioObject name="hero"><Vehicle name="vehicle.lincoln.mkz_2017" vehicleCategory="car"/></ScenarioObject>',
                "  </Entities>",
                "  <Storyboard/>",
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
    create_resp = client.post(
        "/runs",
        json={
            "descriptor": {
                **VALID_DESCRIPTOR,
                "scenario_name": "osc_follow_leading_vehicle",
                "map_name": "Town01",
            }
        },
    )
    assert create_resp.status_code == 200
    run_id = create_resp.json()["data"]["run_id"]

    update_resp = client.post(
        f"/runs/{run_id}/environment",
        json={
            "weather": {"preset": "CloudyNoon"},
            "debug": {"viewer_friendly": True},
        },
    )
    assert update_resp.status_code == 409
