from __future__ import annotations

from pathlib import Path
from typing import Any

from app.scenario.launch_builder import default_launch_capabilities


def list_platform_scenario_catalog() -> list[dict[str, Any]]:
    return [build_free_drive_sensor_collection_item()]


def build_free_drive_sensor_collection_item() -> dict[str, Any]:
    scenario_file = (
        Path(__file__).resolve().parent / "runtime" / "duckpark_free_drive.py"
    )
    return {
        "scenario_id": "free_drive_sensor_collection",
        "scenario_name": "free_drive_sensor_collection",
        "display_name": "随机自由行驶 / 传感器采集",
        "description": (
            "面向传感器数据采集的自由行驶模板。支持所有地图随机出生点、"
            "天气、背景车辆/行人和最长运行时长；hero 由平台内置自动驾驶控制，"
            "背景交通会优先围绕 ego 注入。"
        ),
        "default_map_name": "Town01",
        "execution_support": "scenario_runner",
        "execution_backend": "scenario_runner",
        "source": {
            "provider": "scenario_runner",
            "version": "duckpark",
            "launch_mode": "python_scenario",
            "scenario_class": "DuckparkFreeDrive",
            "additional_scenario_path": str(scenario_file),
        },
        "preset": {
            "locked_map_name": "",
            "map_locked": False,
            "event_locked": False,
            "actors_locked": False,
            "weather_runtime_editable": False,
            "event_summary": "随机背景车流和行人产生自然事件，适合长时间传感器采集。",
            "actors_summary": "hero + 可配置背景车辆/行人",
        },
        "parameter_declarations": [],
        "descriptor_template": {
            "version": 1,
            "scenario_name": "free_drive_sensor_collection",
            "map_name": "Town01",
            "weather": {"preset": "ClearNoon"},
            "sync": {"enabled": True, "fixed_delta_seconds": 0.05},
            "ego_vehicle": {
                "blueprint": "vehicle.lincoln.mkz_2017",
                "spawn_point": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.5,
                    "roll": 0.0,
                    "pitch": 0.0,
                    "yaw": 0.0,
                },
            },
            "traffic": {
                "enabled": True,
                "num_vehicles": 20,
                "num_walkers": 16,
                "seed": None,
                "injection_mode": "carla_api_near_ego",
            },
            "sensors": {
                "enabled": True,
                "profile_name": "front_rgb",
                "config_yaml_path": None,
                "sensors": [],
            },
            "termination": {"timeout_seconds": 120, "success_condition": "timeout"},
            "recorder": {"enabled": False},
            "debug": {"viewer_friendly": False},
            "metadata": {
                "author": "duckpark",
                "tags": ["scenario_runner", "free_drive_sensor_collection"],
                "description": "随机自由行驶传感器采集模板",
            },
        },
        "launch_capabilities": default_launch_capabilities(
            map_editable=True,
            sensor_profile_editable=True,
        ),
    }
