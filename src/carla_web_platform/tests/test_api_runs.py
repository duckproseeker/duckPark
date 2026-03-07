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
