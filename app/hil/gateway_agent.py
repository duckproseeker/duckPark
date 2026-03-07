from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, parse, request

AGENT_VERSION = "0.1.0"
DEFAULT_STATE_DIR_NAME = "pi_gateway"


@dataclass(frozen=True)
class GatewayAgentSettings:
    api_base_url: str
    gateway_id: str
    gateway_name: str
    input_video_device: str
    heartbeat_interval_seconds: float
    api_timeout_seconds: float
    state_dir: Path
    gadget_state_file: Path
    bridge_state_file: Path
    current_run_id_file: Path
    agent_version: str
    video_input_modes: tuple[str, ...]
    dut_output_modes: tuple[str, ...]
    result_ingest_modes: tuple[str, ...]
    once: bool = False


def parse_args(argv: list[str] | None = None) -> GatewayAgentSettings:
    parser = argparse.ArgumentParser(description="DuckPark Pi gateway agent")
    parser.add_argument("--api-base-url", default=os.getenv("PI_GATEWAY_API_BASE_URL"))
    parser.add_argument("--gateway-id", default=os.getenv("PI_GATEWAY_ID"))
    parser.add_argument("--gateway-name", default=os.getenv("PI_GATEWAY_NAME"))
    parser.add_argument(
        "--input-video-device",
        default=os.getenv("PI_GATEWAY_INPUT_VIDEO_DEVICE", "/dev/video0"),
    )
    parser.add_argument(
        "--heartbeat-interval",
        type=float,
        default=float(os.getenv("PI_GATEWAY_HEARTBEAT_INTERVAL_SECONDS", "5")),
    )
    parser.add_argument(
        "--api-timeout",
        type=float,
        default=float(os.getenv("PI_GATEWAY_API_TIMEOUT_SECONDS", "3")),
    )
    parser.add_argument(
        "--state-dir",
        default=os.getenv("PI_GATEWAY_STATE_DIR"),
    )
    parser.add_argument(
        "--agent-version",
        default=os.getenv("PI_GATEWAY_AGENT_VERSION", AGENT_VERSION),
    )
    parser.add_argument(
        "--video-input-modes",
        default=os.getenv("PI_GATEWAY_VIDEO_INPUT_MODES", "hdmi_x1301,frame_stream"),
    )
    parser.add_argument(
        "--dut-output-modes",
        default=os.getenv("PI_GATEWAY_DUT_OUTPUT_MODES", "uvc_gadget"),
    )
    parser.add_argument(
        "--result-ingest-modes",
        default=os.getenv("PI_GATEWAY_RESULT_INGEST_MODES", "http_push"),
    )
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)

    if not args.api_base_url:
        parser.error("--api-base-url is required")
    if not args.gateway_id:
        parser.error("--gateway-id is required")
    if not args.gateway_name:
        parser.error("--gateway-name is required")

    project_root = Path(__file__).resolve().parents[2]
    default_state_dir = project_root / "run_data" / DEFAULT_STATE_DIR_NAME
    state_dir = Path(args.state_dir or default_state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)

    return GatewayAgentSettings(
        api_base_url=args.api_base_url.rstrip("/"),
        gateway_id=args.gateway_id.strip(),
        gateway_name=args.gateway_name.strip(),
        input_video_device=args.input_video_device.strip(),
        heartbeat_interval_seconds=max(args.heartbeat_interval, 1.0),
        api_timeout_seconds=max(args.api_timeout, 1.0),
        state_dir=state_dir,
        gadget_state_file=state_dir / "gadget_state.json",
        bridge_state_file=state_dir / "bridge_state.json",
        current_run_id_file=state_dir / "current_run_id",
        agent_version=args.agent_version.strip(),
        video_input_modes=parse_csv(args.video_input_modes),
        dut_output_modes=parse_csv(args.dut_output_modes),
        result_ingest_modes=parse_csv(args.result_ingest_modes),
        once=args.once,
    )


