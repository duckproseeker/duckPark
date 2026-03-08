from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.routes_projects import get_platform_service, raise_platform_http_error
from app.api.schemas import ApiResponse, CreateBenchmarkTaskRequest
from app.core.errors import AppError
from app.core.models import BenchmarkDefinitionRecord, BenchmarkTaskRecord
from app.utils.time_utils import to_iso8601

router = APIRouter(tags=["基准任务"])


def benchmark_definition_to_payload(
    definition: BenchmarkDefinitionRecord,
) -> dict[str, object]:
    return {
        "benchmark_definition_id": definition.benchmark_definition_id,
        "name": definition.name,
        "description": definition.description,
        "focus_metrics": definition.focus_metrics,
        "cadence": definition.cadence,
        "report_shape": definition.report_shape,
        "project_ids": definition.project_ids,
        "default_evaluation_profile_name": definition.default_evaluation_profile_name,
        "created_at_utc": to_iso8601(definition.created_at),
        "updated_at_utc": to_iso8601(definition.updated_at),
    }


def benchmark_task_to_payload(task: BenchmarkTaskRecord) -> dict[str, object]:
    return {
        "benchmark_task_id": task.benchmark_task_id,
        "project_id": task.project_id,
        "project_name": task.project_name,
        "dut_model": task.dut_model,
        "benchmark_definition_id": task.benchmark_definition_id,
        "benchmark_name": task.benchmark_name,
        "status": task.status.value,
        "planned_run_count": task.planned_run_count,
        "counts_by_status": task.counts_by_status,
        "run_ids": task.run_ids,
        "scenario_matrix": [item.model_dump(mode="json") for item in task.scenario_matrix],
        "hil_config": task.hil_config,
        "evaluation_profile_name": task.evaluation_profile_name,
        "auto_start": task.auto_start,
        "summary": task.summary,
        "created_at_utc": to_iso8601(task.created_at),
        "updated_at_utc": to_iso8601(task.updated_at),
        "started_at_utc": to_iso8601(task.started_at),
        "ended_at_utc": to_iso8601(task.ended_at),
    }


@router.get(
    "/benchmark-definitions",
    response_model=ApiResponse,
    summary="查询基准定义列表",
)
def list_benchmark_definitions() -> ApiResponse:
    service = get_platform_service()
    return ApiResponse(
        success=True,
        data={
            "definitions": [
                benchmark_definition_to_payload(item)
                for item in service.list_benchmark_definitions()
            ]
        },
    )


@router.get(
    "/benchmark-definitions/{benchmark_definition_id}",
    response_model=ApiResponse,
    summary="查询单个基准定义",
)
def get_benchmark_definition(benchmark_definition_id: str) -> ApiResponse:
    service = get_platform_service()
    try:
        definition = service.get_benchmark_definition(benchmark_definition_id)
    except AppError as exc:
        raise_platform_http_error(exc)
    return ApiResponse(success=True, data=benchmark_definition_to_payload(definition))


@router.get("/benchmark-tasks", response_model=ApiResponse, summary="查询基准任务列表")
def list_benchmark_tasks(
    project_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> ApiResponse:
    service = get_platform_service()
    try:
        tasks = service.list_benchmark_tasks(project_id=project_id, status=status)
    except AppError as exc:
        raise_platform_http_error(exc)

    return ApiResponse(
        success=True,
        data={"tasks": [benchmark_task_to_payload(item) for item in tasks]},
    )


@router.get(
    "/benchmark-tasks/{benchmark_task_id}",
    response_model=ApiResponse,
    summary="查询单个基准任务",
)
def get_benchmark_task(benchmark_task_id: str) -> ApiResponse:
    service = get_platform_service()
    try:
        task = service.get_benchmark_task(benchmark_task_id)
    except AppError as exc:
        raise_platform_http_error(exc)
    return ApiResponse(success=True, data=benchmark_task_to_payload(task))


@router.post("/benchmark-tasks", response_model=ApiResponse, summary="创建基准任务")
def create_benchmark_task(request: CreateBenchmarkTaskRequest) -> ApiResponse:
    service = get_platform_service()
    try:
        task = service.create_benchmark_task(
            project_id=request.project_id,
            benchmark_definition_id=request.benchmark_definition_id,
            dut_model=request.dut_model,
            scenario_matrix=[
                item.model_dump(mode="json") for item in request.scenario_matrix
            ],
            hil_config=(
                request.hil_config.model_dump(mode="json")
                if request.hil_config is not None
                else None
            ),
            evaluation_profile_name=request.evaluation_profile_name,
            auto_start=request.auto_start,
        )
    except AppError as exc:
        raise_platform_http_error(exc)

    return ApiResponse(success=True, data=benchmark_task_to_payload(task))
