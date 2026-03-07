from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import app


def test_register_list_and_heartbeat_gateway() -> None:
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
            "agent_version": "0.1.0",
            "address": "192.168.110.236",
        },
    )
    assert register_resp.status_code == 200
    assert register_resp.json()["data"]["gateway_id"] == "rpi5-x1301-01"

    heartbeat_resp = client.post(
        "/gateways/rpi5-x1301-01/heartbeat",
        json={
            "status": "READY",
            "metrics": {"input_fps": 30.0, "output_fps": 29.7, "frame_drop_rate": 0.01},
        },
    )
    assert heartbeat_resp.status_code == 200
    assert heartbeat_resp.json()["data"]["status"] == "READY"

    list_resp = client.get("/gateways")
    assert list_resp.status_code == 200
    assert list_resp.json()["data"]["gateways"][0]["gateway_id"] == "rpi5-x1301-01"


def test_list_evaluation_profiles() -> None:
    client = TestClient(app)

    response = client.get("/evaluation-profiles")
    assert response.status_code == 200
    assert response.json()["data"]["profiles"][0]["profile_name"] == "yolo_open_loop_v1"