def parse_csv(raw_value: str | None) -> tuple[str, ...]:
    if not raw_value:
        return tuple()
    return tuple(item.strip() for item in raw_value.split(",") if item.strip())


def now_utc_iso8601() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def read_text_file(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def is_module_loaded(module_name: str) -> bool:
    try:
        with Path("/proc/modules").open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.split(" ", 1)[0] == module_name:
                    return True
    except OSError:
        return False
    return False


def list_udc_names() -> list[str]:
    udc_root = Path("/sys/class/udc")
    if not udc_root.exists():
        return []
    return sorted(entry.name for entry in udc_root.iterdir())


def get_udc_state(udc_name: str | None) -> str | None:
    if not udc_name:
        return None
    state_path = Path("/sys/class/udc") / udc_name / "state"
    if not state_path.exists():
        return None
    try:
        return state_path.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def run_command(command: list[str], timeout_seconds: float = 2.0) -> str | None:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def find_gadget_video_device() -> str | None:
    output = run_command(["v4l2-ctl", "--list-devices"])
    if not output:
        return None

    current_block: str | None = None
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
                return device
    return None


def probe_v4l2_device(device_path: str, prefix: str) -> dict[str, Any]:
    output = run_command(["v4l2-ctl", "-d", device_path, "--all"])
    if not output:
        return {}

    metrics: dict[str, Any] = {}
    card_type = re.search(r"Card type\s+:\s+(.+)", output)
    width_height = re.search(r"Width/Height\s+:\s+(\d+)/(\d+)", output)
    pixel_format = re.search(r"Pixel Format\s+:\s+'([^']+)'\s+\((.+)\)", output)

    if card_type:
        metrics[f"{prefix}_card_type"] = card_type.group(1).strip()
    if width_height:
        metrics[f"{prefix}_width"] = int(width_height.group(1))
        metrics[f"{prefix}_height"] = int(width_height.group(2))
    if pixel_format:
        metrics[f"{prefix}_pixel_format"] = pixel_format.group(1).strip()
        metrics[f"{prefix}_pixel_format_desc"] = pixel_format.group(2).strip()
    return metrics


def detect_local_address(api_base_url: str) -> str | None:
    parsed = parse.urlparse(api_base_url)
    if not parsed.hostname:
        return None
    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme == "https" else 80

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect((parsed.hostname, port))
            address = sock.getsockname()[0]
    except OSError:
        return None
    return address


def read_platform_model() -> str | None:
    model_path = Path("/proc/device-tree/model")
    if not model_path.exists():
        return None
    try:
        return model_path.read_text(encoding="utf-8", errors="ignore").replace("\x00", "").strip()
    except OSError:
        return None


def build_register_payload(
    settings: GatewayAgentSettings, address: str | None, metrics: dict[str, Any]
) -> dict[str, Any]:
    capabilities: dict[str, Any] = {
        "video_input_modes": list(settings.video_input_modes),
        "dut_output_modes": list(settings.dut_output_modes),
        "result_ingest_modes": list(settings.result_ingest_modes),
    }
    platform_model = read_platform_model()
    if platform_model:
        capabilities["platform_model"] = platform_model
    if metrics.get("gadget_driver"):
        capabilities["gadget_driver"] = metrics["gadget_driver"]

    return {
        "gateway_id": settings.gateway_id,
        "name": settings.gateway_name,
        "capabilities": capabilities,
        "agent_version": settings.agent_version,
        "address": address,
    }


def determine_gateway_status(metrics: dict[str, Any], current_run_id: str | None) -> str:
    if not metrics.get("udc_present", False):
        return "ERROR"
    if not metrics.get("input_device_exists", False):
        return "ERROR"
    if not metrics.get("gadget_driver_loaded", False):
        return "ERROR"
    if not metrics.get("gadget_video_device_exists", False):
        return "ERROR"
    if current_run_id:
        return "BUSY"
    return "READY"


def collect_gateway_metrics(settings: GatewayAgentSettings) -> tuple[dict[str, Any], str | None]:
    udc_names = list_udc_names()
    udc_name = udc_names[0] if udc_names else None
    udc_state = get_udc_state(udc_name)

    gadget_state = read_json_file(settings.gadget_state_file)
    bridge_state = read_json_file(settings.bridge_state_file)
    current_run_id = read_text_file(settings.current_run_id_file)

    gadget_video_device = (
        gadget_state.get("gadget_video_device")
        or bridge_state.get("gadget_video_device")
        or find_gadget_video_device()
    )

    metrics: dict[str, Any] = {
        "captured_at_utc": now_utc_iso8601(),
        "udc_present": bool(udc_name),
        "udc_name": udc_name,
        "udc_state": udc_state or "missing",
        "host_connected": bool(udc_state and udc_state != "not attached"),
        "input_device": settings.input_video_device,
        "input_device_exists": Path(settings.input_video_device).exists(),
        "gadget_driver": gadget_state.get("gadget_driver", "g_webcam"),
        "gadget_driver_loaded": is_module_loaded(
            str(gadget_state.get("gadget_driver", "g_webcam"))
        ),
        "gadget_video_device": gadget_video_device,
        "gadget_video_device_exists": bool(
            gadget_video_device and Path(gadget_video_device).exists()
        ),
    }
    metrics.update(probe_v4l2_device(settings.input_video_device, "input"))
    if gadget_video_device:
        metrics.update(probe_v4l2_device(gadget_video_device, "gadget"))
    metrics.update(gadget_state)
    metrics.update(bridge_state)
    return metrics, current_run_id


def post_json(
    api_base_url: str,
    route: str,
    payload: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=f"{api_base_url}{route}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            response_text = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(
            f"HTTP {exc.code} calling {route}: {detail or exc.reason}"
        ) from exc
    except error.URLError as exc:
        raise RuntimeError(f"Network error calling {route}: {exc.reason}") from exc

    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON from {route}: {response_text}") from exc

    if not parsed.get("success", False):
        raise RuntimeError(f"Platform rejected {route}: {parsed}")
    return parsed


def log(message: str) -> None:
    sys.stdout.write(f"{now_utc_iso8601()} {message}\n")
    sys.stdout.flush()


def run_agent(settings: GatewayAgentSettings) -> int:
    registered = False
    address = detect_local_address(settings.api_base_url)
    log(
        "gateway-agent start "
        f"gateway_id={settings.gateway_id} api={settings.api_base_url} input={settings.input_video_device}"
    )

    while True:
        metrics, current_run_id = collect_gateway_metrics(settings)
        status = determine_gateway_status(metrics, current_run_id)

        try:
            if not registered:
                register_payload = build_register_payload(settings, address, metrics)
                post_json(
                    settings.api_base_url,
                    "/gateways/register",
                    register_payload,
                    settings.api_timeout_seconds,
                )
                registered = True
                log(f"gateway registered gateway_id={settings.gateway_id}")

            heartbeat_payload = {
                "status": status,
                "metrics": metrics,
                "current_run_id": current_run_id,
            }
            post_json(
                settings.api_base_url,
                f"/gateways/{settings.gateway_id}/heartbeat",
                heartbeat_payload,
                settings.api_timeout_seconds,
            )
            log(
                "heartbeat sent "
                f"status={status} udc_state={metrics.get('udc_state')} "
                f"gadget={metrics.get('gadget_video_device') or '-'}"
            )
        except RuntimeError as exc:
            registered = False
            log(f"gateway-agent error: {exc}")

        if settings.once:
            return 0
        time.sleep(settings.heartbeat_interval_seconds)


def main(argv: list[str] | None = None) -> int:
    settings = parse_args(argv)
    return run_agent(settings)


if __name__ == "__main__":
    raise SystemExit(main())
