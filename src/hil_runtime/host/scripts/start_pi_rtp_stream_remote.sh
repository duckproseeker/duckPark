#!/usr/bin/env bash
set -euo pipefail

PI_HOST="${DUCKPARK_PI_HOST:-}"
PI_USER="${DUCKPARK_PI_USER:-}"
PI_PORT="${DUCKPARK_PI_PORT:-22}"
PI_RUNTIME_ROOT="${DUCKPARK_PI_RUNTIME_ROOT:-\$HOME/duckPark/src/hil_runtime}"
PI_LEGACY_PLATFORM_ROOT="${DUCKPARK_PI_LEGACY_PLATFORM_ROOT:-\$HOME/duckpark/carla_web_platform}"
PI_LOG_FILE="${DUCKPARK_PI_RTP_LOG_FILE:-/tmp/duckpark_pi_rtp_stream.log}"
SSH_BIN="${DUCKPARK_PI_SSH_BIN:-ssh}"
SSH_STRICT_HOST_KEY_CHECKING="${DUCKPARK_PI_SSH_STRICT_HOST_KEY_CHECKING:-accept-new}"
SSH_IDENTITY_FILE="${DUCKPARK_PI_SSH_IDENTITY_FILE:-}"

PI_HDMI_RTP_DEVICE_VALUE="${PI_HDMI_RTP_DEVICE:-/dev/video0}"
PI_HDMI_RTP_TARGET_HOST_VALUE="${PI_HDMI_RTP_TARGET_HOST:-192.168.50.2}"
PI_HDMI_RTP_TARGET_PORT_VALUE="${PI_HDMI_RTP_TARGET_PORT:-5000}"
PI_HDMI_RTP_WIDTH_VALUE="${PI_HDMI_RTP_WIDTH:-1920}"
PI_HDMI_RTP_HEIGHT_VALUE="${PI_HDMI_RTP_HEIGHT:-1080}"
PI_HDMI_RTP_FRAMERATE_VALUE="${PI_HDMI_RTP_FRAMERATE:-30}"
PI_HDMI_RTP_ENCODER_VALUE="${PI_HDMI_RTP_ENCODER:-auto}"
PI_HDMI_RTP_NETWORK_INTERFACE_VALUE="${PI_HDMI_RTP_NETWORK_INTERFACE:-eth0}"
PI_HDMI_RTP_INPUT_PIXFMT_VALUE="${PI_HDMI_RTP_INPUT_PIXFMT:-RGB3}"
PI_HDMI_RTP_FORCE_V4L2_FORMAT_VALUE="${PI_HDMI_RTP_FORCE_V4L2_FORMAT:-1}"
PI_HDMI_RTP_BITRATE_KBPS_VALUE="${PI_HDMI_RTP_BITRATE_KBPS:-8000}"

usage() {
  cat <<'EOF'
Usage:
  bash hil_runtime/host/scripts/start_pi_rtp_stream_remote.sh

Required environment:
  DUCKPARK_PI_HOST                  Pi SSH host
  DUCKPARK_PI_USER                  Pi SSH user

Optional environment:
  DUCKPARK_PI_PORT                  Pi SSH port, default 22
  DUCKPARK_PI_RUNTIME_ROOT          New-layout hil_runtime root on Pi
  DUCKPARK_PI_LEGACY_PLATFORM_ROOT  Legacy platform repo root on Pi
  DUCKPARK_PI_RTP_LOG_FILE          Pi-side RTP log file path
  DUCKPARK_PI_SSH_BIN               SSH binary, default ssh
  DUCKPARK_PI_SSH_STRICT_HOST_KEY_CHECKING
                                     SSH StrictHostKeyChecking mode, default accept-new
  DUCKPARK_PI_SSH_IDENTITY_FILE     Optional SSH identity file. If unset, the wrapper will
                                     reuse ~/.ssh/id_ed25519_duckpark when present.

Pass-through Pi RTP environment:
  PI_HDMI_RTP_DEVICE
  PI_HDMI_RTP_TARGET_HOST
  PI_HDMI_RTP_TARGET_PORT
  PI_HDMI_RTP_WIDTH
  PI_HDMI_RTP_HEIGHT
  PI_HDMI_RTP_FRAMERATE
  PI_HDMI_RTP_ENCODER
  PI_HDMI_RTP_NETWORK_INTERFACE
  PI_HDMI_RTP_INPUT_PIXFMT
  PI_HDMI_RTP_FORCE_V4L2_FORMAT
  PI_HDMI_RTP_BITRATE_KBPS

Notes:
  - This wrapper is intended for HIL orchestration commands executed from the host/container.
  - SSH key-based auth should already be configured; the script runs with BatchMode=yes.
EOF
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command not found: $1" >&2
    exit 1
  fi
}

