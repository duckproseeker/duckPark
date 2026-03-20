from __future__ import annotations

from typing import Any

from app.scenario.launch_builder import default_launch_capabilities


def list_platform_scenario_catalog() -> list[dict[str, Any]]:
    return [
        build_town10_autonomous_demo_item(),
        build_free_drive_sensor_collection_item(),
    ]


def build_town10_autonomous_demo_item() -> dict[str, Any]:
    return {
        "scenario_id": "town10_autonomous_demo",
        "scenario_name": "town10_autonomous_demo",
        "display_name": "Town10 自动驾驶演示",
        "description": (
            "面向联调和客户演示的自动驾驶接管模板。固定 Town10HD_Opt，"
            "hero 由平台内置自动驾驶接管，适合配合 CARLA 跟随视角、"
            "Pi HDMI 采集和 Jetson 手动推理展示整条链路。默认保持长驻运行，"
            "由执行页 Stop 按钮手动结束。"
        ),
        "default_map_name": "Town10HD_Opt",
        "execution_support": "native",
        "execution_backend": "native",
        "web_hidden": False,
        "source": {
            "provider": "native",
            "version": "duckpark_native",
            "launch_mode": "native_descriptor",
            "template_params": {"targetSpeedMps": 6.5},
        },
        "preset": {
            "locked_map_name": "Town10HD_Opt",
            "map_locked": True,
            "event_locked": False,
            "actors_locked": False,
            "weather_runtime_editable": False,
            "event_summary": (
                "平台自动驾驶在 Town10HD_Opt 内长驻巡航，便于持续展示前视画面与推理结果；"
                "默认通过执行页 Stop 手动结束。"
            ),
            "actors_summary": "hero + 演示级背景车辆/行人，默认围绕 ego 注入",
        },
        "parameter_declarations": [],
        "descriptor_template": {
            "version": 1,
            "scenario_name": "town10_autonomous_demo",
            "map_name": "Town10HD_Opt",
            "weather": {"preset": "ClearNoon"},
            "sync": {"enabled": False, "fixed_delta_seconds": 1.0 / 30.0},
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
                "num_vehicles": 12,
                "num_walkers": 8,
                "seed": None,
                "injection_mode": "carla_api_near_ego",
            },
            "sensors": {
                "enabled": True,
                "auto_start": False,
                "profile_name": "front_rgb",
                "config_yaml_path": None,
                "sensors": [],
            },
            "termination": {"timeout_seconds": 86400, "success_condition": "manual_stop"},
            "recorder": {"enabled": True},
            "debug": {"viewer_friendly": False},
            "metadata": {
                "author": "duckpark",
                "tags": ["native", "town10_autonomous_demo", "demo"],
                "description": "Town10 自动驾驶演示模板",
            },
        },
        "launch_capabilities": default_launch_capabilities(
            map_editable=False,
            sensor_profile_editable=False,
            timeout_editable=False,
        ),
    }


def build_free_drive_sensor_collection_item() -> dict[str, Any]:
    return {
        "scenario_id": "free_drive_sensor_collection",
        "scenario_name": "free_drive_sensor_collection",
        "display_name": "随机自由行驶 / 传感器采集",
        "description": (
            "面向传感器数据采集的自由行驶模板。支持所有地图随机出生点、"
            "天气、背景车辆/行人和最长运行时长；hero 由平台内置自动驾驶控制，"
            "背景交通会优先围绕 ego 注入。"
        ),
        "default_map_name": "Town10HD_Opt",
        "execution_support": "native",
        "execution_backend": "native",
        "web_hidden": False,
        "source": {
            "provider": "native",
            "version": "duckpark_native",
            "launch_mode": "native_descriptor",
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
            "map_name": "Town10HD_Opt",
            "weather": {"preset": "ClearNoon"},
            "sync": {"enabled": False, "fixed_delta_seconds": 1.0 / 30.0},
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
                "auto_start": False,
                "profile_name": "front_rgb",
                "config_yaml_path": None,
                "sensors": [],
            },
            "termination": {"timeout_seconds": 120, "success_condition": "timeout"},
            "recorder": {"enabled": True},
            "debug": {"viewer_friendly": False},
            "metadata": {
                "author": "duckpark",
                "tags": ["native", "free_drive_sensor_collection"],
                "description": "随机自由行驶传感器采集模板",
            },
        },
        "launch_capabilities": default_launch_capabilities(
            map_editable=True,
            sensor_profile_editable=True,
        ),
    }
