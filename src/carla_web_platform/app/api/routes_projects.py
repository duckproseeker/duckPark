from __future__ import annotations

from functools import lru_cache
from typing import NoReturn

from fastapi import APIRouter, HTTPException

from app.api.schemas import ApiResponse
from app.core.config import get_settings
from app.core.errors import AppError, ConflictError, NotFoundError, ValidationError
from app.core.models import ProjectRecord
from app.orchestrator.queue import FileCommandQueue
from app.orchestrator.run_manager import RunManager
from app.platform.service import PlatformService
from app.storage.artifact_store import ArtifactStore
from app.storage.benchmark_definition_store import BenchmarkDefinitionStore
from app.storage.benchmark_task_store import BenchmarkTaskStore
from app.storage.gateway_store import GatewayStore
from app.storage.project_store import ProjectStore
from app.storage.report_store import ReportStore
from app.storage.run_store import RunStore
from app.utils.time_utils import to_iso8601

router = APIRouter(tags=["项目管理"])


def raise_platform_http_error(exc: AppError) -> NoReturn:
    detail = {"code": exc.code, "message": exc.message}
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=detail)
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=409, detail=detail)
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=422, detail=detail)
    raise HTTPException(status_code=500, detail=detail)


@lru_cache(maxsize=1)
def get_platform_service() -> PlatformService:
    settings = get_settings()
    return PlatformService(
        project_store=ProjectStore(settings.projects_root),
        benchmark_definition_store=BenchmarkDefinitionStore(
            settings.benchmark_definitions_root
        ),
        benchmark_task_store=BenchmarkTaskStore(settings.benchmark_tasks_root),
        report_store=ReportStore(settings.reports_root),
        run_store=RunStore(settings.runs_root),
        run_manager=RunManager(
            run_store=RunStore(settings.runs_root),
            artifact_store=ArtifactStore(settings.artifacts_root),
            command_queue=FileCommandQueue(settings.commands_root),
            gateway_store=GatewayStore(settings.gateways_root),
        ),
        artifact_store=ArtifactStore(settings.artifacts_root),
        gateway_store=GatewayStore(settings.gateways_root),
        sensor_profiles_root=settings.sensor_profiles_root,
        report_artifacts_root=settings.report_artifacts_root,
    )


def project_to_payload(project: ProjectRecord) -> dict[str, object]:
    return {
        "project_id": project.project_id,
        "name": project.name,
        "vendor": project.vendor,
        "processor": project.processor,
        "description": project.description,
        "benchmark_focus": project.benchmark_focus,
        "target_metrics": project.target_metrics,
        "input_modes": project.input_modes,
        "status": project.status.value,
        "created_at_utc": to_iso8601(project.created_at),
        "updated_at_utc": to_iso8601(project.updated_at),
    }


@router.get("/projects", response_model=ApiResponse, summary="查询项目列表")
def list_projects() -> ApiResponse:
    service = get_platform_service()
    return ApiResponse(
        success=True,
        data={"projects": [project_to_payload(item) for item in service.list_projects()]},
    )


@router.get("/projects/{project_id}", response_model=ApiResponse, summary="查询单个项目")
def get_project(project_id: str) -> ApiResponse:
    service = get_platform_service()
    try:
        project = service.get_project(project_id)
    except AppError as exc:
        raise_platform_http_error(exc)
    return ApiResponse(success=True, data=project_to_payload(project))