require_text() {
  local value="$1"
  local label="$2"
  if [[ -z "${value}" ]]; then
    echo "${label} is required" >&2
    exit 1
  fi
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

require_command "${SSH_BIN}"
require_text "${PI_HOST}" "DUCKPARK_PI_HOST"
require_text "${PI_USER}" "DUCKPARK_PI_USER"

SSH_TARGET="${PI_USER}@${PI_HOST}"
declare -a SSH_ARGS=(
  -p "${PI_PORT}"
  -o BatchMode=yes
  -o "StrictHostKeyChecking=${SSH_STRICT_HOST_KEY_CHECKING}"
)

if [[ -z "${SSH_IDENTITY_FILE}" ]] && [[ -f "${HOME}/.ssh/id_ed25519_duckpark" ]]; then
  SSH_IDENTITY_FILE="${HOME}/.ssh/id_ed25519_duckpark"
fi

if [[ -n "${SSH_IDENTITY_FILE}" ]]; then
  SSH_ARGS+=(-i "${SSH_IDENTITY_FILE}" -o IdentitiesOnly=yes)
fi

"${SSH_BIN}" \
  "${SSH_ARGS[@]}" \
  "${SSH_TARGET}" \
  PI_HDMI_RTP_DEVICE_VALUE="${PI_HDMI_RTP_DEVICE_VALUE}" \
  PI_HDMI_RTP_TARGET_HOST_VALUE="${PI_HDMI_RTP_TARGET_HOST_VALUE}" \
  PI_HDMI_RTP_TARGET_PORT_VALUE="${PI_HDMI_RTP_TARGET_PORT_VALUE}" \
  PI_HDMI_RTP_WIDTH_VALUE="${PI_HDMI_RTP_WIDTH_VALUE}" \
  PI_HDMI_RTP_HEIGHT_VALUE="${PI_HDMI_RTP_HEIGHT_VALUE}" \
  PI_HDMI_RTP_FRAMERATE_VALUE="${PI_HDMI_RTP_FRAMERATE_VALUE}" \
  PI_HDMI_RTP_ENCODER_VALUE="${PI_HDMI_RTP_ENCODER_VALUE}" \
  PI_HDMI_RTP_NETWORK_INTERFACE_VALUE="${PI_HDMI_RTP_NETWORK_INTERFACE_VALUE}" \
  PI_HDMI_RTP_INPUT_PIXFMT_VALUE="${PI_HDMI_RTP_INPUT_PIXFMT_VALUE}" \
  PI_HDMI_RTP_FORCE_V4L2_FORMAT_VALUE="${PI_HDMI_RTP_FORCE_V4L2_FORMAT_VALUE}" \
  PI_HDMI_RTP_BITRATE_KBPS_VALUE="${PI_HDMI_RTP_BITRATE_KBPS_VALUE}" \
  PI_RUNTIME_ROOT_VALUE="${PI_RUNTIME_ROOT}" \
  PI_LEGACY_PLATFORM_ROOT_VALUE="${PI_LEGACY_PLATFORM_ROOT}" \
  PI_LOG_FILE_VALUE="${PI_LOG_FILE}" \
  bash -s <<'EOF'
set -euo pipefail

export PI_HDMI_RTP_DEVICE="${PI_HDMI_RTP_DEVICE_VALUE}"
export PI_HDMI_RTP_TARGET_HOST="${PI_HDMI_RTP_TARGET_HOST_VALUE}"
export PI_HDMI_RTP_TARGET_PORT="${PI_HDMI_RTP_TARGET_PORT_VALUE}"
export PI_HDMI_RTP_WIDTH="${PI_HDMI_RTP_WIDTH_VALUE}"
export PI_HDMI_RTP_HEIGHT="${PI_HDMI_RTP_HEIGHT_VALUE}"
export PI_HDMI_RTP_FRAMERATE="${PI_HDMI_RTP_FRAMERATE_VALUE}"
export PI_HDMI_RTP_ENCODER="${PI_HDMI_RTP_ENCODER_VALUE}"
export PI_HDMI_RTP_NETWORK_INTERFACE="${PI_HDMI_RTP_NETWORK_INTERFACE_VALUE}"
export PI_HDMI_RTP_INPUT_PIXFMT="${PI_HDMI_RTP_INPUT_PIXFMT_VALUE}"
export PI_HDMI_RTP_FORCE_V4L2_FORMAT="${PI_HDMI_RTP_FORCE_V4L2_FORMAT_VALUE}"
export PI_HDMI_RTP_BITRATE_KBPS="${PI_HDMI_RTP_BITRATE_KBPS_VALUE}"

RUNTIME_SCRIPT="${PI_RUNTIME_ROOT_VALUE}/pi/scripts/start_pi_hdmi_rtp_stream.sh"
LEGACY_SCRIPT="${PI_LEGACY_PLATFORM_ROOT_VALUE}/scripts/start_pi_hdmi_rtp_stream.sh"
LOG_FILE="${PI_LOG_FILE_VALUE}"

if pgrep -f 'start_pi_hdmi_rtp_stream.sh' >/dev/null 2>&1; then
  echo "pi_rtp_already_running log=${LOG_FILE}"
  exit 0
fi

if [[ -x "${RUNTIME_SCRIPT}" ]]; then
  nohup bash "${RUNTIME_SCRIPT}" >"${LOG_FILE}" 2>&1 < /dev/null &
elif [[ -x "${LEGACY_SCRIPT}" ]]; then
  nohup bash "${LEGACY_SCRIPT}" >"${LOG_FILE}" 2>&1 < /dev/null &
else
  echo "Pi RTP start script not found. Tried: ${RUNTIME_SCRIPT} ${LEGACY_SCRIPT}" >&2
  exit 1
fi

sleep 1
if pgrep -f 'start_pi_hdmi_rtp_stream.sh' >/dev/null 2>&1; then
  echo "pi_rtp_started log=${LOG_FILE}"
  exit 0
fi

echo "Pi RTP stream did not stay up. Recent log:" >&2
tail -n 40 "${LOG_FILE}" >&2 || true
exit 1
EOF
