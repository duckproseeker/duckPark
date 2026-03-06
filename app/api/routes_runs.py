from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import ApiResponse, CreateRunRequest
from app.core.config import get_settings
from app.core.errors import AppError, ConflictError, NotFoundError, ValidationError
from app.orchestrator.queue import FileCommandQueue
from app.orchestrator.run_manager import RunManager
from app.storage.artifact_store import ArtifactStore
from app.storage.run_store import RunStore
from app.utils.time_utils import to_iso8601

router = APIRouter()


@lru_cache(maxsize=1)
def get_run_manager() -> RunManager:
    settings = get_settings()
    return RunManager(
        run_store=RunStore(settings.runs_root),
        artifact_store=ArtifactStore(settings.artifacts_root),
        command_queue=FileCommandQueue(settings.commands_root),
    )


def _run_to_dict(run: object) -> dict:
    return {
        "run_id": run.run_id,
        "status": run.status.value,
        "scenario_name": run.scenario_name,
        "map_name": run.map_name,
        "start_time": to_iso8601(run.started_at),
        "end_time": to_iso8601(run.ended_at),
        "error_reason": run.error_reason,
        "stop_requested": run.stop_requested,
        "cancel_requested": run.cancel_requested,
        "artifact_dir": run.artifact_dir,
    }


def _raise_http_error(exc: AppError) -> None:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail={"code": exc.code, "message": exc.message})
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=409, detail={"code": exc.code, "message": exc.message})
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": exc.message})
    raise HTTPException(status_code=500, detail={"code": exc.code, "message": exc.message})


@router.post("/runs", response_model=ApiResponse)
def create_run(request: CreateRunRequest) -> ApiResponse:
    manager = get_run_manager()
    try:
        run = manager.create_run(request.descriptor, request.descriptor_path)
    except AppError as exc:
        _raise_http_error(exc)

    return ApiResponse(
        success=True,
        data={"run_id": run.run_id, "status": run.status.value},
    )


@router.post("/runs/{run_id}/start", response_model=ApiResponse)
def start_run(run_id: str) -> ApiResponse:
    manager = get_run_manager()
    try:
        run = manager.start_run(run_id)
    except AppError as exc:
        _raise_http_error(exc)

    return ApiResponse(success=True, data=_run_to_dict(run))


@router.post("/runs/{run_id}/stop", response_model=ApiResponse)
def stop_run(run_id: str) -> ApiResponse:
    manager = get_run_manager()
    try:
        run = manager.stop_run(run_id)
    except AppError as exc:
        _raise_http_error(exc)

    return ApiResponse(success=True, data=_run_to_dict(run))


@router.post("/runs/{run_id}/cancel", response_model=ApiResponse)
def cancel_run(run_id: str) -> ApiResponse:
    manager = get_run_manager()
    try:
        run = manager.cancel_run(run_id)
    except AppError as exc:
        _raise_http_error(exc)

    return ApiResponse(success=True, data=_run_to_dict(run))


@router.get("/runs/{run_id}", response_model=ApiResponse)
def get_run(run_id: str) -> ApiResponse:
    manager = get_run_manager()
    try:
        run = manager.get_run(run_id)
    except AppError as exc:
        _raise_http_error(exc)

    return ApiResponse(success=True, data=_run_to_dict(run))


@router.get("/runs", response_model=ApiResponse)
def list_runs(status: str | None = Query(default=None)) -> ApiResponse:
    manager = get_run_manager()
    try:
        runs = manager.list_runs(status)
    except AppError as exc:
        _raise_http_error(exc)

    return ApiResponse(success=True, data=[_run_to_dict(run) for run in runs])


@router.get("/runs/{run_id}/events", response_model=ApiResponse)
def get_run_events(run_id: str) -> ApiResponse:
    manager = get_run_manager()
    try:
        events = manager.get_events(run_id)
    except AppError as exc:
        _raise_http_error(exc)

    return ApiResponse(success=True, data=events)
