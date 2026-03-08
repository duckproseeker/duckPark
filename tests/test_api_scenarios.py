from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.api.main import app
from app.core.config import get_settings


def test_scenario_catalog_and_environment_endpoints() -> None:
    client = TestClient(app)

    catalog_resp = client.get("/scenarios/catalog")
    assert catalog_resp.status_code == 200
    items = catalog_resp.json()["data"]["items"]
    native_items = [item for item in items if item["execution_support"] == "native"]
    assert len(native_items) >= 10
    assert any(item["execution_support"] == "catalog_only" for item in items)
    assert any(item["scenario_id"] == "control_loss" for item in items)
    assert any(item["scenario_id"] == "change_lane" for item in native_items)
    assert any(item["scenario_id"] == "pedestrian_crossing" for item in native_items)

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
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["profile_name"] == "test_profile"
    assert "raw_yaml" in items[0]
