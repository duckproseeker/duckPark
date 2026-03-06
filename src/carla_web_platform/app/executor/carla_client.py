from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CarlaTickResult:
    frame: int
    sim_time: float


class CarlaClientError(RuntimeError):
    """CARLA client wrapper error."""


class CarlaClient:
    """Thin wrapper around CARLA Python API.

    The executor keeps exclusive world tick authority and uses this class only
    from the execution thread/process.
    """

    def __init__(
        self, host: str, port: int, timeout_seconds: float, traffic_manager_port: int
    ) -> None:
        self._host = host
        self._port = port
        self._timeout_seconds = timeout_seconds
        self._traffic_manager_port = traffic_manager_port

        self._carla: Any = None
        self._client: Any = None
        self._world: Any = None
        self._tm: Any = None
        self._original_sync_mode: bool | None = None
        self._original_fixed_delta: float | None = None
        self._spawned_actors: list[Any] = []
        self._tm_sync_enabled = False

    @property
    def spawned_actors(self) -> list[Any]:
        return self._spawned_actors

    def connect(self) -> None:
        try:
            import carla  # type: ignore
        except ImportError as exc:
            raise CarlaClientError(
                "carla Python API not found in executor environment"
            ) from exc

        self._carla = carla
        self._client = carla.Client(self._host, self._port)
        self._client.set_timeout(self._timeout_seconds)
        self._world = self._client.get_world()
        self._tm = self._client.get_trafficmanager(self._traffic_manager_port)

    def load_map(self, map_name: str) -> None:
        if self._client is None:
            raise CarlaClientError("CARLA client is not connected")
        self._world = self._client.load_world(map_name)

    def set_weather(self, preset_name: str) -> None:
        if self._world is None or self._carla is None:
            raise CarlaClientError("CARLA world is not ready")

        weather = getattr(self._carla.WeatherParameters, preset_name, None)
        if weather is None:
            raise CarlaClientError(f"Unsupported weather preset: {preset_name}")
        self._world.set_weather(weather)

    def configure_world_sync(self, enabled: bool, fixed_delta_seconds: float) -> None:
        if self._world is None:
            raise CarlaClientError("CARLA world is not ready")

        settings = self._world.get_settings()
        if self._original_sync_mode is None:
            self._original_sync_mode = bool(settings.synchronous_mode)
        if self._original_fixed_delta is None:
            self._original_fixed_delta = settings.fixed_delta_seconds

        settings.synchronous_mode = enabled
        settings.fixed_delta_seconds = fixed_delta_seconds
        self._world.apply_settings(settings)

    def configure_tm_sync(self, enabled: bool) -> None:
        if self._tm is None:
            raise CarlaClientError("Traffic Manager is not ready")
        self._tm.set_synchronous_mode(enabled)
        self._tm_sync_enabled = enabled

    def _build_transform(self, spawn_point: dict[str, float]) -> Any:
        if self._carla is None:
            raise CarlaClientError("CARLA module is not loaded")
        return self._carla.Transform(
            self._carla.Location(
                x=spawn_point["x"],
                y=spawn_point["y"],
                z=spawn_point["z"],
            ),
            self._carla.Rotation(
                roll=spawn_point.get("roll", 0.0),
                pitch=spawn_point.get("pitch", 0.0),
                yaw=spawn_point.get("yaw", 0.0),
            ),
        )

    def spawn_ego_vehicle(
        self,
        blueprint: str,
        spawn_point: dict[str, float],
        role_name: str = "ego_vehicle",
    ) -> Any:
        if self._world is None:
            raise CarlaClientError("CARLA world is not ready")

        blueprint_library = self._world.get_blueprint_library()
        blueprint_obj = blueprint_library.find(blueprint)
        if blueprint_obj.has_attribute("role_name"):
            blueprint_obj.set_attribute("role_name", role_name)
        transform = self._build_transform(spawn_point)
        actor = self._world.try_spawn_actor(blueprint_obj, transform)
        if actor is None:
            raise CarlaClientError("Failed to spawn ego vehicle")

        self._spawned_actors.append(actor)
        return actor

    def set_vehicle_autopilot(self, vehicle: Any, enabled: bool) -> None:
        if vehicle is None:
            return
        vehicle.set_autopilot(enabled, self._traffic_manager_port)

    def spawn_traffic_vehicles(self, count: int, autopilot: bool = True) -> list[Any]:
        if self._world is None:
            raise CarlaClientError("CARLA world is not ready")

        blueprint_library = self._world.get_blueprint_library().filter("vehicle.*")
        spawn_points = list(self._world.get_map().get_spawn_points())
        random.shuffle(spawn_points)

        spawned: list[Any] = []
        for spawn_point in spawn_points:
            if len(spawned) >= count:
                break
            blueprint_obj = random.choice(blueprint_library)
            actor = self._world.try_spawn_actor(blueprint_obj, spawn_point)
            if actor is None:
                continue
            actor.set_autopilot(autopilot, self._traffic_manager_port)
            self._spawned_actors.append(actor)
            spawned.append(actor)

        return spawned

    def spawn_crossing_actor_ahead(self, ego_vehicle: Any) -> Any | None:
        if self._world is None or self._carla is None:
            raise CarlaClientError("CARLA world is not ready")

        ego_transform = ego_vehicle.get_transform()
        forward = ego_transform.get_forward_vector()
        blocker_location = ego_transform.location + self._carla.Location(
            x=forward.x * 20.0,
            y=forward.y * 20.0,
            z=0.0,
        )
        blocker_rotation = self._carla.Rotation(
            pitch=0.0,
            yaw=ego_transform.rotation.yaw + 90.0,
            roll=0.0,
        )
        blocker_transform = self._carla.Transform(blocker_location, blocker_rotation)

        blueprints = self._world.get_blueprint_library().filter("walker.pedestrian.*")
        if not blueprints:
            blueprints = self._world.get_blueprint_library().filter("vehicle.*")
        if not blueprints:
            return None

        actor = self._world.try_spawn_actor(
            random.choice(blueprints), blocker_transform
        )
        if actor is not None:
            self._spawned_actors.append(actor)
        return actor

    def tick(self) -> CarlaTickResult:
        if self._world is None:
            raise CarlaClientError("CARLA world is not ready")

        frame = self._world.tick()
        snapshot = self._world.get_snapshot()
        sim_time = float(snapshot.timestamp.elapsed_seconds)
        return CarlaTickResult(frame=frame, sim_time=sim_time)

    def start_recorder(self, recorder_path: Path) -> None:
        if self._client is None:
            raise CarlaClientError("CARLA client is not connected")
        self._client.start_recorder(str(recorder_path))

    def stop_recorder(self) -> None:
        if self._client is None:
            return
        self._client.stop_recorder()

    def cleanup(self) -> None:
        self._destroy_spawned_actors()
        self._restore_world_settings()

    def _destroy_spawned_actors(self) -> None:
        if not self._spawned_actors:
            return
        if self._client is None or self._carla is None:
            return

        commands = [
            self._carla.command.DestroyActor(actor.id) for actor in self._spawned_actors
        ]
        self._client.apply_batch(commands)
        self._spawned_actors.clear()

    def _restore_world_settings(self) -> None:
        if self._world is None:
            return

        settings = self._world.get_settings()
        if self._original_sync_mode is not None:
            settings.synchronous_mode = self._original_sync_mode
        if self._original_fixed_delta is not None:
            settings.fixed_delta_seconds = self._original_fixed_delta
        self._world.apply_settings(settings)

        if self._tm is not None and self._tm_sync_enabled:
            self._tm.set_synchronous_mode(False)

    def spawned_actor_count(self) -> int:
        return len(self._spawned_actors)
