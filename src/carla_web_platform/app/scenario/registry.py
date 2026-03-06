from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.scenario.builtins import empty_drive, follow_lane, npc_crossing


@dataclass(frozen=True)
class BuiltinScenarioSpec:
    scenario_name: str
    module: Any
    description: str


BUILTIN_SCENARIOS: dict[str, BuiltinScenarioSpec] = {
    "empty_drive": BuiltinScenarioSpec(
        scenario_name="empty_drive",
        module=empty_drive,
        description="Spawn ego vehicle, no NPC, run for fixed timeout.",
    ),
    "follow_lane": BuiltinScenarioSpec(
        scenario_name="follow_lane",
        module=follow_lane,
        description="Spawn ego and a few NPC vehicles with lane-follow behavior.",
    ),
    "npc_crossing": BuiltinScenarioSpec(
        scenario_name="npc_crossing",
        module=npc_crossing,
        description="Spawn a crossing disturbance actor ahead of ego.",
    ),
}


def list_builtin_scenarios() -> list[dict[str, str]]:
    return [
        {
            "scenario_name": spec.scenario_name,
            "description": spec.description,
        }
        for spec in BUILTIN_SCENARIOS.values()
    ]


def get_builtin_scenario_module(scenario_name: str) -> Any:
    if scenario_name not in BUILTIN_SCENARIOS:
        raise KeyError(f"Unknown builtin scenario: {scenario_name}")
    return BUILTIN_SCENARIOS[scenario_name].module
