from __future__ import annotations

from app.scenario.runtime import ScenarioRuntimeContext


def setup(context: ScenarioRuntimeContext) -> None:
    # Empty drive keeps default setup only.
    return


def on_tick(context: ScenarioRuntimeContext, tick_count: int, sim_time: float) -> None:
    return


def teardown(context: ScenarioRuntimeContext) -> None:
    return
