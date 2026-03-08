from __future__ import annotations

from dataclasses import dataclass, field
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
    source: dict[str, str] = field(default_factory=dict)


def _official_source(class_name: str, source_file: str) -> dict[str, str]:
    return {
        "provider": "scenario_runner_adapted",
        "version": "v0.9.16",
        "class_name": class_name,
        "source_file": source_file,
    }


BUILTIN_SCENARIOS: dict[str, BuiltinScenarioSpec] = {
    "empty_drive": BuiltinScenarioSpec(
        scenario_name="empty_drive",
        display_name="空场景直行",
        module=empty_drive,
        description="ego 使用 Traffic Manager 自动驾驶空场景巡航，不生成 NPC。",
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
        description="ego 先起步，再在前方车道侧向生成横穿干扰体。",
        default_map_name="Town01",
        default_timeout_seconds=25,
        default_fixed_delta_seconds=0.05,
        weather_preset="WetNoon",
    ),
    "free_ride": BuiltinScenarioSpec(
        scenario_name="free_ride",
        display_name="自由巡航",
        module=empty_drive,
        description="移植自官方 FreeRide，保持 ego 单车巡航，用于验证基础链路和画面显示。",
        default_map_name="Town01",
        default_timeout_seconds=35,
        default_fixed_delta_seconds=0.05,
        weather_preset="ClearNoon",
        source=_official_source("FreeRide", "freeride.py"),
    ),
    "change_lane": BuiltinScenarioSpec(
        scenario_name="change_lane",
        display_name="变道回归",
        module=follow_lane,
        description="移植自官方 ChangeLane，使用多车流量验证车道保持与相邻车流干扰。",
        default_map_name="Town01",
        default_timeout_seconds=40,
        default_fixed_delta_seconds=0.05,
        weather_preset="CloudyNoon",
        traffic_enabled=True,
        num_vehicles=14,
        source=_official_source("ChangeLane", "change_lane.py"),
    ),
    "follow_leading_vehicle": BuiltinScenarioSpec(
        scenario_name="follow_leading_vehicle",
        display_name="跟车评测",
        module=follow_lane,
        description="移植自官方 FollowLeadingVehicle，保留前向车流压测，用于验证跟车稳定性。",
        default_map_name="Town01",
        default_timeout_seconds=40,
        default_fixed_delta_seconds=0.05,
        weather_preset="ClearNoon",
        traffic_enabled=True,
        num_vehicles=10,
        source=_official_source(
            "FollowLeadingVehicle", "follow_leading_vehicle.py"
        ),
    ),
    "cut_in": BuiltinScenarioSpec(
        scenario_name="cut_in",
        display_name="加塞干扰",
        module=follow_lane,
        description="移植自官方 CutIn，使用更密集车流制造并线干扰，用于观察吞吐和异常率。",
        default_map_name="Town01",
        default_timeout_seconds=35,
        default_fixed_delta_seconds=0.05,
        weather_preset="ClearNoon",
        traffic_enabled=True,
        num_vehicles=16,
        source=_official_source("CutIn", "cut_in.py"),
    ),
    "parking_cut_in": BuiltinScenarioSpec(
        scenario_name="parking_cut_in",
        display_name="泊车切入",
        module=follow_lane,
        description="移植自官方 ParkingCutIn，模拟侧方车辆并入主车道的干扰场景。",
        default_map_name="Town01",
        default_timeout_seconds=35,
        default_fixed_delta_seconds=0.05,
        weather_preset="WetNoon",
        traffic_enabled=True,
        num_vehicles=12,
        source=_official_source("ParkingCutIn", "parking_cut_in.py"),
    ),
    "blocked_intersection": BuiltinScenarioSpec(
        scenario_name="blocked_intersection",
        display_name="路口阻塞",
        module=npc_crossing,
        description="移植自官方 BlockedIntersection，在 ego 前方注入阻塞目标，适合验证停止与绕行前处理。",
        default_map_name="Town01",
        default_timeout_seconds=30,
        default_fixed_delta_seconds=0.05,
        weather_preset="CloudyNoon",
        traffic_enabled=True,
        num_vehicles=6,
        source=_official_source(
            "BlockedIntersection", "blocked_intersection.py"
        ),
    ),
    "construction_obstacle": BuiltinScenarioSpec(
        scenario_name="construction_obstacle",
        display_name="施工障碍",
        module=npc_crossing,
        description="移植自官方 ConstructionObstacle，在 ego 前方生成障碍干扰，用于验证减速和告警表现。",
        default_map_name="Town01",
        default_timeout_seconds=30,
        default_fixed_delta_seconds=0.05,
        weather_preset="WetNoon",
        source=_official_source(
            "ConstructionObstacle", "construction_crash_vehicle.py"
        ),
    ),
    "pedestrian_crossing": BuiltinScenarioSpec(
        scenario_name="pedestrian_crossing",
        display_name="行人横穿",
        module=npc_crossing,
        description="移植自官方 PedestrianCrossing，在前向道路注入横穿行人干扰。",
        default_map_name="Town01",
        default_timeout_seconds=30,
        default_fixed_delta_seconds=0.05,
        weather_preset="ClearSunset",
        source=_official_source(
            "PedestrianCrossing", "pedestrian_crossing.py"
        ),
    ),
    "parked_obstacle": BuiltinScenarioSpec(
        scenario_name="parked_obstacle",
        display_name="静态障碍",
        module=npc_crossing,
        description="移植自官方 ParkedObstacle，在主车道前方放置静态障碍，用于观察通过率与异常触发。",
        default_map_name="Town01",
        default_timeout_seconds=30,
        default_fixed_delta_seconds=0.05,
        weather_preset="HardRainNoon",
        source=_official_source("ParkedObstacle", "route_obstacles.py"),
    ),
    "junction_right_turn": BuiltinScenarioSpec(
        scenario_name="junction_right_turn",
        display_name="路口右转",
        module=follow_lane,
        description="移植自官方 JunctionRightTurn，使用交叉车流验证转向路口通过稳定性。",
        default_map_name="Town01",
        default_timeout_seconds=40,
        default_fixed_delta_seconds=0.05,
        weather_preset="ClearSunset",
        traffic_enabled=True,
        num_vehicles=12,
        source=_official_source(
            "JunctionRightTurn", "signalized_junction_right_turn.py"
        ),
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
        "debug": {"viewer_friendly": False},
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
                "source": spec.source,
                "descriptor_template": _descriptor_template_from_spec(spec),
            }
        )
    return results


def get_builtin_scenario_module(scenario_name: str) -> Any:
    if scenario_name not in BUILTIN_SCENARIOS:
        raise KeyError(f"Unknown builtin scenario: {scenario_name}")
    return BUILTIN_SCENARIOS[scenario_name].module
