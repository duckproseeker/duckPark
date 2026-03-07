from __future__ import annotations

from app.scenario.runtime import ScenarioRuntimeContext


def setup(context: ScenarioRuntimeContext) -> None:
    context.carla_client.set_vehicle_autopilot(context.ego_vehicle, enabled=True)
    context.state["ego_control_mode"] = "autopilot"


def on_tick(context: ScenarioRuntimeContext, tick_count: int, sim_time: float) -> None:
    return


def teardown(context: ScenarioRuntimeContext) -> None:
    return
