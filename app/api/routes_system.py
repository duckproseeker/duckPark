from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from app.api.schemas import ApiResponse
from app.core.config import get_settings
from app.core.models import CaptureStatus, GatewayStatus, RunStatus
from app.orchestrator.queue import FileCommandQueue
from app.storage.capture_store import CaptureStore
from app.storage.executor_store import ExecutorStore
from app.storage.gateway_store import GatewayStore
from app.storage.run_store import RunStore

router = APIRouter(tags=["系统"])


@lru_cache(maxsize=1)
def get_system_dependencies() -> dict[str, Any]:
    settings = get_settings()
    return {
        "queue": FileCommandQueue(settings.commands_root),
        "executor_store": ExecutorStore(settings.executor_root),
        "run_store": RunStore(settings.runs_root),
        "capture_store": CaptureStore(settings.captures_root),
        "gateway_store": GatewayStore(settings.gateways_root),
        "frontend_dist": Path(settings.runs_root).parents[1] / "frontend" / "dist" / "index.html",
    }


def _executor_payload(deps: dict[str, Any]) -> dict[str, Any]:
    heartbeat = deps["executor_store"].read_heartbeat()
    pending_commands = deps["queue"].count_pending()
    if heartbeat is None:
        return {
            "alive": False,
            "status": "OFFLINE",
            "active_run_id": None,
            "last_command_run_id": None,
            "last_heartbeat_at_utc": None,
            "heartbeat_age_seconds": None,
            "pending_commands": pending_commands,
            "warning": "executor heartbeat missing; queued runs will not start",
        }

    last_heartbeat_text = heartbeat.get("updated_at_utc")
    last_heartbeat_at = None
    if isinstance(last_heartbeat_text, str):
        last_heartbeat_at = datetime.fromisoformat(last_heartbeat_text)
    heartbeat_age_seconds = None
    alive = False
    if last_heartbeat_at is not None:
        heartbeat_age_seconds = (
            datetime.now(timezone.utc) - last_heartbeat_at.astimezone(timezone.utc)
        ).total_seconds()
        alive = heartbeat_age_seconds <= 5.0

    status = str(heartbeat.get("status", "UNKNOWN")).upper()
    if not alive:
        status = "OFFLINE"

    return {
        "alive": alive,
        "status": status,
        "active_run_id": heartbeat.get("active_run_id"),
        "last_command_run_id": heartbeat.get("last_command_run_id"),
        "last_heartbeat_at_utc": last_heartbeat_text,
        "heartbeat_age_seconds": heartbeat_age_seconds,
        "pending_commands": pending_commands,
        "warning": None if alive else "executor heartbeat stale; queued runs are blocked",
    }


@router.get("/system/status", response_model=ApiResponse, summary="查询平台状态")
def get_system_status() -> ApiResponse:
    deps = get_system_dependencies()
    runs = deps["run_store"].list()
    captures = deps["capture_store"].list()
    gateways = deps["gateway_store"].list()
    executor = _executor_payload(deps)

    run_status_counts = {status.value: 0 for status in RunStatus}
    for run in runs:
        run_status_counts[run.status.value] = run_status_counts.get(run.status.value, 0) + 1

    capture_status_counts = {status.value: 0 for status in CaptureStatus}
    for capture in captures:
        capture_status_counts[capture.status.value] = capture_status_counts.get(capture.status.value, 0) + 1

    gateway_status_counts = {status.value: 0 for status in GatewayStatus}
    for gateway in gateways:
        gateway_status_counts[gateway.status.value] = gateway_status_counts.get(gateway.status.value, 0) + 1

    return ApiResponse(
        success=True,
        data={
            "api": {"status": "ok"},
            "executor": executor,
            "counts": {
                "runs": run_status_counts,
                "captures": capture_status_counts,
                "gateways": gateway_status_counts,
            },
            "totals": {
                "runs": len(runs),
                "captures": len(captures),
                "gateways": len(gateways),
            },
            "capture_observability": {
                "running_capture_ids": [
                    item.capture_id for item in captures if item.status == CaptureStatus.RUNNING
                ],
                "completed_capture_ids": [
                    item.capture_id for item in captures if item.status == CaptureStatus.COMPLETED
                ],
                "latest_capture_id": captures[0].capture_id if captures else None,
            },
            "frontend": {
                "bundle_present": deps["frontend_dist"].exists(),
            },
        },
    )
