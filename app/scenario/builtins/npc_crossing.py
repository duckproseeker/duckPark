from __future__ import annotations

from app.scenario.runtime import ScenarioRuntimeContext


def setup(context: ScenarioRuntimeContext) -> None:
    context.carla_client.set_vehicle_autopilot(context.ego_vehicle, enabled=True)
    context.state["ego_control_mode"] = "autopilot"
    context.state["blocker_spawned"] = False
    context.state["blocker_spawn_tick"] = 20


def on_tick(context: ScenarioRuntimeContext, tick_count: int, sim_time: float) -> None:
    if context.state.get("blocker_spawned"):
        return

    if tick_count < int(context.state.get("blocker_spawn_tick", 20)):
        return

    blocker = context.carla_client.spawn_crossing_actor_ahead(context.ego_vehicle)
    if blocker is not None:
        context.npc_vehicles.append(blocker)
    context.state["blocker_spawned"] = True


def teardown(context: ScenarioRuntimeContext) -> None:
    return
