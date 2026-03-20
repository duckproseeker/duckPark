#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${CARLA_FRONT_RGB_PREVIEW_CONTAINER:-ros2-dev}"
CONTAINER_SRC_ROOT="${CARLA_FRONT_RGB_PREVIEW_SRC_ROOT:-/ros2_ws/src}"
CONTAINER_PLATFORM_ROOT="${CARLA_FRONT_RGB_PREVIEW_PLATFORM_ROOT:-${CONTAINER_SRC_ROOT}/carla_web_platform}"
DISPLAY_VALUE="${CARLA_FRONT_RGB_PREVIEW_DISPLAY:-:1}"
XAUTHORITY_PATH="${CARLA_FRONT_RGB_PREVIEW_XAUTHORITY:-/run/user/1000/gdm/Xauthority}"
PYTHONPATH_VALUE="${CARLA_FRONT_RGB_PREVIEW_PYTHONPATH:-${CONTAINER_PLATFORM_ROOT}}"
SCRIPT_PATH="${CARLA_FRONT_RGB_PREVIEW_SCRIPT_PATH:-hil_runtime/host/scripts/carla_front_rgb_preview.py}"
BACKGROUND="${CARLA_FRONT_RGB_PREVIEW_BACKGROUND:-0}"
LOG_FILE="${CARLA_FRONT_RGB_PREVIEW_LOG_FILE:-/tmp/carla_front_rgb_preview.log}"

usage() {
  cat <<'EOF'
Usage:
  bash hil_runtime/host/scripts/start_carla_front_rgb_preview.sh [preview args...]

Environment overrides:
  CARLA_FRONT_RGB_PREVIEW_CONTAINER   Docker container name, default ros2-dev
  CARLA_FRONT_RGB_PREVIEW_SRC_ROOT    Source root inside container, default /ros2_ws/src
  CARLA_FRONT_RGB_PREVIEW_PLATFORM_ROOT
                                      Platform repo path inside container, default /ros2_ws/src/carla_web_platform
  CARLA_FRONT_RGB_PREVIEW_DISPLAY     X11 display, default :1
  CARLA_FRONT_RGB_PREVIEW_XAUTHORITY  Xauthority path inside container
  CARLA_FRONT_RGB_PREVIEW_SCRIPT_PATH Preview script path relative to source root
  CARLA_FRONT_RGB_PREVIEW_BACKGROUND  1 to run under nohup in the background
  CARLA_FRONT_RGB_PREVIEW_LOG_FILE    Background log file path

Examples:
  bash hil_runtime/host/scripts/start_carla_front_rgb_preview.sh
  bash hil_runtime/host/scripts/start_carla_front_rgb_preview.sh --display-mode native_follow
  CARLA_FRONT_RGB_PREVIEW_BACKGROUND=1 bash hil_runtime/host/scripts/start_carla_front_rgb_preview.sh --traffic-vehicles 20
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command not found: $1" >&2
    exit 1
  fi
}

bool_flag() {
  local value
  value=$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]')
  [[ "${value}" == "1" || "${value}" == "true" || "${value}" == "yes" || "${value}" == "on" ]]
}

require_command docker

docker exec "${CONTAINER_NAME}" pkill -f "python3 ${SCRIPT_PATH}" >/dev/null 2>&1 || true

declare -a cmd=(
  docker exec
  -e "DISPLAY=${DISPLAY_VALUE}"
  -e "XAUTHORITY=${XAUTHORITY_PATH}"
  -e "PYTHONPATH=${PYTHONPATH_VALUE}"
  -e "DUCKPARK_PLATFORM_ROOT=${CONTAINER_PLATFORM_ROOT}"
  -w "${CONTAINER_SRC_ROOT}"
  "${CONTAINER_NAME}"
  python3
  "${SCRIPT_PATH}"
)

if (($# > 0)); then
  cmd+=("$@")
fi

if bool_flag "${BACKGROUND}"; then
  nohup "${cmd[@]}" >"${LOG_FILE}" 2>&1 &
  echo "front RGB preview started in background, pid=$!, log=${LOG_FILE}"
  exit 0
fi

exec "${cmd[@]}"
