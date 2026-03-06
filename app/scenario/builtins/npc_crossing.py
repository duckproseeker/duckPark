from __future__ import annotations

from app.scenario.runtime import ScenarioRuntimeContext


def setup(context: ScenarioRuntimeContext) -> None:
    blocker = context.carla_client.spawn_crossing_actor_ahead(context.ego_vehicle)
    if blocker is not None:
        context.npc_vehicles.append(blocker)


def on_tick(context: ScenarioRuntimeContext, tick_count: int, sim_time: float) -> None:
    return


def teardown(context: ScenarioRuntimeContext) -> None:
    return
