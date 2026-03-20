# HIL Runtime Assets

This top-level tree stores runtime assets that deploy to different machines and should not keep accumulating under `src/carla_web_platform/`.

## Layout

- `host/scripts/`
  - CARLA headed startup and front RGB / native follow preview helpers for the Ubuntu host
- `pi/scripts/`
  - Raspberry Pi HDMI capture, RTP send, UVC gadget, gateway agent, and DUT result receiver entrypoints
- `pi/systemd/`
  - Pi systemd service templates
- `pi/config/`
  - Pi environment examples
- `jetson/scripts/`
  - Jetson detector launchers, metrics reporters, and demo wrappers
- `jetson/tools/jetson_cpp_detector/`
  - Jetson Nano C++ detector source
- `docs/`
  - Verified bring-up notes and live investigation logs

## Boundary

- Keep platform product code, FastAPI routes, frontend pages, executor logic, and platform-only deployment scripts inside `src/carla_web_platform/`.
- Keep host / Pi / Jetson runtime helpers and hardware-chain notes inside `src/hil_runtime/`.

## Path Assumptions

- Shell entrypoints in this tree auto-detect `src/carla_web_platform/` as the platform root.
- Override `DUCKPARK_PLATFORM_ROOT` when the platform repo is checked out somewhere else.
- Override `DUCKPARK_SRC_ROOT` when the top-level `src/` root is not adjacent to this directory.

## Current Note

- The existing `src/carla_web_platform/scripts/remote_deploy.sh` still focuses on platform deployment.
- If `hil_runtime/` needs to be synced to a remote host, Pi, or Jetson, use a target-specific copy/sync step rather than assuming the platform deploy bundle includes it.
- For the verified Ubuntu host bring-up flow that combines Web, headed CARLA, and host follow display, read `../carla_web_platform/docs/host-bringup.md`.
