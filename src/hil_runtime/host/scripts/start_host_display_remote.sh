#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./host_ssh_common.sh
source "${SCRIPT_DIR}/host_ssh_common.sh"

duckpark_host_ssh_init

DISPLAY_WAIT_FOR_ROLE_SECONDS="${DUCKPARK_HIL_DISPLAY_WAIT_FOR_ROLE_SECONDS:-${DUCKPARK_HIL_TIMEOUT_SECONDS:-86400}}"

duckpark_host_ssh \
  DUCKPARK_HOST_SRC_ROOT_VALUE="${DUCKPARK_HOST_SRC_ROOT}" \
  DUCKPARK_HIL_MAP_NAME_VALUE="${DUCKPARK_HIL_MAP_NAME:-Town01}" \
  DUCKPARK_HIL_DISPLAY_WAIT_FOR_ROLE_SECONDS_VALUE="${DISPLAY_WAIT_FOR_ROLE_SECONDS}" \
  bash -s <<'EOF'
set -euo pipefail

cd "${DUCKPARK_HOST_SRC_ROOT_VALUE}"
CARLA_FRONT_RGB_PREVIEW_BACKGROUND=1 \
  bash hil_runtime/host/scripts/start_carla_front_rgb_preview.sh \
  --display-mode native_follow \
  --map-name "${DUCKPARK_HIL_MAP_NAME_VALUE}" \
  --no-spawn-ego-if-missing \
  --no-enable-autopilot \
  --traffic-vehicles 0 \
  --wait-for-role-seconds "${DUCKPARK_HIL_DISPLAY_WAIT_FOR_ROLE_SECONDS_VALUE}"
EOF
