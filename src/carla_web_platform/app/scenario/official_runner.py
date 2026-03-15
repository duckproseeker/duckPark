from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class OfficialOpenScenarioPreset:
    scenario_id: str
    display_name: str
    relative_xosc_path: str
    description: str


OFFICIAL_OPENSCENARIO_PRESETS: tuple[OfficialOpenScenarioPreset, ...] = (
    OfficialOpenScenarioPreset(
        scenario_id="osc_follow_leading_vehicle",
        display_name="官方 OpenSCENARIO / 跟车",
        relative_xosc_path="srunner/examples/FollowLeadingVehicle.xosc",
        description="官方 OpenSCENARIO 示例，主车跟随前车并观察减速停车过程。",
    ),
    OfficialOpenScenarioPreset(
        scenario_id="osc_lane_change_simple",
        display_name="官方 OpenSCENARIO / 简单变道",
        relative_xosc_path="srunner/examples/LaneChangeSimple.xosc",
        description="官方 OpenSCENARIO 示例，验证主车与目标车辆的简单变道交互。",
    ),
    OfficialOpenScenarioPreset(
        scenario_id="osc_sync_arrival_intersection",
        display_name="官方 OpenSCENARIO / 路口同步到达",
        relative_xosc_path="srunner/examples/SyncArrivalIntersection.xosc",
        description="官方 OpenSCENARIO 示例，复现主车与对向车流的同步到达路口交互。",
    ),
    OfficialOpenScenarioPreset(
        scenario_id="osc_intersection_collision_avoidance",
        display_name="官方 OpenSCENARIO / 路口避碰",
        relative_xosc_path="srunner/examples/IntersectionCollisionAvoidance.xosc",
        description="官方 OpenSCENARIO 示例，复现路口冲突与避碰过程。",
    ),
    OfficialOpenScenarioPreset(
        scenario_id="osc_pedestrian_crossing_front",
        display_name="官方 OpenSCENARIO / 前向行人横穿",
        relative_xosc_path="srunner/examples/PedestrianCrossingFront.xosc",
        description="官方 OpenSCENARIO 示例，复现主车前方行人横穿场景。",
    ),
    OfficialOpenScenarioPreset(
        scenario_id="osc_cyclist_crossing",
        display_name="官方 OpenSCENARIO / 骑行者横穿",
        relative_xosc_path="srunner/examples/CyclistCrossing.xosc",
        description="官方 OpenSCENARIO 示例，复现骑行者横穿干扰。",
    ),
    OfficialOpenScenarioPreset(
        scenario_id="osc_slalom",
        display_name="官方 OpenSCENARIO / 绕桩",
        relative_xosc_path="srunner/examples/Slalom.xosc",
        description="官方 OpenSCENARIO 示例，复现固定障碍物绕行。",
    ),
    OfficialOpenScenarioPreset(
        scenario_id="osc_changing_weather",
        display_name="官方 OpenSCENARIO / 天气变化",
        relative_xosc_path="srunner/examples/ChangingWeather.xosc",
        description="官方 OpenSCENARIO 示例，运行过程中由场景脚本驱动天气变化。",
    ),
)


def scenario_runner_ready(settings: Settings | None = None) -> bool:
    return not scenario_runner_runtime_issues(settings)


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _dedupe_paths(entries: list[Path]) -> list[str]:
    unique_entries: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        normalized = str(entry)
        if normalized in seen or not entry.exists():
            continue
        seen.add(normalized)
        unique_entries.append(normalized)
    return unique_entries


def _carla_pythonpath_entries(carla_root: Path) -> list[Path]:
    flat_agents_root = carla_root / "agents"
    pythonapi_root = carla_root / "PythonAPI"
    carla_python_root = pythonapi_root / "carla"
    dist_root = carla_python_root / "dist"
    egg_candidates = sorted(dist_root.glob("carla-*.egg")) if dist_root.exists() else []
    entries: list[Path] = [*egg_candidates]
    if carla_python_root.exists():
        entries.append(carla_python_root)
    if flat_agents_root.exists():
        entries.append(carla_root)
    return entries


def scenario_runner_runtime_issues(settings: Settings | None = None) -> list[str]:
    settings = settings or get_settings()
    issues: list[str] = []

    root = settings.scenario_runner_root
    if root is None:
        issues.append("缺少 SCENARIO_RUNNER_ROOT")
    elif not (root / "scenario_runner.py").exists():
        issues.append(f"找不到 scenario_runner.py: {root / 'scenario_runner.py'}")

    carla_root = settings.scenario_runner_carla_root
    if carla_root is None:
        issues.append("缺少 SCENARIO_RUNNER_CARLA_ROOT")
        return issues

    flat_agents_root = carla_root / "agents"
    carla_python_root = carla_root / "PythonAPI" / "carla"
    agents_root = carla_python_root / "agents"
    dist_root = carla_python_root / "dist"
    egg_candidates = sorted(dist_root.glob("carla-*.egg")) if dist_root.exists() else []

    if not agents_root.exists() and not flat_agents_root.exists() and not _module_available("agents"):
        issues.append(
            "找不到 agents 包目录: "
            f"{agents_root} 或 {flat_agents_root}"
        )

    if not egg_candidates and not _module_available("carla"):
        issues.append(
            "未找到 CARLA Python API。请确认已安装 carla 包，或"
            f" {dist_root} 下存在 carla-*.egg"
        )

    return issues


