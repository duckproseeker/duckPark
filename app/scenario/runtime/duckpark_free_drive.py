from __future__ import annotations

import time

import py_trees
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import (
    ChangeActorControl,
)
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenarios.basic_scenario import BasicScenario


class WallClockTimeout(py_trees.behaviour.Behaviour):
    def __init__(self, duration_seconds: float, name: str = "WallClockTimeout"):
        super().__init__(name)
        self._duration_seconds = max(0.0, float(duration_seconds))
        self._started_at = 0.0

    def initialise(self):
        self._started_at = time.monotonic()
        super().initialise()

    def update(self):
        if time.monotonic() - self._started_at >= self._duration_seconds:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.RUNNING


class DuckparkFreeDrive(BasicScenario):
    """Free-drive template with the platform autopilot attached to the hero vehicle."""

    def __init__(
        self,
        world,
        ego_vehicles,
        config,
        randomize: bool = False,
        debug_mode: bool = False,
        criteria_enable: bool = True,
        timeout: float = 100000.0,
    ):
        _ = randomize
        params = config.other_parameters.get("duckpark_free_drive", {})
        self.timeout = float(params.get("timeout_seconds") or timeout or 120.0)
        self._controller_module = str(params.get("controller_module") or "").strip()
        self._controller_args = {
            "traffic_manager_port": str(params.get("traffic_manager_port") or "8010"),
            "target_speed_mps": str(params.get("target_speed_mps") or "10.0"),
        }
        super().__init__(
            "DuckparkFreeDrive",
            ego_vehicles,
            config,
            world,
            debug_mode,
            criteria_enable=criteria_enable,
        )

    def _setup_scenario_trigger(self, config):
        _ = config
        return None

    def _create_behavior(self):
        sequence = py_trees.composites.Sequence("DuckparkFreeDrive")
        if self.ego_vehicles and self._controller_module:
            sequence.add_child(
                ChangeActorControl(
                    self.ego_vehicles[0],
                    control_py_module=self._controller_module,
                    args=self._controller_args,
                )
            )
        sequence.add_child(WallClockTimeout(self.timeout))
        return sequence

    def _create_test_criteria(self):
        return [CollisionTest(ego_vehicle) for ego_vehicle in self.ego_vehicles]

    def __del__(self):
        self.remove_all_actors()
