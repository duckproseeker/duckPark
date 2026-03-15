from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SensorRecorderResult:
    profile_name: str | None
    sensor_count: int
    output_root: Path


class SensorRecorder:
    """Attach descriptor-defined sensors to the hero actor and persist outputs."""

    def __init__(
        self,
        host: str,
        port: int,
        timeout_seconds: float,
        output_root: Path,
    ) -> None:
        self._host = host
        self._port = port
        self._timeout_seconds = timeout_seconds
        self._output_root = output_root

        self._carla: Any = None
        self._client: Any = None
        self._world: Any = None
        self._hero_actor: Any = None
        self._spawned_sensors: list[Any] = []
        self._jsonl_handles: dict[str, Any] = {}
        self._lock = threading.Lock()

    def start(self, descriptor: Any, *, hero_role_name: str = "hero") -> SensorRecorderResult:
        sensor_config = getattr(descriptor, "sensors", None)
        sensor_specs = list(getattr(sensor_config, "sensors", []) or [])
        if not getattr(sensor_config, "enabled", False) or not sensor_specs:
            raise RuntimeError("descriptor does not define enabled sensors")

        self._connect()
        self._hero_actor = self._wait_for_hero_actor(hero_role_name)
        blueprint_library = self._world.get_blueprint_library()
        self._output_root.mkdir(parents=True, exist_ok=True)

        manifest = {
            "profile_name": getattr(sensor_config, "profile_name", None),
            "config_yaml_path": getattr(sensor_config, "config_yaml_path", None),
            "hero_role_name": hero_role_name,
            "sensors": [spec.model_dump(mode="json") for spec in sensor_specs],
        }
        (self._output_root / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        for spec in sensor_specs:
            blueprint = blueprint_library.find(spec.type)
            self._apply_spec_to_blueprint(blueprint, spec)
            transform = self._build_transform(spec)
            sensor_actor = self._world.spawn_actor(
                blueprint,
                transform,
                attach_to=self._hero_actor,
            )
            sensor_output_dir = self._output_root / spec.id
            sensor_output_dir.mkdir(parents=True, exist_ok=True)
            sensor_actor.listen(
                self._build_sensor_callback(
                    sensor_id=spec.id,
                    sensor_type=spec.type,
                    output_dir=sensor_output_dir,
                )
            )
            self._spawned_sensors.append(sensor_actor)

        return SensorRecorderResult(
            profile_name=getattr(sensor_config, "profile_name", None),
            sensor_count=len(self._spawned_sensors),
            output_root=self._output_root,
        )

    def stop(self) -> None:
        for handle in self._jsonl_handles.values():
            try:
                handle.close()
            except Exception:  # noqa: BLE001
                pass
        self._jsonl_handles.clear()

        sensor_actors = list(reversed(self._spawned_sensors))
        for sensor_actor in sensor_actors:
            try:
                sensor_actor.listen(lambda *_args: None)
            except Exception:  # noqa: BLE001
                pass
            try:
                sensor_actor.stop()
            except Exception:  # noqa: BLE001
                pass
        # CARLA sensor callbacks may still flush briefly after stop(); give the
        # native listener threads a short grace window before destroy().
        if sensor_actors:
            time.sleep(0.2)
        for sensor_actor in sensor_actors:
            try:
                sensor_actor.destroy()
            except Exception:  # noqa: BLE001
                pass
        self._spawned_sensors.clear()
        self._hero_actor = None
        self._world = None
        self._client = None
        self._carla = None

    def _connect(self) -> None:
        try:
            import carla  # type: ignore
        except ImportError as exc:
            raise RuntimeError("carla Python API not found for sensor recording") from exc

        self._carla = carla
        self._client = carla.Client(self._host, self._port)
        self._client.set_timeout(self._timeout_seconds)
        self._world = self._client.get_world()

    def _wait_for_hero_actor(self, role_name: str, wait_timeout_seconds: float = 40.0) -> Any:
        deadline = time.monotonic() + wait_timeout_seconds
        while time.monotonic() < deadline:
            self._world = self._client.get_world()
            candidates = list(self._world.get_actors().filter("vehicle.*"))
            fallback_candidates: list[Any] = []
            for actor in candidates:
                actor_role = str(actor.attributes.get("role_name") or "").strip()
                if actor_role == role_name:
                    return actor
                if actor_role and actor_role.startswith("scenario_"):
                    continue
                fallback_candidates.append(actor)
            if len(fallback_candidates) == 1:
                return fallback_candidates[0]
            if len(fallback_candidates) > 1:
                fallback_candidates.sort(key=lambda actor: int(actor.id))
                return fallback_candidates[0]
            time.sleep(0.2)
        raise RuntimeError(f"hero actor with role_name='{role_name}' not found")

    def _build_transform(self, spec: Any) -> Any:
        return self._carla.Transform(
            self._carla.Location(
                x=float(spec.x),
                y=float(spec.y),
                z=float(spec.z),
            ),
            self._carla.Rotation(
                roll=float(spec.roll),
                pitch=float(spec.pitch),
                yaw=float(spec.yaw),
            ),
        )

    def _apply_spec_to_blueprint(self, blueprint: Any, spec: Any) -> None:
        attributes = {
            "image_size_x": getattr(spec, "width", None),
            "image_size_y": getattr(spec, "height", None),
            "fov": getattr(spec, "fov", None),
            "horizontal_fov": getattr(spec, "horizontal_fov", None),
            "vertical_fov": getattr(spec, "vertical_fov", None),
            "range": getattr(spec, "range", None),
            "channels": getattr(spec, "channels", None),
            "points_per_second": getattr(spec, "points_per_second", None),
            "rotation_frequency": getattr(spec, "rotation_frequency", None),
        }
        reading_frequency = getattr(spec, "reading_frequency", None)
        if reading_frequency not in {None, 0}:
            attributes["sensor_tick"] = 1.0 / float(reading_frequency)

        for key, value in attributes.items():
            if value is None:
                continue
            self._set_blueprint_attribute(blueprint, key, value)

        extra_attributes = getattr(spec, "attributes", {}) or {}
        if isinstance(extra_attributes, dict):
            for key, value in extra_attributes.items():
                self._set_blueprint_attribute(blueprint, str(key), value)

    def _set_blueprint_attribute(self, blueprint: Any, key: str, value: Any) -> None:
        if not blueprint.has_attribute(key):
            return
        blueprint.set_attribute(key, str(value))

    def _build_sensor_callback(
        self, *, sensor_id: str, sensor_type: str, output_dir: Path
    ):
        def _callback(measurement: Any) -> None:
            try:
                self._persist_measurement(
                    sensor_id=sensor_id,
                    sensor_type=sensor_type,
                    output_dir=output_dir,
                    measurement=measurement,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("sensor recorder failed for %s: %s", sensor_id, exc)

        return _callback

    def _persist_measurement(
        self,
        *,
        sensor_id: str,
        sensor_type: str,
        output_dir: Path,
        measurement: Any,
    ) -> None:
        frame = int(getattr(measurement, "frame", 0))
        timestamp = float(getattr(measurement, "timestamp", 0.0))

        if sensor_type.startswith("sensor.camera."):
            image_path = output_dir / f"frame_{frame:06d}.png"
            if hasattr(measurement, "save_to_disk"):
                measurement.save_to_disk(str(image_path))
            else:
                image_path.write_bytes(bytes(getattr(measurement, "raw_data", b"")))
            return

        if sensor_type.startswith("sensor.lidar."):
            lidar_path = output_dir / f"frame_{frame:06d}.bin"
            lidar_path.write_bytes(bytes(getattr(measurement, "raw_data", b"")))
            return

        if sensor_type == "sensor.other.radar":
            detections: list[dict[str, float]] = []
            for detection in measurement:
                detections.append(
                    {
                        "altitude": float(detection.altitude),
                        "azimuth": float(detection.azimuth),
                        "depth": float(detection.depth),
                        "velocity": float(detection.velocity),
                    }
                )
            self._append_jsonl(
                sensor_id,
                output_dir,
                {
                    "frame": frame,
                    "timestamp": timestamp,
                    "detections": detections,
                },
            )
            return

        if sensor_type == "sensor.other.gnss":
            self._append_jsonl(
                sensor_id,
                output_dir,
                {
                    "frame": frame,
                    "timestamp": timestamp,
                    "latitude": float(measurement.latitude),
                    "longitude": float(measurement.longitude),
                    "altitude": float(measurement.altitude),
                },
            )
            return

        if sensor_type == "sensor.other.imu":
            self._append_jsonl(
                sensor_id,
                output_dir,
                {
                    "frame": frame,
                    "timestamp": timestamp,
                    "accelerometer": {
                        "x": float(measurement.accelerometer.x),
                        "y": float(measurement.accelerometer.y),
                        "z": float(measurement.accelerometer.z),
                    },
                    "gyroscope": {
                        "x": float(measurement.gyroscope.x),
                        "y": float(measurement.gyroscope.y),
                        "z": float(measurement.gyroscope.z),
                    },
                    "compass": float(measurement.compass),
                },
            )
            return

        if sensor_type == "sensor.opendrive_map":
            opendrive_path = output_dir / "opendrive.xml"
            payload = getattr(measurement, "opendrive", None)
            if payload is None:
                payload = str(measurement)
            opendrive_path.write_text(str(payload), encoding="utf-8")
            return

        raw_path = output_dir / f"frame_{frame:06d}.bin"
        if hasattr(measurement, "raw_data"):
            raw_path.write_bytes(bytes(getattr(measurement, "raw_data", b"")))
            return

        self._append_jsonl(
            sensor_id,
            output_dir,
            {
                "frame": frame,
                "timestamp": timestamp,
                "repr": repr(measurement),
            },
        )

    def _append_jsonl(self, sensor_id: str, output_dir: Path, payload: dict[str, Any]) -> None:
        with self._lock:
            handle = self._jsonl_handles.get(sensor_id)
            if handle is None:
                jsonl_path = output_dir / "records.jsonl"
                handle = jsonl_path.open("a", encoding="utf-8")
                self._jsonl_handles[sensor_id] = handle
            handle.write(json.dumps(payload, ensure_ascii=False))
            handle.write("\n")
            handle.flush()
