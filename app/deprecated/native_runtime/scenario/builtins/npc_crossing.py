from __future__ import annotations

from app.scenario.runtime import ScenarioRuntimeContext


def setup(context: ScenarioRuntimeContext) -> None:
    spec = context.state.get("scenario_spec")
    descriptor_traffic = getattr(context.descriptor, "traffic", None)
    context.carla_client.set_vehicle_autopilot(context.ego_vehicle, enabled=True)
    context.state["ego_control_mode"] = "autopilot"
    context.state["blocker_spawned"] = False
    context.state["blocker_spawn_tick"] = int(
        getattr(spec, "event_trigger_tick", 20)
    )
    context.state["event_actor_kind"] = (
        getattr(spec, "event_actor_kind", None) or "walker"
    )
    context.state["event_distance_m"] = float(
        getattr(spec, "event_distance_m", 18.0)
    )
    context.state["event_lateral_offset_m"] = float(
        getattr(spec, "event_lateral_offset_m", 2.8)
    )
    traffic_enabled = bool(
        getattr(spec, "traffic_enabled", getattr(descriptor_traffic, "enabled", False))
    )
    num_vehicles = int(
        getattr(spec, "num_vehicles", getattr(descriptor_traffic, "num_vehicles", 0))
    )
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
    if context.state.get("blocker_spawned"):
        return

    if tick_count < int(context.state.get("blocker_spawn_tick", 20)):
        return

    if hasattr(context.carla_client, "spawn_event_actor_ahead"):
        blocker = context.carla_client.spawn_event_actor_ahead(
            context.ego_vehicle,
            actor_kind=str(context.state.get("event_actor_kind", "walker")),
            distance_m=float(context.state.get("event_distance_m", 18.0)),
            lateral_offset_m=float(context.state.get("event_lateral_offset_m", 2.8)),
            role_name=f"{getattr(context.descriptor, 'scenario_name', 'scenario')}_event_actor",
        )
    else:
        blocker = context.carla_client.spawn_crossing_actor_ahead(context.ego_vehicle)
    if blocker is not None:
        context.npc_vehicles.append(blocker)
    context.state["blocker_spawned"] = True


def teardown(context: ScenarioRuntimeContext) -> None:
    return
