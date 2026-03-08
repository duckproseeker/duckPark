from __future__ import annotations

import math
import queue
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ViewerView:
    view_id: str
    label: str
    transform: dict[str, float]
    attachment_type: str


VIEWER_VIEWS: tuple[ViewerView, ...] = (
    ViewerView(
        view_id="first_person",
        label="第一视角",
        transform={
            "x": 0.35,
            "y": 0.0,
            "z": 1.25,
            "pitch": 0.0,
            "yaw": 0.0,
            "roll": 0.0,
        },
        attachment_type="rigid",
    ),
    ViewerView(
        view_id="third_person",
        label="第三视角",
        transform={
            "x": -6.0,
            "y": 0.0,
            "z": 2.6,
            "pitch": -12.0,
            "yaw": 0.0,
            "roll": 0.0,
        },
        attachment_type="spring_arm",
    ),
)


class EgoSnapshotViewerError(RuntimeError):
    """Raised when a read-only viewer snapshot cannot be collected."""


class EgoSnapshotViewer:
    """Read-only CARLA snapshot viewer.

    This class follows the same constraint as `scripts/ego_viewer.py`:
    it never calls `world.tick()` and only attaches a temporary camera
    to the already-running ego vehicle.
    """

    def __init__(
        self,
        *,
        host: str,
        port: int,
        timeout_seconds: float,
        width: int = 1280,
        height: int = 720,
        role_names: tuple[str, ...] = ("ego_vehicle", "hero", "ego"),
        preferred_actor_id: int | None = None,
        preferred_spawn_point: dict[str, float] | None = None,
        ego_wait_timeout_seconds: float = 5.0,
        poll_interval_seconds: float = 0.35,
    ) -> None:
        self._host = host
        self._port = port
        self._timeout_seconds = timeout_seconds
        self._width = width
        self._height = height
        self._preferred_actor_id = preferred_actor_id
        self._preferred_spawn_point = preferred_spawn_point
        self._ego_wait_timeout_seconds = ego_wait_timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds
        self._role_names = tuple(
            role_name.strip().lower() for role_name in role_names if role_name.strip()
        )

        self._carla: Any = None
        self._client: Any = None
        self._world: Any = None

    def _connect(self) -> None:
        try:
            import carla  # type: ignore
        except ImportError as exc:
            raise EgoSnapshotViewerError(
                "viewer 依赖 carla Python API，当前 API 进程环境不可用"
            ) from exc

        self._carla = carla
        self._client = carla.Client(self._host, self._port)
        self._client.set_timeout(self._timeout_seconds)
        self._world = self._client.get_world()

    def _refresh_world(self) -> None:
        if self._client is None:
            raise EgoSnapshotViewerError("CARLA client 未连接")
        self._world = self._client.get_world()

    @staticmethod
    def _vehicle_sort_key(vehicle: Any) -> tuple[int, float]:
        velocity = vehicle.get_velocity()
        speed = math.sqrt(
            velocity.x * velocity.x
            + velocity.y * velocity.y
            + velocity.z * velocity.z
        )
        alive = 1 if vehicle.is_alive else 0
        return alive, speed

    @staticmethod
    def _distance_to_spawn(vehicle: Any, spawn_point: dict[str, float]) -> float:
        transform = vehicle.get_transform()
        dx = float(transform.location.x) - float(spawn_point["x"])
        dy = float(transform.location.y) - float(spawn_point["y"])
        dz = float(transform.location.z) - float(spawn_point["z"])
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    @staticmethod
    def _vehicle_preview(vehicles: list[Any], max_items: int = 8) -> str:
        preview = []
        for vehicle in vehicles[:max_items]:
            preview.append(
                f"{vehicle.id}:{vehicle.attributes.get('role_name', '').strip() or '<empty>'}"
            )
        return ", ".join(preview) if preview else "<none>"

    def _find_ego_vehicle_once(self) -> Any | None:
        if self._world is None:
            raise EgoSnapshotViewerError("CARLA world 未连接")

        vehicles = list(self._world.get_actors().filter("vehicle.*"))
        alive_vehicles = [vehicle for vehicle in vehicles if getattr(vehicle, "is_alive", False)]

        if self._preferred_actor_id is not None:
            for vehicle in alive_vehicles:
                if int(vehicle.id) == int(self._preferred_actor_id):
                    return vehicle

        for role_name in self._role_names:
            matches = [
                vehicle
                for vehicle in alive_vehicles
                if vehicle.attributes.get("role_name", "").strip().lower() == role_name
            ]
            if matches:
                matches.sort(key=self._vehicle_sort_key, reverse=True)
                return matches[0]

        if len(alive_vehicles) == 1:
            return alive_vehicles[0]

        if self._preferred_spawn_point and alive_vehicles:
            closest = min(
                alive_vehicles,
                key=lambda vehicle: self._distance_to_spawn(
                    vehicle, self._preferred_spawn_point
                ),
            )
            distance_m = self._distance_to_spawn(closest, self._preferred_spawn_point)
            if distance_m <= 12.0:
                return closest

        return None

    def _wait_for_ego_vehicle(self) -> Any:
        deadline = time.monotonic() + max(0.5, self._ego_wait_timeout_seconds)
        last_preview = "<none>"
        last_count = 0

        while time.monotonic() < deadline:
            self._refresh_world()
            assert self._world is not None
            vehicles = list(self._world.get_actors().filter("vehicle.*"))
            last_count = len(vehicles)
            last_preview = self._vehicle_preview(vehicles)

            ego_vehicle = self._find_ego_vehicle_once()
            if ego_vehicle is not None:
                return ego_vehicle

            time.sleep(self._poll_interval_seconds)

        raise EgoSnapshotViewerError(
            "当前 world 中未找到 ego_vehicle"
            f"（vehicles={last_count}, preview={last_preview}）"
        )

    def _camera_blueprint(self) -> Any:
        if self._world is None:
            raise EgoSnapshotViewerError("CARLA world 未连接")

        bp = self._world.get_blueprint_library().find("sensor.camera.rgb")
        bp.set_attribute("image_size_x", str(self._width))
        bp.set_attribute("image_size_y", str(self._height))
        bp.set_attribute("fov", "100")
        if bp.has_attribute("sensor_tick"):
            bp.set_attribute("sensor_tick", "0.0")
        return bp

    def _viewer_view(self, view_id: str) -> ViewerView:
        for view in VIEWER_VIEWS:
            if view.view_id == view_id:
                return view
        raise EgoSnapshotViewerError(f"未知 viewer 视角: {view_id}")

    def _build_transform(self, view: ViewerView) -> Any:
        assert self._carla is not None
        return self._carla.Transform(
            self._carla.Location(
                x=view.transform["x"],
                y=view.transform["y"],
                z=view.transform["z"],
            ),
            self._carla.Rotation(
                pitch=view.transform["pitch"],
                yaw=view.transform["yaw"],
                roll=view.transform["roll"],
            ),
        )

    def capture_png_bytes(self, *, view_id: str) -> bytes:
        self._connect()
        assert self._world is not None
        assert self._carla is not None

        ego_vehicle = self._wait_for_ego_vehicle()
        viewer_view = self._viewer_view(view_id)
        image_queue: queue.Queue[Any] = queue.Queue(maxsize=1)

        def on_image(image: Any) -> None:
            try:
                if image_queue.full():
                    _ = image_queue.get_nowait()
                image_queue.put_nowait(image)
            except queue.Empty:
                pass
            except queue.Full:
                pass

        sensor = self._world.spawn_actor(
            self._camera_blueprint(),
            self._build_transform(viewer_view),
            attach_to=ego_vehicle,
            attachment_type=(
                self._carla.AttachmentType.SpringArmGhost
                if viewer_view.attachment_type == "spring_arm"
                else self._carla.AttachmentType.Rigid
            ),
        )

        try:
            sensor.listen(on_image)
            try:
                image = image_queue.get(timeout=2.5)
            except queue.Empty as exc:
                raise EgoSnapshotViewerError(
                    "未在超时时间内收到 viewer 帧，请确认 run 正在推进"
                ) from exc

            with tempfile.TemporaryDirectory(prefix="ego-snapshot-") as tmp_dir:
                image_path = Path(tmp_dir) / "frame.png"
                image.save_to_disk(str(image_path))
                return image_path.read_bytes()
        finally:
            try:
                sensor.stop()
            except Exception:
                pass
            try:
                sensor.destroy()
            except Exception:
                pass


def list_viewer_views() -> list[dict[str, str]]:
    return [{"view_id": item.view_id, "label": item.label} for item in VIEWER_VIEWS]
