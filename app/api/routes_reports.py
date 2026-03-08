from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.api.routes_projects import get_platform_service, raise_platform_http_error
from app.api.schemas import ApiResponse, ReportExportRequest
from app.core.errors import AppError
from app.core.models import ReportRecord
from app.utils.time_utils import to_iso8601

router = APIRouter(tags=["报告中心"])


def report_to_payload(report: ReportRecord) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "benchmark_task_id": report.benchmark_task_id,
        "project_id": report.project_id,
        "benchmark_definition_id": report.benchmark_definition_id,
        "dut_model": report.dut_model,
        "title": report.title,
        "status": report.status.value,
        "artifact_dir": report.artifact_dir,
        "json_path": report.json_path,
        "markdown_path": report.markdown_path,
        "summary": report.summary,
        "created_at_utc": to_iso8601(report.created_at),
        "updated_at_utc": to_iso8601(report.updated_at),
    }


@router.get("/reports", response_model=ApiResponse, summary="查询报告列表")
def list_reports(benchmark_task_id: str | None = Query(default=None)) -> ApiResponse:
    service = get_platform_service()
    try:
        reports = service.list_reports(benchmark_task_id=benchmark_task_id)
    except AppError as exc:
        raise_platform_http_error(exc)
    return ApiResponse(
        success=True,
        data={"reports": [report_to_payload(item) for item in reports]},
    )


@router.get("/reports/{report_id}", response_model=ApiResponse, summary="查询单个报告")
def get_report(report_id: str) -> ApiResponse:
    service = get_platform_service()
    try:
        report = service.get_report(report_id)
    except AppError as exc:
        raise_platform_http_error(exc)
    return ApiResponse(success=True, data=report_to_payload(report))


@router.post("/reports/export", response_model=ApiResponse, summary="导出基准任务报告")
def export_report(request: ReportExportRequest) -> ApiResponse:
    service = get_platform_service()
    try:
        report = service.export_report(request.benchmark_task_id)
    except AppError as exc:
        raise_platform_http_error(exc)
    return ApiResponse(success=True, data=report_to_payload(report))


@router.get(
    "/reports/{report_id}/download",
    response_class=FileResponse,
    include_in_schema=False,
)
def download_report(report_id: str, format: str = Query(default="json")) -> FileResponse:
    service = get_platform_service()
    try:
        report = service.get_report(report_id)
    except AppError as exc:
        raise_platform_http_error(exc)

    if format == "markdown":
        return FileResponse(
            report.markdown_path,
            media_type="text/markdown",
            filename=f"{report.report_id}.md",
        )
    return FileResponse(
        report.json_path,
        media_type="application/json",
        filename=f"{report.report_id}.json",
    )
