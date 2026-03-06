from __future__ import annotations

from app.scenario.registry import get_builtin_scenario_module
from app.scenario.runtime import ScenarioRuntimeContext


class ScenarioAdapter:
    def setup(self, context: ScenarioRuntimeContext) -> None:
        module = get_builtin_scenario_module(context.descriptor.scenario_name)
        module.setup(context)

    def on_tick(
        self, context: ScenarioRuntimeContext, tick_count: int, sim_time: float
    ) -> None:
        module = get_builtin_scenario_module(context.descriptor.scenario_name)
        module.on_tick(context, tick_count, sim_time)

    def teardown(self, context: ScenarioRuntimeContext) -> None:
        module = get_builtin_scenario_module(context.descriptor.scenario_name)
        module.teardown(context)
