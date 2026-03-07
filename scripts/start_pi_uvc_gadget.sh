#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)
STATE_DIR="${PI_GATEWAY_STATE_DIR:-${PROJECT_ROOT}/run_data/pi_gateway}"
STATE_FILE="${STATE_DIR}/gadget_state.json"
VENDOR_ID="${PI_GATEWAY_USB_VENDOR_ID:-0x1d6b}"
PRODUCT_ID="${PI_GATEWAY_USB_PRODUCT_ID:-0x0102}"
MANUFACTURER="${PI_GATEWAY_USB_MANUFACTURER:-DuckPark}"
PRODUCT_NAME="${PI_GATEWAY_USB_PRODUCT_NAME:-DuckPark UVC}"
SERIAL_NUMBER="${PI_GATEWAY_USB_SERIAL:-DUCKPARKPI5}"

mkdir -p "${STATE_DIR}"

find_gadget_video_device() {
  python3 - <<'PY'
import subprocess

try:
    output = subprocess.run(
        ["v4l2-ctl", "--list-devices"],
        capture_output=True,
        check=False,
        text=True,
        timeout=2.0,
    ).stdout
except (FileNotFoundError, subprocess.TimeoutExpired):
    raise SystemExit(1)

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

if [[ ! -d /sys/class/udc ]] || [[ -z "$(ls -A /sys/class/udc 2>/dev/null || true)" ]]; then
  cat >&2 <<'EOF'
未检测到 UDC。

请先确认树莓派 5 已启用 USB peripheral 模式：
  [pi5]
  dtoverlay=dwc2,dr_mode=peripheral

并且重启后 /sys/class/udc 下能看到控制器节点。
EOF
  exit 1
fi

sudo modprobe -r g_webcam >/dev/null 2>&1 || true
sudo modprobe -r g_ether usb_f_rndis u_ether >/dev/null 2>&1 || true
sudo modprobe libcomposite
sudo modprobe g_webcam \
  idVendor="${VENDOR_ID}" \
  idProduct="${PRODUCT_ID}" \
  iManufacturer="${MANUFACTURER}" \
  iProduct="${PRODUCT_NAME}" \
  iSerialNumber="${SERIAL_NUMBER}"

GADGET_DEVICE=""
for _ in $(seq 1 20); do
  GADGET_DEVICE="$(find_gadget_video_device || true)"
  if [[ -n "${GADGET_DEVICE}" ]]; then
    break
  fi
  sleep 1
done

if [[ -z "${GADGET_DEVICE}" ]]; then
  echo "UVC gadget 已加载，但未找到对应的 /dev/video 节点" >&2
  exit 1
fi

UDC_NAME="$(ls /sys/class/udc | head -n1)"
UDC_STATE="$(cat "/sys/class/udc/${UDC_NAME}/state" 2>/dev/null || echo unknown)"

cat > "${STATE_FILE}" <<EOF
{
  "started_at_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "gadget_driver": "g_webcam",
  "gadget_video_device": "${GADGET_DEVICE}",
  "udc_name": "${UDC_NAME}",
  "udc_state": "${UDC_STATE}",
  "usb_vendor_id": "${VENDOR_ID}",
  "usb_product_id": "${PRODUCT_ID}"
}
EOF

echo "UVC gadget ready: ${GADGET_DEVICE} (UDC=${UDC_NAME}, state=${UDC_STATE})"
