from __future__ import annotations

import math

from app.executor.carla_client import CarlaClient


class FakeLocation:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z

    def distance(self, other: "FakeLocation") -> float:
        return math.sqrt(
            (self.x - other.x) ** 2
            + (self.y - other.y) ** 2
            + (self.z - other.z) ** 2
        )

    def __add__(self, other: "FakeLocation") -> "FakeLocation":
        return FakeLocation(self.x + other.x, self.y + other.y, self.z + other.z)


class FakeRotation:
    def __init__(self, roll: float = 0.0, pitch: float = 0.0, yaw: float = 0.0) -> None:
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw


class FakeVector:
    def __init__(self, x: float, y: float, z: float = 0.0) -> None:
        self.x = x
        self.y = y
        self.z = z


class FakeTransform:
    def __init__(self, location: FakeLocation, rotation: FakeRotation) -> None:
        self.location = location
        self.rotation = rotation

    def get_forward_vector(self) -> FakeVector:
        yaw_radians = math.radians(self.rotation.yaw)
        return FakeVector(math.cos(yaw_radians), math.sin(yaw_radians), 0.0)


class FakeWaypoint:
    def __init__(self, transform: FakeTransform) -> None:
        self.transform = transform

    def next(self, distance_m: float) -> list["FakeWaypoint"]:
        forward = self.transform.get_forward_vector()
        next_location = FakeLocation(
            self.transform.location.x + forward.x * distance_m,
            self.transform.location.y + forward.y * distance_m,
            self.transform.location.z,
        )
        return [FakeWaypoint(FakeTransform(next_location, self.transform.rotation))]


class FakeLaneType:
    Driving = "Driving"


class FakeCarlaModule:
    Location = FakeLocation
    Rotation = FakeRotation
    Transform = FakeTransform
    LaneType = FakeLaneType


class FakeBlueprint:
    def __init__(self, blueprint_id: str) -> None:
        self.id = blueprint_id
        self.attributes: dict[str, str] = {}

    def has_attribute(self, name: str) -> bool:
        return name == "role_name"

    def set_attribute(self, name: str, value: str) -> None:
        self.attributes[name] = value


class FakeBlueprintLibrary:
    def find(self, blueprint_id: str) -> FakeBlueprint:
        return FakeBlueprint(blueprint_id)

    def filter(self, pattern: str) -> list[FakeBlueprint]:
        return [FakeBlueprint(pattern)]


class FakeActor:
    _next_id = 1

    def __init__(self, transform: FakeTransform) -> None:
        self.id = FakeActor._next_id
        FakeActor._next_id += 1
        self._transform = transform
        self.autopilot_enabled = False

    def set_autopilot(self, enabled: bool, traffic_manager_port: int) -> None:
        self.autopilot_enabled = enabled

    def get_transform(self) -> FakeTransform:
        return self._transform


class FakeMap:
    def __init__(self, projected_waypoint: FakeWaypoint, spawn_points: list[FakeTransform]) -> None:
        self._projected_waypoint = projected_waypoint
        self._spawn_points = spawn_points

    def get_waypoint(
        self,
        location: FakeLocation,
        project_to_road: bool = True,
        lane_type: str | None = None,
    ) -> FakeWaypoint:
        return self._projected_waypoint

    def get_spawn_points(self) -> list[FakeTransform]:
        return list(self._spawn_points)


class FakeWorld:
    def __init__(
        self,
        fake_map: FakeMap,
        blocked_locations: set[tuple[float, float, float]] | None = None,
    ) -> None:
        self._map = fake_map
        self._blueprint_library = FakeBlueprintLibrary()
        self._blocked_locations = blocked_locations or set()

    def get_map(self) -> FakeMap:
        return self._map

    def get_blueprint_library(self) -> FakeBlueprintLibrary:
        return self._blueprint_library

    def try_spawn_actor(self, blueprint: FakeBlueprint, transform: FakeTransform) -> FakeActor | None:
        location_key = (
            round(transform.location.x, 3),
            round(transform.location.y, 3),
            round(transform.location.z, 3),
        )
        if location_key in self._blocked_locations:
            return None
        return FakeActor(transform)


def build_client(
    projected_transform: FakeTransform,
    spawn_points: list[FakeTransform],
    blocked_locations: set[tuple[float, float, float]] | None = None,
) -> CarlaClient:
    client = CarlaClient("127.0.0.1", 2000, 10.0, 8010)
    client._carla = FakeCarlaModule()
    client._world = FakeWorld(
        fake_map=FakeMap(FakeWaypoint(projected_transform), spawn_points),
        blocked_locations=blocked_locations,
    )
    return client


def test_spawn_ego_vehicle_prefers_projected_driving_lane_when_nearby() -> None:
    projected_transform = FakeTransform(
        FakeLocation(10.0, 20.0, 0.2),
        FakeRotation(yaw=90.0),
    )
    fallback_spawn = FakeTransform(
        FakeLocation(100.0, 100.0, 0.5),
        FakeRotation(yaw=0.0),
    )
    client = build_client(projected_transform, [fallback_spawn])

    result = client.spawn_ego_vehicle(
        "vehicle.tesla.model3",
        {"x": 10.2, "y": 20.1, "z": 0.5, "roll": 0.0, "pitch": 0.0, "yaw": 0.0},
    )

    assert result.source == "projected_to_driving_lane"
    assert result.resolved_spawn_point["x"] == 10.0
    assert result.resolved_spawn_point["y"] == 20.0
    assert result.distance_to_requested_m is not None
    assert result.distance_to_requested_m < 1.0


def test_spawn_ego_vehicle_falls_back_to_map_spawn_when_requested_point_is_far() -> None:
    projected_transform = FakeTransform(
        FakeLocation(0.0, 0.0, 0.2),
        FakeRotation(yaw=0.0),
    )
    preferred_fallback = FakeTransform(
        FakeLocation(50.0, 60.0, 0.5),
        FakeRotation(yaw=180.0),
    )
    secondary_fallback = FakeTransform(
        FakeLocation(150.0, 160.0, 0.5),
        FakeRotation(yaw=0.0),
    )
    client = build_client(projected_transform, [preferred_fallback, secondary_fallback])

    result = client.spawn_ego_vehicle(
        "vehicle.tesla.model3",
        {"x": 500.0, "y": 500.0, "z": 0.5, "roll": 0.0, "pitch": 0.0, "yaw": 0.0},
    )

    assert result.source == "map_spawn_point_fallback"
    assert result.fallback_index == 0
    assert result.resolved_spawn_point["x"] == 150.0


def test_spawn_ego_vehicle_tries_next_fallback_when_first_spawn_point_is_blocked() -> None:
    projected_transform = FakeTransform(
        FakeLocation(0.0, 0.0, 0.2),
        FakeRotation(yaw=0.0),
    )
    blocked_spawn = FakeTransform(
        FakeLocation(20.0, 20.0, 0.5),
        FakeRotation(yaw=0.0),
    )
    available_spawn = FakeTransform(
        FakeLocation(25.0, 20.0, 0.5),
        FakeRotation(yaw=0.0),
    )
    blocked_locations = {(20.0, 20.0, 0.5)}
    client = build_client(
        projected_transform,
        [blocked_spawn, available_spawn],
        blocked_locations=blocked_locations,
    )

    result = client.spawn_ego_vehicle(
        "vehicle.tesla.model3",
        {"x": 400.0, "y": 400.0, "z": 0.5, "roll": 0.0, "pitch": 0.0, "yaw": 0.0},
    )

    assert result.source == "map_spawn_point_fallback"
    assert result.resolved_spawn_point["x"] == 25.0
