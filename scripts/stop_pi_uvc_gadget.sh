#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)
STATE_DIR="${PI_GATEWAY_STATE_DIR:-${PROJECT_ROOT}/run_data/pi_gateway}"
STATE_FILE="${STATE_DIR}/gadget_state.json"

sudo modprobe -r g_webcam >/dev/null 2>&1 || true
rm -f "${STATE_FILE}"

echo "UVC gadget stopped"
