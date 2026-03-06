from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.scenario.builtins import empty_drive, follow_lane, npc_crossing

DEFAULT_EGO_BLUEPRINT = "vehicle.tesla.model3"
DEFAULT_SPAWN_POINT = {
    "x": 230.0,
    "y": 195.0,
    "z": 0.5,
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 90.0,
}


@dataclass(frozen=True)
class BuiltinScenarioSpec:
    scenario_name: str
    display_name: str
    module: Any
    description: str
    default_map_name: str
    default_timeout_seconds: int
    default_fixed_delta_seconds: float
    weather_preset: str = "ClearNoon"
    traffic_enabled: bool = False
    num_vehicles: int = 0
    num_walkers: int = 0


BUILTIN_SCENARIOS: dict[str, BuiltinScenarioSpec] = {
    "empty_drive": BuiltinScenarioSpec(
        scenario_name="empty_drive",
        display_name="空场景直行",
        module=empty_drive,
        description="仅生成 ego 车辆，不生成 NPC，按固定时长运行。",
        default_map_name="Town01",
        default_timeout_seconds=20,
        default_fixed_delta_seconds=0.05,
        weather_preset="ClearNoon",
    ),
    "follow_lane": BuiltinScenarioSpec(
        scenario_name="follow_lane",
        display_name="车道跟随",
        module=follow_lane,
        description="ego 自动驾驶并保持车道，生成少量 NPC 车辆。",
        default_map_name="Town01",
        default_timeout_seconds=30,
        default_fixed_delta_seconds=0.05,
        weather_preset="CloudyNoon",
        traffic_enabled=True,
        num_vehicles=8,
    ),
    "npc_crossing": BuiltinScenarioSpec(
        scenario_name="npc_crossing",
        display_name="横穿干扰",
        module=npc_crossing,
        description="在 ego 前方创建横穿干扰体，用于集成回归测试。",
        default_map_name="Town01",
        default_timeout_seconds=25,
        default_fixed_delta_seconds=0.05,
        weather_preset="WetNoon",
    ),
}


def _descriptor_template_from_spec(spec: BuiltinScenarioSpec) -> dict[str, Any]:
    return {
        "version": 1,
        "scenario_name": spec.scenario_name,
        "map_name": spec.default_map_name,
        "weather": {"preset": spec.weather_preset},
        "sync": {
            "enabled": True,
            "fixed_delta_seconds": spec.default_fixed_delta_seconds,
        },
        "ego_vehicle": {
            "blueprint": DEFAULT_EGO_BLUEPRINT,
            "spawn_point": DEFAULT_SPAWN_POINT,
        },
        "traffic": {
            "enabled": spec.traffic_enabled,
            "num_vehicles": spec.num_vehicles,
            "num_walkers": spec.num_walkers,
        },
        "sensors": {"enabled": False},
        "termination": {
            "timeout_seconds": spec.default_timeout_seconds,
            "success_condition": "timeout",
        },
        "recorder": {"enabled": False},
        "metadata": {
            "author": "mvp-ui",
            "tags": [spec.scenario_name],
            "description": f"{spec.display_name}（控制台默认模板）",
        },
    }


def list_builtin_scenarios() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for spec in BUILTIN_SCENARIOS.values():
        results.append(
            {
                "scenario_name": spec.scenario_name,
                "display_name": spec.display_name,
                "description": spec.description,
                "default_map_name": spec.default_map_name,
                "descriptor_template": _descriptor_template_from_spec(spec),
            }
        )
    return results


def get_builtin_scenario_module(scenario_name: str) -> Any:
    if scenario_name not in BUILTIN_SCENARIOS:
        raise KeyError(f"Unknown builtin scenario: {scenario_name}")
    return BUILTIN_SCENARIOS[scenario_name].module
