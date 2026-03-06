from __future__ import annotations

import pytest

from app.scenario.validators import validate_descriptor


VALID_DESCRIPTOR = {
    "version": 1,
    "scenario_name": "empty_drive",
    "map_name": "Town01",
    "weather": {"preset": "ClearNoon"},
    "sync": {"enabled": True, "fixed_delta_seconds": 0.05},
    "ego_vehicle": {
        "blueprint": "vehicle.tesla.model3",
        "spawn_point": {
            "x": 230.0,
            "y": 195.0,
            "z": 0.5,
            "roll": 0.0,
            "pitch": 0.0,
            "yaw": 90.0,
        },
    },
    "traffic": {"enabled": False, "num_vehicles": 0, "num_walkers": 0},
    "sensors": {"enabled": False},
    "termination": {"timeout_seconds": 10, "success_condition": "timeout"},
    "recorder": {"enabled": False},
    "metadata": {"author": "test", "tags": ["unit"], "description": "descriptor test"},
}


def test_descriptor_validation_success() -> None:
    descriptor = validate_descriptor(VALID_DESCRIPTOR)
    assert descriptor.scenario_name == "empty_drive"
    assert descriptor.sync.fixed_delta_seconds == 0.05


def test_descriptor_validation_failure() -> None:
    bad_payload = {**VALID_DESCRIPTOR, "termination": {"timeout_seconds": 0, "success_condition": "timeout"}}
    with pytest.raises(Exception):
        validate_descriptor(bad_payload)
