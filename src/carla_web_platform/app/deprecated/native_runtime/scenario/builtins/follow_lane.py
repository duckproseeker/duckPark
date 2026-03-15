from __future__ import annotations

from app.scenario.runtime import ScenarioRuntimeContext


def setup(context: ScenarioRuntimeContext) -> None:
    spec = context.state.get("scenario_spec")
    descriptor_traffic = getattr(context.descriptor, "traffic", None)
    traffic_enabled = bool(
        getattr(spec, "traffic_enabled", getattr(descriptor_traffic, "enabled", False))
    )
    num_vehicles = int(
        getattr(spec, "num_vehicles", getattr(descriptor_traffic, "num_vehicles", 0))
    )
    context.carla_client.set_vehicle_autopilot(context.ego_vehicle, enabled=True)
    context.state["ego_control_mode"] = "autopilot"
    if traffic_enabled and num_vehicles > 0:
        context.npc_vehicles.extend(
            context.carla_client.spawn_fixed_traffic_vehicles(
                count=num_vehicles,
                anchor_spawn_point=context.descriptor.ego_vehicle.spawn_point.model_dump(
                    mode="python"
                ),
                autopilot=True,
            )
        )


def on_tick(context: ScenarioRuntimeContext, tick_count: int, sim_time: float) -> None:
    return


def teardown(context: ScenarioRuntimeContext) -> None:
    return
