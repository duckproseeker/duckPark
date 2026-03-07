#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)
STATE_DIR="${PI_GATEWAY_STATE_DIR:-${PROJECT_ROOT}/run_data/pi_gateway}"
STATE_FILE="${STATE_DIR}/bridge_state.json"

pkill -f 'ffmpeg .* -f v4l2 .* /dev/video' >/dev/null 2>&1 || true

if [[ -f "${STATE_FILE}" ]]; then
  python3 - <<PY
import json
from pathlib import Path

state_path = Path("${STATE_FILE}")
payload = json.loads(state_path.read_text(encoding="utf-8"))
payload["bridge_running"] = False
state_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
PY
fi

echo "HDMI to UVC bridge stopped"
