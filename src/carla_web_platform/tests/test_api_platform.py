from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import app
from app.core.config import get_settings


def _write_sensor_profile() -> None:
    settings = get_settings()
    profile_path = settings.sensor_profiles_root / "front_rgb.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "profile_name: front_rgb",
                "display_name: Front RGB Camera",
                "description: API test profile",
                "sensors:",
                "  - id: FrontRGB",
                "    type: sensor.camera.rgb",
                "    x: 1.5",
                "    y: 0.0",
                "    z: 1.7",
                "    width: 1920",
                "    height: 1080",
                "    fov: 90.0",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_list_projects_and_benchmark_definitions() -> None:
    client = TestClient(app)

    projects_resp = client.get("/projects")
    definitions_resp = client.get("/benchmark-definitions")

    assert projects_resp.status_code == 200
    assert definitions_resp.status_code == 200
    project_ids = {item["project_id"] for item in projects_resp.json()["data"]["projects"]}
    definition_ids = {
        item["benchmark_definition_id"]
        for item in definitions_resp.json()["data"]["definitions"]
    }
    assert "baseline-validation" in project_ids
    assert "perception-baseline" in definition_ids


def test_create_benchmark_task_and_export_report() -> None:
    _write_sensor_profile()
    client = TestClient(app)

    task_resp = client.post(
        "/benchmark-tasks",
        json={
            "project_id": "baseline-validation",
            "benchmark_definition_id": "perception-baseline",
            "dut_model": "演示开发板",
            "scenario_matrix": [
                {
                    "scenario_id": "empty_drive",
                    "map_name": "Town01",
                    "environment_preset_id": "clear_day",
                    "sensor_profile_name": "front_rgb",
                }
            ],
            "evaluation_profile_name": "yolo_open_loop_v1",
            "auto_start": False,
        },
    )

    assert task_resp.status_code == 200
    task_payload = task_resp.json()["data"]
    assert task_payload["project_id"] == "baseline-validation"
    assert task_payload["benchmark_definition_id"] == "perception-baseline"
    assert task_payload["dut_model"] == "演示开发板"
    assert task_payload["status"] == "CREATED"
    assert task_payload["planned_run_count"] == 1
    assert task_payload["scenario_matrix"][0]["resolved_map_name"] == "Town01_Opt"
    assert len(task_payload["run_ids"]) == 1

    run_id = task_payload["run_ids"][0]
    run_resp = client.get(f"/runs/{run_id}")
    assert run_resp.status_code == 200
    assert run_resp.json()["data"]["map_name"] == "Town01_Opt"
    assert run_resp.json()["data"]["metadata"]["dut_model"] == "演示开发板"

    report_resp = client.post(
        "/reports/export",
        json={"benchmark_task_id": task_payload["benchmark_task_id"]},
    )
    assert report_resp.status_code == 200
    report_payload = report_resp.json()["data"]
    assert report_payload["benchmark_task_id"] == task_payload["benchmark_task_id"]
    assert report_payload["dut_model"] == "演示开发板"
    assert report_payload["status"] == "READY"

    download_resp = client.get(
        f"/reports/{report_payload['report_id']}/download?format=json"
    )
    assert download_resp.status_code == 200
    assert report_payload["report_id"] in download_resp.text
