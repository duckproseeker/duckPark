from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import app

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


def test_update_run_environment() -> None:
    client = TestClient(app)

    create_resp = client.post("/runs", json={"descriptor": VALID_DESCRIPTOR})
    assert create_resp.status_code == 200
    run_id = create_resp.json()["data"]["run_id"]

    update_resp = client.post(
        f"/runs/{run_id}/environment",
        json={
            "weather": {
                "preset": "CloudyNoon",
                "cloudiness": 72.0,
                "fog_density": 15.0,
            },
            "debug": {"viewer_friendly": True},
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["weather"]["preset"] == "CloudyNoon"

    get_resp = client.get(f"/runs/{run_id}/environment")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["descriptor_weather"]["cloudiness"] == 72.0
    assert get_resp.json()["data"]["runtime_control"]["debug"]["viewer_friendly"] is True


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

    frame_resp = client.get(f"/runs/{run_id}/viewer/frame")
    assert frame_resp.status_code == 409
