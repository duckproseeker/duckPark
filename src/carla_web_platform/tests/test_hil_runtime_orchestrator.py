from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from app.core.models import EventLevel
from app.executor.hil_runtime_orchestrator import HilRuntimeOrchestrator, HilRuntimeStep


def test_stop_pipeline_preserves_host_carla_for_manual_stop_demo(tmp_path: Path) -> None:
    recorded_events: list[tuple[str, str]] = []

    orchestrator = HilRuntimeOrchestrator(
        SimpleNamespace(
            hil_orchestration_enabled=True,
            hil_runtime_root=tmp_path,
            project_root=tmp_path,
            hil_platform_base_url=None,
            api_port=8000,
        ),
        event_callback=lambda run_id, event_type, message, **kwargs: recorded_events.append(
            (event_type, message)
        ),
    )

    run = SimpleNamespace(
        hil_config={"mode": "camera_open_loop"},
        scenario_name="town10_autonomous_demo",
        map_name="Town10HD_Opt",
    )
    descriptor = SimpleNamespace(
        termination=SimpleNamespace(timeout_seconds=86400, success_condition="manual_stop"),
        sync=SimpleNamespace(fixed_delta_seconds=1.0 / 30.0),
        weather=SimpleNamespace(preset="ClearNoon"),
    )

    orchestrator.stop_pipeline(
        "run_test",
        run,
        descriptor,
        [
            HilRuntimeStep(
                step_id="host_carla",
                label="Host CARLA",
                start_command="echo start",
                stop_command="echo stop",
            )
        ],
    )

    assert recorded_events == [
        ("HIL_RUNTIME_STEP_STOP_SKIPPED", "Host CARLA 按当前演示策略保留运行态")
    ]


def test_start_pipeline_skips_pi_step_when_gateway_unreachable(
    monkeypatch, tmp_path: Path
) -> None:
    recorded_events: list[tuple[str, str, str, dict[str, object], EventLevel]] = []

    orchestrator = HilRuntimeOrchestrator(
        SimpleNamespace(
            hil_orchestration_enabled=True,
            hil_runtime_root=tmp_path,
            hil_runtime_workdir=tmp_path,
            project_root=tmp_path,
            hil_platform_base_url=None,
            api_port=8000,
            hil_command_timeout_seconds=1.0,
            hil_pi_start_command="echo start",
            hil_pi_stop_command="echo stop",
            duckpark_pi_host="192.168.110.236",
            duckpark_pi_user="kavin",
            duckpark_pi_port=22,
        ),
        event_callback=lambda run_id, event_type, message, **kwargs: recorded_events.append(
            (
                run_id,
                event_type,
                message,
                kwargs.get("payload", {}),
                kwargs.get("level", EventLevel.INFO),
            )
        ),
    )

    monkeypatch.setattr(
        "app.executor.hil_runtime_orchestrator.probe_pi_gateway",
        lambda settings: {
            "status": "OFFLINE",
            "configured": True,
            "reachable": False,
            "host": "192.168.110.236",
            "user": "kavin",
            "port": 22,
            "start_command_configured": True,
            "stop_command_configured": True,
            "last_probe_at_utc": "2026-03-23T00:00:00+00:00",
            "warning": "No route to host",
        },
    )
    monkeypatch.setattr(
        orchestrator,
        "_resolve_steps",
        lambda: [
            HilRuntimeStep(
                step_id="pi_pipeline",
                label="Pi HDMI RTP Pipeline",
                start_command="echo start",
                stop_command="echo stop",
            )
        ],
    )

    run = SimpleNamespace(
        hil_config={"mode": "camera_open_loop"},
        scenario_name="town10_autonomous_demo",
        map_name="Town10HD_Opt",
    )
    descriptor = SimpleNamespace(
        termination=SimpleNamespace(timeout_seconds=86400, success_condition="manual_stop"),
        sync=SimpleNamespace(fixed_delta_seconds=1.0 / 30.0),
        weather=SimpleNamespace(preset="ClearNoon"),
    )

    started_steps = orchestrator.start_pipeline("run_test", run, descriptor)

    assert started_steps == []
    assert recorded_events == [
        (
            "run_test",
            "HIL_RUNTIME_STEP_SKIPPED",
            "树莓派网关当前不可达，已跳过虚拟传感器注入链路",
            {
                "step_id": "pi_pipeline",
                "gateway_status": {
                    "status": "OFFLINE",
                    "configured": True,
                    "reachable": False,
                    "host": "192.168.110.236",
                    "user": "kavin",
                    "port": 22,
                    "start_command_configured": True,
                    "stop_command_configured": True,
                    "last_probe_at_utc": "2026-03-23T00:00:00+00:00",
                    "warning": "No route to host",
                },
            },
            EventLevel.WARNING,
        )
    ]
