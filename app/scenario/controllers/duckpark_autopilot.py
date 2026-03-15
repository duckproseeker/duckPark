from __future__ import annotations

from typing import Any

from agents.navigation.basic_agent import BasicAgent
from srunner.scenariomanager.actorcontrols.basic_control import BasicControl


class DuckparkAutopilot(BasicControl):
    """Platform default hero controller backed by CARLA's BasicAgent."""

    def __init__(self, actor: Any, args: dict[str, Any] | None = None):
        super().__init__(actor)
        raw_args = args or {}
        self._target_speed_mps = self._coerce_float(
            raw_args.get("target_speed_mps"),
            fallback=10.0,
        )
        self._agent = BasicAgent(
            actor,
            target_speed=self._target_speed_mps * 3.6,
            opt_dict={
                "ignore_stop_signs": False,
                "ignore_traffic_lights": False,
                "ignore_vehicles": False,
            },
        )

    def update_target_speed(self, speed: float) -> None:
        super().update_target_speed(speed)
        self._target_speed_mps = self._coerce_float(speed, fallback=self._target_speed_mps)
        self._agent.set_target_speed(self._target_speed_mps * 3.6)

    def reset(self) -> None:
        if self._actor is None or not getattr(self._actor, "is_alive", False):
            return
        try:
            control = self._actor.get_control()
            control.throttle = 0.0
            control.brake = 1.0
            control.hand_brake = False
            self._actor.apply_control(control)
        except RuntimeError:
            return

    def run_step(self) -> None:
        if self._actor is None or not getattr(self._actor, "is_alive", False):
            return

        if self._agent.done():
            # Re-arm a short roaming destination so the ego keeps driving instead of stopping.
            self._agent.set_destination(self._pick_forward_destination())

        control = self._agent.run_step()
        control.manual_gear_shift = False
        self._actor.apply_control(control)

    def _pick_forward_destination(self) -> Any:
        world = self._actor.get_world()
        current_waypoint = world.get_map().get_waypoint(
            self._actor.get_location(),
            project_to_road=True,
        )
        if current_waypoint is None:
            return self._actor.get_location()

        waypoint = current_waypoint
        for _ in range(30):
            next_waypoints = waypoint.next(2.0)
            if not next_waypoints:
                break
            waypoint = next_waypoints[0]
        return waypoint.transform.location

    @staticmethod
    def _coerce_float(value: Any, *, fallback: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback
