#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)
STATE_DIR="${PI_GATEWAY_STATE_DIR:-${PROJECT_ROOT}/run_data/pi_gateway}"
STATE_FILE="${STATE_DIR}/bridge_state.json"

MEDIA_DEVICE="${PI_GATEWAY_MEDIA_DEVICE:-/dev/media0}"
HDMI_STATUS_DEVICE="${PI_GATEWAY_HDMI_STATUS_DEVICE:-/dev/v4l-subdev2}"
INPUT_VIDEO_DEVICE="${PI_GATEWAY_INPUT_VIDEO_DEVICE:-/dev/video0}"
FRAMERATE="${PI_GATEWAY_BRIDGE_FRAMERATE:-30}"
WIDTH=""
HEIGHT=""

usage() {
  cat <<'EOF'
用法:
  bash scripts/start_pi_hdmi_to_uvc_bridge.sh [options]

可选参数:
  --media-device <path>         media device，默认 /dev/media0
  --hdmi-status-device <path>   tc358743 subdev，默认 /dev/v4l-subdev2
  --input-video-device <path>   采集节点，默认 /dev/video0
  --width <pixels>              手动指定宽度
  --height <pixels>             手动指定高度
  --framerate <fps>             输出帧率，默认 30
  --help                        输出帮助
EOF
}

require_arg_value() {
  if [[ $# -lt 2 || -z "${2:-}" ]]; then
    echo "参数 $1 缺少取值" >&2
    usage >&2
    exit 1
  fi
}

find_gadget_video_device() {
  python3 - <<'PY'
import subprocess

output = subprocess.run(
    ["v4l2-ctl", "--list-devices"],
    capture_output=True,
    check=False,
    text=True,
    timeout=2.0,
).stdout

current_block = None
for raw_line in output.splitlines():
    line = raw_line.rstrip()
    if not line:
        current_block = None
        continue
    if not raw_line.startswith("\t"):
        current_block = line
        continue
    if current_block and ("gadget.0" in current_block or ".usb" in current_block):
        device = line.strip()
        if device.startswith("/dev/video"):
            print(device)
            break
PY
}

while (($# > 0)); do
  case "$1" in
    --media-device)
      require_arg_value "$@"
      MEDIA_DEVICE="$2"
      shift 2
      ;;
    --hdmi-status-device)
      require_arg_value "$@"
      HDMI_STATUS_DEVICE="$2"
      shift 2
      ;;
    --input-video-device)
      require_arg_value "$@"
      INPUT_VIDEO_DEVICE="$2"
      shift 2
      ;;
    --width)
      require_arg_value "$@"
      WIDTH="$2"
      shift 2
      ;;
    --height)
      require_arg_value "$@"
      HEIGHT="$2"
      shift 2
      ;;
    --framerate)
      require_arg_value "$@"
      FRAMERATE="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "未知参数: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

mkdir -p "${STATE_DIR}"

bash "${SCRIPT_DIR}/start_pi_uvc_gadget.sh"
CONFIG_ARGS=(
  --media-device "${MEDIA_DEVICE}"
  --hdmi-status-device "${HDMI_STATUS_DEVICE}"
  --input-video-device "${INPUT_VIDEO_DEVICE}"
)
if [[ -n "${WIDTH}" ]]; then
  CONFIG_ARGS+=(--width "${WIDTH}")
fi
if [[ -n "${HEIGHT}" ]]; then
  CONFIG_ARGS+=(--height "${HEIGHT}")
fi

bash "${SCRIPT_DIR}/configure_pi_hdmi_input.sh" "${CONFIG_ARGS[@]}"

GADGET_VIDEO_DEVICE="$(find_gadget_video_device || true)"
if [[ -z "${GADGET_VIDEO_DEVICE}" ]]; then
  echo "未找到 UVC gadget 输出节点" >&2
  exit 1
fi

if [[ -f "${STATE_FILE}" ]]; then
  WIDTH="$(python3 - <<PY
import json
from pathlib import Path
payload = json.loads(Path("${STATE_FILE}").read_text(encoding="utf-8"))
print(payload.get("capture_width", ${WIDTH:-640}))
PY
)"
  HEIGHT="$(python3 - <<PY
import json
from pathlib import Path
payload = json.loads(Path("${STATE_FILE}").read_text(encoding="utf-8"))
print(payload.get("capture_height", ${HEIGHT:-480}))
PY
)"
fi

python3 - <<PY
import json
from pathlib import Path

state_path = Path("${STATE_FILE}")
payload = json.loads(state_path.read_text(encoding="utf-8"))
payload.update(
    {
        "bridge_running": True,
        "bridge_started_at_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "bridge_framerate": int("${FRAMERATE}"),
        "gadget_video_device": "${GADGET_VIDEO_DEVICE}",
        "gadget_pixel_format": "YUYV",
    }
)
state_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
PY

exec ffmpeg \
  -hide_banner \
  -loglevel warning \
  -fflags nobuffer \
  -f v4l2 \
  -input_format rgb24 \
  -framerate "${FRAMERATE}" \
  -video_size "${WIDTH}x${HEIGHT}" \
  -i "${INPUT_VIDEO_DEVICE}" \
  -pix_fmt yuyv422 \
  -f v4l2 \
  "${GADGET_VIDEO_DEVICE}"
