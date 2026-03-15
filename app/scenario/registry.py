"""Deprecated compatibility shim for the retired builtin scenario registry."""

from app.deprecated.native_runtime.scenario.registry import (
    BUILTIN_SCENARIOS,
    BuiltinScenarioSpec,
    get_builtin_scenario_module,
    get_builtin_scenario_spec,
    list_builtin_scenarios,
)

__all__ = [
    "BUILTIN_SCENARIOS",
    "BuiltinScenarioSpec",
    "get_builtin_scenario_module",
    "get_builtin_scenario_spec",
    "list_builtin_scenarios",
]
