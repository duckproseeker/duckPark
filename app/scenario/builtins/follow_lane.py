from __future__ import annotations

from app.scenario.runtime import ScenarioRuntimeContext


def setup(context: ScenarioRuntimeContext) -> None:
    context.carla_client.set_vehicle_autopilot(context.ego_vehicle, enabled=True)
    if context.descriptor.traffic.enabled and context.descriptor.traffic.num_vehicles > 0:
        context.npc_vehicles.extend(
            context.carla_client.spawn_traffic_vehicles(
                count=context.descriptor.traffic.num_vehicles,
                autopilot=True,
            )
        )


def on_tick(context: ScenarioRuntimeContext, tick_count: int, sim_time: float) -> None:
    return


def teardown(context: ScenarioRuntimeContext) -> None:
    return
