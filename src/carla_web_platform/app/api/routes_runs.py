from __future__ import annotations

from functools import lru_cache
from typing import Any, NoReturn

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import ApiResponse, CreateRunRequest
from app.core.config import get_settings
from app.core.errors import AppError, ConflictError, NotFoundError, ValidationError
from app.core.models import RunRecord
from app.orchestrator.queue import FileCommandQueue
from app.orchestrator.run_manager import RunManager
from app.storage.artifact_store import ArtifactStore
from app.storage.run_store import RunStore
from app.utils.time_utils import to_iso8601

router = APIRouter(tags=["运行管理"])


@lru_cache(maxsize=1)
def get_run_manager() -> RunManager:
    settings = get_settings()
    return RunManager(
        run_store=RunStore(settings.runs_root),
        artifact_store=ArtifactStore(settings.artifacts_root),
        command_queue=FileCommandQueue(settings.commands_root),
    )


@lru_cache(maxsize=1)
def get_artifact_store() -> ArtifactStore:
    settings = get_settings()
    return ArtifactStore(settings.artifacts_root)


def run_to_payload(run: RunRecord) -> dict[str, Any]:
    metrics = get_artifact_store().read_metrics(run.run_id) or {}
    created_at_utc = to_iso8601(run.created_at)
    updated_at_utc = to_iso8601(run.updated_at)
    started_at_utc = to_iso8601(run.started_at)
    ended_at_utc = to_iso8601(run.ended_at)

    return {
        "run_id": run.run_id,
        "status": run.status.value,
        "scenario_name": run.scenario_name,
        "map_name": run.map_name,
        "created_at_utc": created_at_utc,
        "updated_at_utc": updated_at_utc,
        "started_at_utc": started_at_utc,
        "ended_at_utc": ended_at_utc,
        # Backward compatible aliases.
        "created_time": created_at_utc,
        "updated_time": updated_at_utc,
        "start_time": started_at_utc,
        "end_time": ended_at_utc,
        "error_reason": run.error_reason,
        "stop_requested": run.stop_requested,
        "cancel_requested": run.cancel_requested,
        "artifact_dir": run.artifact_dir,
        "sim_time": metrics.get("sim_time"),
        "current_tick": metrics.get("current_tick"),
        "wall_elapsed_seconds": metrics.get("wall_time"),
        "spawned_actors_count": metrics.get("spawned_actors_count"),
    }


def raise_http_error(exc: AppError) -> NoReturn:
    detail = {"code": exc.code, "message": exc.message}
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=detail)
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=409, detail=detail)
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=422, detail=detail)
    raise HTTPException(status_code=500, detail=detail)


@router.post(
    "/runs",
    response_model=ApiResponse,
    summary="创建运行",
    description="根据 descriptor 创建一个 run，创建后状态为 CREATED。",
)
def create_run(request: CreateRunRequest) -> ApiResponse:
    manager = get_run_manager()
    try:
        run = manager.create_run(request.descriptor, request.descriptor_path)
    except AppError as exc:
        raise_http_error(exc)

    return ApiResponse(
        success=True, data={"run_id": run.run_id, "status": run.status.value}
    )


@router.post(
    "/runs/{run_id}/start",
    response_model=ApiResponse,
    summary="启动运行",
    description="将 run 放入执行队列，状态从 CREATED 变为 QUEUED。",
)
def start_run(run_id: str) -> ApiResponse:
    manager = get_run_manager()
    try:
        run = manager.start_run(run_id)
    except AppError as exc:
        raise_http_error(exc)

    return ApiResponse(success=True, data=run_to_payload(run))


@router.post(
    "/runs/{run_id}/stop",
    response_model=ApiResponse,
    summary="停止运行",
    description="请求停止运行。若尚未启动会直接取消；若运行中则进入 STOPPING。",
)
def stop_run(run_id: str) -> ApiResponse:
    manager = get_run_manager()
    try:
        run = manager.stop_run(run_id)
    except AppError as exc:
        raise_http_error(exc)

    return ApiResponse(success=True, data=run_to_payload(run))


@router.post(
    "/runs/{run_id}/cancel",
    response_model=ApiResponse,
    summary="取消运行",
    description="请求取消运行。语义与 stop 类似，但标记为取消请求。",
)
def cancel_run(run_id: str) -> ApiResponse:
    manager = get_run_manager()
    try:
        run = manager.cancel_run(run_id)
    except AppError as exc:
        raise_http_error(exc)

    return ApiResponse(success=True, data=run_to_payload(run))


@router.get(
    "/runs/{run_id}",
    response_model=ApiResponse,
    summary="查询单个运行",
    description="返回 run 当前状态、起止时间、错误原因和 artifact 路径。",
)
def get_run(run_id: str) -> ApiResponse:
    manager = get_run_manager()
    try:
        run = manager.get_run(run_id)
    except AppError as exc:
        raise_http_error(exc)

    return ApiResponse(success=True, data=run_to_payload(run))


@router.get(
    "/runs",
    response_model=ApiResponse,
    summary="查询运行列表",
    description="返回运行列表，可按状态过滤。",
)
def list_runs(
    status: str | None = Query(default=None, description="可选状态过滤值")
) -> ApiResponse:
    manager = get_run_manager()
    try:
        runs = manager.list_runs(status)
    except AppError as exc:
        raise_http_error(exc)

    return ApiResponse(success=True, data=[run_to_payload(run) for run in runs])


@router.get(
    "/runs/{run_id}/events",
    response_model=ApiResponse,
    summary="查询运行事件",
    description="返回该 run 的 events.jsonl 事件流。",
)
def get_run_events(run_id: str) -> ApiResponse:
    manager = get_run_manager()
    try:
        events = manager.get_events(run_id)
    except AppError as exc:
        raise_http_error(exc)

    return ApiResponse(success=True, data=events)
