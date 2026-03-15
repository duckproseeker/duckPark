from __future__ import annotations

from app.scenario.builtins import empty_drive, npc_crossing
from app.scenario.runtime import ScenarioRuntimeContext


class FakeCarlaClient:
    def __init__(self) -> None:
        self.autopilot_calls: list[tuple[object, bool]] = []
        self.blocker_calls = 0
        self.blocker = object()

    def set_vehicle_autopilot(self, vehicle: object, enabled: bool) -> None:
        self.autopilot_calls.append((vehicle, enabled))

    def spawn_crossing_actor_ahead(self, ego_vehicle: object) -> object:
        self.blocker_calls += 1
        return self.blocker


class FakeDescriptor:
    traffic = None


def build_context(client: FakeCarlaClient) -> ScenarioRuntimeContext:
    return ScenarioRuntimeContext(
        run_id="run_test",
        descriptor=FakeDescriptor(),
        carla_client=client,
        ego_vehicle=object(),
    )


def test_empty_drive_enables_ego_autopilot() -> None:
    client = FakeCarlaClient()
    context = build_context(client)

    empty_drive.setup(context)

    assert client.autopilot_calls == [(context.ego_vehicle, True)]
    assert context.state["ego_control_mode"] == "autopilot"


def test_npc_crossing_spawns_blocker_once_after_delay() -> None:
    client = FakeCarlaClient()
    context = build_context(client)

    npc_crossing.setup(context)
    npc_crossing.on_tick(context, tick_count=5, sim_time=0.25)
    npc_crossing.on_tick(context, tick_count=19, sim_time=0.95)
    npc_crossing.on_tick(context, tick_count=20, sim_time=1.0)
    npc_crossing.on_tick(context, tick_count=30, sim_time=1.5)

    assert client.autopilot_calls == [(context.ego_vehicle, True)]
    assert client.blocker_calls == 1
    assert context.npc_vehicles == [client.blocker]
    assert context.state["blocker_spawned"] is True
