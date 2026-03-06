#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import math
import queue
import sys
import time
from dataclasses import dataclass

import numpy as np
import pygame

try:
    import carla
except ImportError as exc:
    raise SystemExit(
        "未找到 carla Python API。请先 source 对应环境，或把 carla-*.egg 加入 PYTHONPATH。"
    ) from exc


@dataclass
class CameraView:
    name: str
    transform: "carla.Transform"


class CarlaEgoViewer:
    """只读调试观察器。

    注意：
    - 本工具不会调用 world.tick()
    - 不会参与仿真控制，仅做观察显示
    """

    def __init__(
        self,
        host: str,
        port: int,
        width: int,
        height: int,
        timeout: float,
        role_names: list[str],
        poll_interval: float,
    ) -> None:
        self.host = host
        self.port = port
        self.width = width
        self.height = height
        self.timeout = timeout
        self.role_names = [r.strip().lower() for r in role_names if r.strip()]
        self.poll_interval = poll_interval

        self.client: carla.Client | None = None
        self.world: carla.World | None = None
        self.bp_lib: carla.BlueprintLibrary | None = None

        self.current_map_name: str = "<unknown>"
        self.last_sim_time: float | None = None
        self.world_switch_count = 0
        self.last_world_change_reason = ""

        self.ego_vehicle: carla.Vehicle | None = None
        self.camera_sensor: carla.Sensor | None = None

        self.surface: pygame.Surface | None = None
        self.display: pygame.Surface | None = None
        self.clock: pygame.time.Clock | None = None
        self.font: pygame.font.Font | None = None

        self.image_queue: "queue.Queue[carla.Image]" = queue.Queue(maxsize=2)
        self.current_view_index = 0

        self.views = [
            CameraView(
                name="第一视角",
                transform=carla.Transform(
                    carla.Location(x=0.35, y=0.0, z=1.25),
                    carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0),
                ),
            ),
            CameraView(
                name="第三视角",
                transform=carla.Transform(
                    carla.Location(x=-6.0, y=0.0, z=2.6),
                    carla.Rotation(pitch=-12.0, yaw=0.0, roll=0.0),
                ),
            ),
        ]

    def connect(self) -> None:
        self.client = carla.Client(self.host, self.port)
        self.client.set_timeout(self.timeout)
        self.refresh_world(reason="connect", force_log=True)
        print(
            f"[viewer] 连接成功 host={self.host} port={self.port} "
            f"map={self.current_map_name} role_names={self.role_names}",
            flush=True,
        )

    def init_pygame(self) -> None:
        pygame.init()
        pygame.font.init()
        self.display = pygame.display.set_mode(
            (self.width, self.height), pygame.HWSURFACE | pygame.DOUBLEBUF
        )
        pygame.display.set_caption("CARLA Ego Viewer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 18)

    def close(self) -> None:
        self.destroy_camera()
        self.ego_vehicle = None
        pygame.quit()

    def destroy_camera(self) -> None:
        if self.camera_sensor is not None:
            try:
                self.camera_sensor.stop()
            except Exception:
                pass
            try:
                self.camera_sensor.destroy()
            except Exception:
                pass
            self.camera_sensor = None

        while not self.image_queue.empty():
            try:
                self.image_queue.get_nowait()
            except queue.Empty:
                break

    def refresh_world(
        self, reason: str, force_log: bool = False
    ) -> tuple[carla.World, bool]:
        assert self.client is not None

        new_world = self.client.get_world()
        new_map_name = new_world.get_map().name

        sim_time: float | None = None
        try:
            snapshot = new_world.get_snapshot()
            sim_time = float(snapshot.timestamp.elapsed_seconds)
        except Exception:
            sim_time = None

        changed = False
        change_reasons: list[str] = []

        if self.world is None:
            changed = True
            change_reasons.append("首次获取 world")
        elif self.current_map_name != new_map_name:
            changed = True
            change_reasons.append(
                f"map 切换: {self.current_map_name} -> {new_map_name}"
            )
        elif (
            self.last_sim_time is not None
            and sim_time is not None
            and sim_time + 0.5 < self.last_sim_time
        ):
            changed = True
            change_reasons.append(
                f"sim_time 回退: {self.last_sim_time:.3f} -> {sim_time:.3f}（可能 world 重载）"
            )

        self.world = new_world
        self.bp_lib = self.world.get_blueprint_library()
        self.current_map_name = new_map_name
        if sim_time is not None:
            self.last_sim_time = sim_time

        if changed:
            self.world_switch_count += 1
            self.last_world_change_reason = "; ".join(change_reasons)
            print(
                f"[viewer] 检测到 world 变化: reason={self.last_world_change_reason} "
                f"map={self.current_map_name} trigger={reason}",
                flush=True,
            )
            self._handle_world_switch()
        elif force_log:
            print(
                f"[viewer] world 刷新: map={self.current_map_name} sim_time={self.last_sim_time}",
                flush=True,
            )

        return self.world, changed

    def _handle_world_switch(self) -> None:
        self.destroy_camera()
        self.ego_vehicle = None

    def _role_priority(self) -> list[str]:
        priority = ["ego_vehicle"]
        for name in self.role_names:
            if name not in priority:
                priority.append(name)
        return priority

    @staticmethod
    def _vehicle_sort_key(vehicle: carla.Vehicle) -> tuple[int, float]:
        vel = vehicle.get_velocity()
        speed = math.sqrt(vel.x * vel.x + vel.y * vel.y + vel.z * vel.z)
        alive = 1 if vehicle.is_alive else 0
        return alive, speed

    def _collect_vehicle_diagnostics(
        self, vehicles: list[carla.Vehicle], max_items: int = 8
    ) -> tuple[dict[str, int], list[tuple[int, str]]]:
        role_counts: dict[str, int] = {}
        preview: list[tuple[int, str]] = []

        for vehicle in vehicles:
            role = vehicle.attributes.get("role_name", "").strip() or "<empty>"
            role_counts[role] = role_counts.get(role, 0) + 1
            if len(preview) < max_items:
                preview.append((vehicle.id, role))

        return role_counts, preview

    def _print_no_ego_diagnostics(
        self,
        world_switched: bool,
        vehicles: list[carla.Vehicle],
    ) -> None:
        role_counts, preview = self._collect_vehicle_diagnostics(vehicles)
        print(
            "[viewer] 未找到 ego: "
            f"host={self.host} port={self.port} map={self.current_map_name} "
            f"vehicles={len(vehicles)} role_counts={role_counts} "
            f"world_switched={world_switched} switch_reason={self.last_world_change_reason or '<none>'}",
            flush=True,
        )
        if preview:
            print(f"[viewer] vehicles 预览(id, role_name): {preview}", flush=True)

    def find_ego_vehicle(self) -> carla.Vehicle | None:
        world, world_switched = self.refresh_world(reason="find_ego_vehicle")

        actors = world.get_actors().filter("vehicle.*")
        vehicles = [actor for actor in actors if isinstance(actor, carla.Vehicle)]

        role_priority = self._role_priority()
        for role_name in role_priority:
            matches = [
                vehicle
                for vehicle in vehicles
                if vehicle.attributes.get("role_name", "").strip().lower() == role_name
            ]
            if matches:
                matches.sort(key=self._vehicle_sort_key, reverse=True)
                return matches[0]

        self._print_no_ego_diagnostics(world_switched=world_switched, vehicles=vehicles)
        return None

    def wait_for_ego_vehicle(self) -> carla.Vehicle:
        while True:
            ego = self.find_ego_vehicle()
            if ego is not None and ego.is_alive:
                transform = ego.get_transform()
                velocity = ego.get_velocity()
                speed = (
                    math.sqrt(
                        velocity.x * velocity.x
                        + velocity.y * velocity.y
                        + velocity.z * velocity.z
                    )
                    * 3.6
                )
                print(
                    f"[viewer] 命中 ego: id={ego.id} role_name={ego.attributes.get('role_name', '')} "
                    f"loc=({transform.location.x:.2f}, {transform.location.y:.2f}, {transform.location.z:.2f}) "
                    f"speed={speed:.2f} km/h map={self.current_map_name}",
                    flush=True,
                )
                return ego

            time.sleep(self.poll_interval)

    def _camera_blueprint(self) -> carla.ActorBlueprint:
        assert self.bp_lib is not None

        bp = self.bp_lib.find("sensor.camera.rgb")
        bp.set_attribute("image_size_x", str(self.width))
        bp.set_attribute("image_size_y", str(self.height))
        bp.set_attribute("fov", "100")

        optional_attrs = {
            "sensor_tick": "0.0",
            "motion_blur_intensity": "0.0",
            "gamma": "2.2",
        }
        for key, value in optional_attrs.items():
            if bp.has_attribute(key):
                bp.set_attribute(key, value)

        return bp

    def spawn_camera(self) -> None:
        world, _ = self.refresh_world(reason="spawn_camera")
        assert self.ego_vehicle is not None

        self.destroy_camera()

        bp = self._camera_blueprint()
        view = self.views[self.current_view_index]

        sensor = world.spawn_actor(
            bp,
            view.transform,
            attach_to=self.ego_vehicle,
            attachment_type=(
                carla.AttachmentType.SpringArmGhost
                if view.name == "第三视角"
                else carla.AttachmentType.Rigid
            ),
        )

        sensor.listen(self._on_image)
        self.camera_sensor = sensor

    def _on_image(self, image: carla.Image) -> None:
        try:
            if self.image_queue.full():
                _ = self.image_queue.get_nowait()
            self.image_queue.put_nowait(image)
        except queue.Full:
            pass

    def switch_view(self) -> None:
        self.current_view_index = (self.current_view_index + 1) % len(self.views)
        if self.ego_vehicle is not None and self.ego_vehicle.is_alive:
            self.spawn_camera()

    def ensure_camera_attached(self) -> None:
        _, world_switched = self.refresh_world(reason="ensure_camera_attached")

        if self.ego_vehicle is None or not self.ego_vehicle.is_alive:
            self.ego_vehicle = self.wait_for_ego_vehicle()
            self.spawn_camera()
            return

        if world_switched:
            self.ego_vehicle = self.wait_for_ego_vehicle()
            self.spawn_camera()
            return

        if self.camera_sensor is None or not self.camera_sensor.is_alive:
            self.spawn_camera()

    def image_to_surface(self, image: carla.Image) -> pygame.Surface:
        array = np.frombuffer(image.raw_data, dtype=np.uint8)
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]  # BGRA -> RGB
        array = np.swapaxes(array, 0, 1)
        return pygame.surfarray.make_surface(array)

    def draw_overlay(self) -> None:
        assert self.display is not None
        assert self.font is not None
        assert self.clock is not None

        lines: list[str] = [
            "CARLA 本地调试观察器（只读）",
            "TAB: 切换第一/第三视角",
            "R: 重新查找 ego 并重挂相机",
            "ESC/Q: 退出",
            f"host={self.host} port={self.port} map={self.current_map_name}",
            f"world_switch_count={self.world_switch_count}",
        ]

        if self.ego_vehicle is not None and self.ego_vehicle.is_alive:
            role_name = self.ego_vehicle.attributes.get("role_name", "")
            transform = self.ego_vehicle.get_transform()
            velocity = self.ego_vehicle.get_velocity()
            speed = (
                math.sqrt(
                    velocity.x * velocity.x
                    + velocity.y * velocity.y
                    + velocity.z * velocity.z
                )
                * 3.6
            )

            lines.append(
                f"ego id={self.ego_vehicle.id} role_name={role_name} "
                f"view={self.views[self.current_view_index].name}"
            )
            lines.append(
                f"loc=({transform.location.x:.2f}, {transform.location.y:.2f}, {transform.location.z:.2f}) "
                f"yaw={transform.rotation.yaw:.1f}"
            )
            lines.append(f"speed={speed:.2f} km/h")
        else:
            lines.append("ego: 未找到")

        lines.append(f"FPS={self.clock.get_fps():.1f}")

        x, y = 12, 10
        line_h = 22
        bg = pygame.Surface((960, 28 + line_h * len(lines)), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        self.display.blit(bg, (x - 6, y - 4))

        for i, text in enumerate(lines):
            text_surface = self.font.render(text, True, (255, 255, 255))
            self.display.blit(text_surface, (x, y + i * line_h))

    def run(self) -> None:
        self.connect()
        self.init_pygame()
        self.ensure_camera_attached()

        assert self.display is not None
        assert self.clock is not None

        last_rebind_check = 0.0

        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                    if event.type == pygame.KEYUP:
                        if event.key in (pygame.K_ESCAPE, pygame.K_q):
                            return
                        if event.key == pygame.K_TAB:
                            self.switch_view()
                        if event.key == pygame.K_r:
                            self.ego_vehicle = None
                            self.ensure_camera_attached()

                now = time.time()
                if now - last_rebind_check > 1.0:
                    self.ensure_camera_attached()
                    last_rebind_check = now

                try:
                    image = self.image_queue.get(timeout=0.2)
                    self.surface = self.image_to_surface(image)
                except queue.Empty:
                    pass

                if self.surface is not None:
                    self.display.blit(self.surface, (0, 0))
                else:
                    self.display.fill((30, 30, 30))

                self.draw_overlay()
                pygame.display.flip()
                self.clock.tick(30)
        finally:
            self.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CARLA 本地调试观察器：自动查找 ego 车辆并显示第一/第三视角"
    )
    parser.add_argument("--host", default="127.0.0.1", help="CARLA 主机地址")
    parser.add_argument("--port", type=int, default=2000, help="CARLA RPC 端口")
    parser.add_argument("--width", type=int, default=1280, help="窗口宽度")
    parser.add_argument("--height", type=int, default=720, help="窗口高度")
    parser.add_argument("--timeout", type=float, default=5.0, help="CARLA RPC 超时")
    parser.add_argument(
        "--role-names",
        default="ego_vehicle,hero,ego",
        help="用于匹配 ego 的 role_name，逗号分隔（优先 ego_vehicle）",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="未找到 ego 时的轮询间隔（秒）",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    role_names = [x.strip() for x in args.role_names.split(",") if x.strip()]

    viewer = CarlaEgoViewer(
        host=args.host,
        port=args.port,
        width=args.width,
        height=args.height,
        timeout=args.timeout,
        role_names=role_names,
        poll_interval=args.poll_interval,
    )
    viewer.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