def build_scenario_runner_pythonpath(settings: Settings | None = None) -> list[str]:
    settings = settings or get_settings()
    entries: list[Path] = []
    if settings.scenario_runner_root is not None:
        entries.append(settings.scenario_runner_root)
        srunner_package_root = settings.scenario_runner_root / "srunner"
        if srunner_package_root.exists():
            entries.append(srunner_package_root)
    if settings.scenario_runner_carla_root is not None:
        entries.extend(_carla_pythonpath_entries(settings.scenario_runner_carla_root))
    return _dedupe_paths(entries)


def resolve_official_xosc_path(
    relative_xosc_path: str, settings: Settings | None = None
) -> Path | None:
    settings = settings or get_settings()
    if settings.scenario_runner_root is None:
        return None
    candidate = settings.scenario_runner_root / relative_xosc_path
    return candidate if candidate.exists() else None


def official_preset_index() -> dict[str, OfficialOpenScenarioPreset]:
    return {item.scenario_id: item for item in OFFICIAL_OPENSCENARIO_PRESETS}


def _safe_parse_xosc(xosc_path: Path) -> ElementTree.Element | None:
    try:
        return ElementTree.parse(xosc_path).getroot()
    except ElementTree.ParseError:
        return None


def _extract_map_name(root: ElementTree.Element | None) -> str:
    if root is None:
        return "Town01"
    logic_file = root.find("./RoadNetwork/LogicFile")
    filepath = logic_file.attrib.get("filepath", "").strip() if logic_file is not None else ""
    return filepath or "Town01"


def _extract_parameter_declarations(
    root: ElementTree.Element | None,
) -> list[dict[str, str]]:
    if root is None:
        return []

    declarations: list[dict[str, str]] = []
    for item in root.findall("./ParameterDeclarations/ParameterDeclaration"):
        name = item.attrib.get("name", "").strip()
        if not name:
            continue
        declarations.append(
            {
                "name": name,
                "parameter_type": item.attrib.get("parameterType", "").strip(),
                "default_value": item.attrib.get("value", "").strip(),
            }
        )
    return declarations


def _extract_actor_summary(root: ElementTree.Element | None) -> str:
    if root is None:
        return "Actors are defined inside the official OpenSCENARIO file."

    parts: list[str] = []
    for scenario_object in root.findall("./Entities/ScenarioObject"):
        name = scenario_object.attrib.get("name", "").strip() or "actor"
        actor_kind = "actor"
        for child in list(scenario_object):
            if child.tag in {"Vehicle", "Pedestrian", "MiscObject", "CatalogReference"}:
                actor_kind = child.tag.lower()
                break
        parts.append(f"{name} ({actor_kind})")
    return ", ".join(parts) if parts else "Actors are defined inside the official OpenSCENARIO file."


def _extract_event_summary(root: ElementTree.Element | None) -> str:
    if root is None:
        return "Event flow follows the official OpenSCENARIO storyboard."

    event_names = [
        item.attrib.get("name", "").strip()
        for item in root.findall(".//Event")
        if item.attrib.get("name", "").strip()
    ]
    if not event_names:
        return "Event flow follows the official OpenSCENARIO storyboard."
    preview = ", ".join(event_names[:3])
    if len(event_names) > 3:
        preview = f"{preview} ..."
    return preview


def build_official_openscenario_catalog_item(
    preset: OfficialOpenScenarioPreset, settings: Settings | None = None
) -> dict[str, Any]:
    settings = settings or get_settings()
    xosc_path = resolve_official_xosc_path(preset.relative_xosc_path, settings)
    root = _safe_parse_xosc(xosc_path) if xosc_path is not None else None
    map_name = _extract_map_name(root)
    parameter_declarations = _extract_parameter_declarations(root)

    return {
        "scenario_id": preset.scenario_id,
        "scenario_name": preset.scenario_id,
        "display_name": preset.display_name,
        "description": preset.description,
        "default_map_name": map_name,
        "execution_support": "scenario_runner",
        "execution_backend": "scenario_runner",
        "source": {
            "provider": "scenario_runner",
            "version": "external",
            "relative_xosc_path": preset.relative_xosc_path,
            "resolved_xosc_path": str(xosc_path) if xosc_path is not None else None,
        },
        "preset": {
            "locked_map_name": map_name,
            "map_locked": True,
            "event_locked": True,
            "actors_locked": True,
            "weather_runtime_editable": False,
            "event_summary": _extract_event_summary(root),
            "actors_summary": _extract_actor_summary(root),
        },
        "parameter_declarations": parameter_declarations,
        "descriptor_template": {
            "version": 1,
            "scenario_name": preset.scenario_id,
            "map_name": map_name,
            "weather": {"preset": "ScenarioRunnerManaged"},
            "sync": {"enabled": True, "fixed_delta_seconds": 0.05},
            "ego_vehicle": {
                "blueprint": "vehicle.lincoln.mkz_2017",
                "spawn_point": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "roll": 0.0,
                    "pitch": 0.0,
                    "yaw": 0.0,
                },
            },
            "traffic": {"enabled": False, "num_vehicles": 0, "num_walkers": 0},
            "sensors": {"enabled": False, "sensors": []},
            "termination": {"timeout_seconds": 120, "success_condition": "scenario_runner"},
            "recorder": {"enabled": False},
            "debug": {"viewer_friendly": False},
            "metadata": {
                "author": "scenario-runner",
                "tags": ["scenario_runner", preset.scenario_id],
                "description": preset.description,
            },
        },
    }


def list_official_openscenario_catalog(settings: Settings | None = None) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    return [
        build_official_openscenario_catalog_item(item, settings)
        for item in OFFICIAL_OPENSCENARIO_PRESETS
    ]
