from __future__ import annotations

from pathlib import Path

from app.hil.gateway_agent import (
    GatewayAgentSettings,
    build_register_payload,
    determine_gateway_status,
    parse_csv,
    parse_tc358743_status,
)


def make_settings(tmp_path: Path) -> GatewayAgentSettings:
    state_dir = tmp_path / "pi_gateway"
    state_dir.mkdir()
    return GatewayAgentSettings(
        api_base_url="http://127.0.0.1:8000",
        gateway_id="rpi5-x1301-01",
        gateway_name="bench-a",
        input_video_device="/dev/video0",
        media_device="/dev/media0",
        hdmi_status_device="/dev/v4l-subdev2",
        heartbeat_interval_seconds=5.0,
        api_timeout_seconds=3.0,
        state_dir=state_dir,
        gadget_state_file=state_dir / "gadget_state.json",
        bridge_state_file=state_dir / "bridge_state.json",
        current_run_id_file=state_dir / "current_run_id",
        agent_version="0.1.0",
        video_input_modes=("hdmi_x1301", "frame_stream"),
        dut_output_modes=("uvc_gadget",),
        result_ingest_modes=("http_push",),
        once=False,
    )


def test_parse_csv_trims_empty_items() -> None:
    assert parse_csv(" hdmi_x1301, frame_stream ,, ") == ("hdmi_x1301", "frame_stream")


def test_determine_gateway_status_ready_and_busy() -> None:
    metrics = {
        "udc_present": True,
        "input_device_exists": True,
        "gadget_driver_loaded": True,
        "gadget_video_device_exists": True,
    }
    assert determine_gateway_status(metrics, None) == "READY"
    assert determine_gateway_status(metrics, "run_001") == "BUSY"


def test_determine_gateway_status_error_when_gadget_missing() -> None:
    metrics = {
        "udc_present": True,
        "input_device_exists": True,
        "gadget_driver_loaded": False,
        "gadget_video_device_exists": False,
    }
    assert determine_gateway_status(metrics, None) == "ERROR"


def test_build_register_payload_contains_capabilities(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    payload = build_register_payload(
        settings,
        address="192.168.110.236",
        metrics={"gadget_driver": "g_webcam"},
    )

    assert payload["gateway_id"] == "rpi5-x1301-01"
    assert payload["address"] == "192.168.110.236"
    assert payload["capabilities"]["video_input_modes"] == ["hdmi_x1301", "frame_stream"]
    assert payload["capabilities"]["dut_output_modes"] == ["uvc_gadget"]
    assert payload["capabilities"]["result_ingest_modes"] == ["http_push"]
    assert payload["capabilities"]["gadget_driver"] == "g_webcam"


def test_parse_tc358743_status_extracts_signal_flags() -> None:
    status_output = """
    tc358743 11-000f: Cable detected (+5V power): yes
    tc358743 11-000f: DDC lines enabled: yes
    tc358743 11-000f: Hotplug enabled: yes
    tc358743 11-000f: TMDS signal detected: no
    tc358743 11-000f: Stable sync signal: no
    tc358743 11-000f: PHY PLL locked: no
    tc358743 11-000f: PHY DE detected: no
    tc358743 11-000f: No video detected
    tc358743 11-000f: Configured format: 640x480p59.94 (800x525)
    tc358743 11-000f: Input color space: RGB full range
    """

    metrics = parse_tc358743_status(status_output)

    assert metrics["hdmi_cable_detected"] is True
    assert metrics["hdmi_hotplug_enabled"] is True
    assert metrics["hdmi_tmds_signal_detected"] is False
    assert metrics["hdmi_stable_sync_signal"] is False
    assert metrics["hdmi_video_detected"] is False
    assert metrics["hdmi_configured_format"] == "640x480p59.94 (800x525)"
    assert metrics["hdmi_input_color_space"] == "RGB full range"
