from __future__ import annotations

import asyncio
import base64
from functools import lru_cache
from typing import Any, NoReturn

from fastapi import APIRouter, HTTPException, Query, Response, WebSocket, WebSocketDisconnect

from app.api.schemas import (
    CreateRunRequest,
    RunCreatePayload,
    RunCreateResponse,
    RunEnvironmentStatePayload,
    RunEnvironmentStateResponse,
    RunEnvironmentUpdateRequest,
    RunEventListResponse,
    RunEventPayload,
    RunListResponse,
    RunPayload,
    RunResponse,
    RunViewerInfoPayload,
    RunViewerInfoResponse,
)
from app.core.config import get_settings
from app.core.errors import AppError, ConflictError, NotFoundError, ValidationError
from app.core.models import RunRecord, RunStatus
from app.orchestrator.queue import FileCommandQueue
from app.orchestrator.run_manager import RunManager
from app.storage.artifact_store import ArtifactStore
from app.storage.benchmark_definition_store import BenchmarkDefinitionStore
from app.storage.benchmark_task_store import BenchmarkTaskStore
from app.storage.gateway_store import GatewayStore
from app.storage.project_store import ProjectStore
from app.storage.run_control_store import RunControlStore
from app.storage.run_store import RunStore
from app.utils.time_utils import to_iso8601
from app.viewer.ego_snapshot import (
    EgoSnapshotViewer,
    EgoSnapshotViewerError,
    list_viewer_views,
)

router = APIRouter(tags=["运行管理"])
ACTIVE_VIEWER_STATUSES = {
    RunStatus.STARTING,
    RunStatus.RUNNING,
    RunStatus.PAUSED,
    RunStatus.STOPPING,
}
VIEWER_STREAM_INTERVAL_MS = 90
VIEWER_STREAM_WIDTH = 640
VIEWER_STREAM_HEIGHT = 360
VIEWER_PLAYBACK_INTERVAL_MS = 100
VIEWER_BUFFER_MIN_FRAMES = 5
VIEWER_BUFFER_MAX_FRAMES = 18


@lru_cache(maxsize=1)
def get_run_manager() -> RunManager:
    settings = get_settings()
    return RunManager(
        run_store=RunStore(settings.runs_root),
        artifact_store=ArtifactStore(settings.artifacts_root),
        command_queue=FileCommandQueue(settings.commands_root),
        gateway_store=GatewayStore(settings.gateways_root),
    )


@lru_cache(maxsize=1)
def get_artifact_store() -> ArtifactStore:
    settings = get_settings()
    return ArtifactStore(settings.artifacts_root)


@lru_cache(maxsize=1)
def get_project_store() -> ProjectStore:
    settings = get_settings()
    return ProjectStore(settings.projects_root)


@lru_cache(maxsize=1)
def get_benchmark_definition_store() -> BenchmarkDefinitionStore:
    settings = get_settings()
    return BenchmarkDefinitionStore(settings.benchmark_definitions_root)


@lru_cache(maxsize=1)
def get_benchmark_task_store() -> BenchmarkTaskStore:
    settings = get_settings()
    return BenchmarkTaskStore(settings.benchmark_tasks_root)


@lru_cache(maxsize=1)
def get_control_store() -> RunControlStore:
    settings = get_settings()
    return RunControlStore(settings.controls_root)


def _metadata_tag_value(metadata: dict[str, Any], prefix: str) -> str | None:
    tags = metadata.get("tags")
    if not isinstance(tags, list):
        return None

    needle = f"{prefix}:"
    for tag in tags:
        if not isinstance(tag, str) or not tag.startswith(needle):
            continue
        value = tag[len(needle) :].strip()
        return value or None
    return None


def _run_context_from_metadata(run: RunRecord) -> dict[str, str | None]:
    metadata = run.descriptor.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    project_id = _metadata_tag_value(metadata, "project") or _metadata_tag_value(
        metadata, "chip"
    )
    benchmark_definition_id = _metadata_tag_value(metadata, "benchmark")
    benchmark_task_id = _metadata_tag_value(metadata, "task")
    dut_model = metadata.get("dut_model")
    if not isinstance(dut_model, str) or not dut_model.strip():
        dut_model = None

    project_name = None
    if project_id:
        try:
            project_name = get_project_store().get(project_id).name
        except AppError:
            project_name = None

    benchmark_name = None
    if benchmark_definition_id:
        try:
            benchmark_name = (
                get_benchmark_definition_store().get(benchmark_definition_id).name
            )
        except AppError:
            benchmark_name = None

    if benchmark_task_id:
        try:
            task = get_benchmark_task_store().get(benchmark_task_id)
            project_name = project_name or task.project_name
            benchmark_name = benchmark_name or task.benchmark_name
            dut_model = dut_model or task.dut_model
        except AppError:
            pass

    return {
        "project_id": project_id,
        "project_name": project_name,
        "benchmark_definition_id": benchmark_definition_id,
        "benchmark_name": benchmark_name,
        "benchmark_task_id": benchmark_task_id,
        "dut_model": dut_model,
    }


def run_to_payload(run: RunRecord) -> RunPayload:
    metrics = get_artifact_store().read_metrics(run.run_id) or {}
    context = _run_context_from_metadata(run)
    created_at_utc = to_iso8601(run.created_at)
    updated_at_utc = to_iso8601(run.updated_at)
    started_at_utc = to_iso8601(run.started_at)
    ended_at_utc = to_iso8601(run.ended_at)

    return RunPayload(
        run_id=run.run_id,
        status=run.status.value,
        scenario_name=run.scenario_name,
        map_name=run.map_name,
        created_at_utc=created_at_utc,
        updated_at_utc=updated_at_utc,
        started_at_utc=started_at_utc,
        ended_at_utc=ended_at_utc,
        created_time=created_at_utc,
        updated_time=updated_at_utc,
        start_time=started_at_utc,
        end_time=ended_at_utc,
        error_reason=run.error_reason,
        stop_requested=run.stop_requested,
        cancel_requested=run.cancel_requested,
        hil_config=run.hil_config,
        evaluation_profile=run.evaluation_profile,
        artifact_dir=run.artifact_dir,
        execution_backend=run.execution_backend,
        scenario_source=run.scenario_source,
        project_id=context["project_id"],
        project_name=context["project_name"],
        benchmark_definition_id=context["benchmark_definition_id"],
        benchmark_name=context["benchmark_name"],
        benchmark_task_id=context["benchmark_task_id"],
        dut_model=context["dut_model"],
        metadata=run.descriptor.get("metadata", {}),
        weather=run.descriptor.get("weather", {}),
        traffic=run.descriptor.get("traffic", {}),
        sensors=run.descriptor.get("sensors", {}),
        debug=run.descriptor.get("debug", {}),
        runtime_capabilities={
            "weather_update": run.execution_backend == "native",
            "viewer_friendly": run.execution_backend == "native",
        },
        sim_time=metrics.get("sim_time"),
        current_tick=metrics.get("current_tick"),
        executed_tick_count=metrics.get("executed_tick_count"),
        sim_elapsed_seconds=metrics.get("sim_elapsed_seconds"),
        achieved_tick_rate_hz=metrics.get("achieved_tick_rate_hz"),
        wall_elapsed_seconds=metrics.get("wall_time"),
        spawned_actors_count=metrics.get("spawned_actors_count"),
    )


def raise_http_error(exc: AppError) -> NoReturn:
    detail = {"code": exc.code, "message": exc.message}
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=detail)
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=409, detail=detail)
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=422, detail=detail)
    raise HTTPException(status_code=500, detail=detail)


def _viewer_preferred_actor_id(events: list[dict[str, Any]]) -> int | None:
    for event in reversed(events):
        if event.get("event_type") != "EGO_SPAWNED":
            continue
        payload = event.get("payload", {})
        actor_id = payload.get("actor_id")
        if isinstance(actor_id, int):
            return actor_id
    return None


def _viewer_preferred_spawn_point(events: list[dict[str, Any]], run: RunRecord) -> dict[str, float] | None:
    for event in reversed(events):
        if event.get("event_type") != "EGO_SPAWNED":
            continue
        payload = event.get("payload", {})
        resolved_spawn_point = payload.get("resolved_spawn_point")
        if isinstance(resolved_spawn_point, dict):
            return resolved_spawn_point

    spawn_point = run.descriptor.get("ego_vehicle", {}).get("spawn_point")
    if isinstance(spawn_point, dict):
        return spawn_point
    return None


def _build_snapshot_viewer(
    manager: RunManager,
    run_id: str,
    run: RunRecord,
    *,
    width: int = 1280,
    height: int = 720,
) -> EgoSnapshotViewer:
    settings = get_settings()
    events = manager.get_events(run_id)
    return EgoSnapshotViewer(
        host=settings.carla_host,
        port=settings.carla_port,
        timeout_seconds=settings.carla_timeout_seconds,
        width=width,
        height=height,
        preferred_actor_id=_viewer_preferred_actor_id(events),
        preferred_spawn_point=_viewer_preferred_spawn_point(events, run),
    )


@router.post(
    "/runs",
    response_model=RunCreateResponse,
    summary="创建运行",
    description="根据 descriptor 创建一个 run，创建后状态为 CREATED。",
)
def create_run(request: CreateRunRequest) -> RunCreateResponse:
    manager = get_run_manager()
    try:
        run = manager.create_run(
            request.descriptor,
            request.descriptor_path,
            request.hil_config.model_dump(mode="json")
            if request.hil_config is not None
            else None,
            request.evaluation_profile.model_dump(mode="json")
            if request.evaluation_profile is not None
            else None,
        )
    except AppError as exc:
        raise_http_error(exc)

    return RunCreateResponse(
        success=True,
        data=RunCreatePayload(
            run_id=run.run_id,
            status=run.status.value,
            hil_config=run.hil_config,
            evaluation_profile=run.evaluation_profile,
        ),
    )


@router.post(
    "/runs/{run_id}/start",
    response_model=RunResponse,
    summary="启动运行",
    description="将 run 放入执行队列，状态从 CREATED 变为 QUEUED。",
)
def start_run(run_id: str) -> RunResponse:
    manager = get_run_manager()
    try:
        run = manager.start_run(run_id)
    except AppError as exc:
        raise_http_error(exc)

    return RunResponse(success=True, data=run_to_payload(run))


@router.post(
    "/runs/{run_id}/stop",
    response_model=RunResponse,
    summary="停止运行",
    description="请求停止运行。若尚未启动会直接取消；若运行中则进入 STOPPING。",
)
def stop_run(run_id: str) -> RunResponse:
    manager = get_run_manager()
    try:
        run = manager.stop_run(run_id)
    except AppError as exc:
        raise_http_error(exc)

    return RunResponse(success=True, data=run_to_payload(run))


@router.post(
    "/runs/{run_id}/cancel",
    response_model=RunResponse,
    summary="取消运行",
    description="请求取消运行。语义与 stop 类似，但标记为取消请求。",
)
def cancel_run(run_id: str) -> RunResponse:
    manager = get_run_manager()
    try:
        run = manager.cancel_run(run_id)
    except AppError as exc:
        raise_http_error(exc)

    return RunResponse(success=True, data=run_to_payload(run))


@router.get(
    "/runs/{run_id}",
    response_model=RunResponse,
    summary="查询单个运行",
    description="返回 run 当前状态、起止时间、错误原因和 artifact 路径。",
)
def get_run(run_id: str) -> RunResponse:
    manager = get_run_manager()
    try:
        run = manager.get_run(run_id)
    except AppError as exc:
        raise_http_error(exc)

    return RunResponse(success=True, data=run_to_payload(run))


@router.get(
    "/runs",
    response_model=RunListResponse,
    summary="查询运行列表",
    description="返回运行列表，可按状态过滤。",
)
def list_runs(
    status: str | None = Query(default=None, description="可选状态过滤值")
) -> RunListResponse:
    manager = get_run_manager()
    try:
        runs = manager.list_runs(status)
    except AppError as exc:
        raise_http_error(exc)

    return RunListResponse(success=True, data=[run_to_payload(run) for run in runs])


@router.get(
    "/runs/{run_id}/events",
    response_model=RunEventListResponse,
    summary="查询运行事件",
    description="返回该 run 的 events.jsonl 事件流。",
)
def get_run_events(run_id: str) -> RunEventListResponse:
    manager = get_run_manager()
    try:
        events = manager.get_events(run_id)
    except AppError as exc:
        raise_http_error(exc)

    return RunEventListResponse(
        success=True,
        data=[
            RunEventPayload(
                timestamp=str(event.get("timestamp", "")),
                run_id=str(event.get("run_id", run_id)),
                level=str(event.get("level", "INFO")),
                event_type=str(event.get("event_type", "")),
                message=str(event.get("message", "")),
                payload=event.get("payload", {}) if isinstance(event.get("payload", {}), dict) else {},
            )
            for event in events
        ],
    )


@router.get(
    "/runs/{run_id}/environment",
    response_model=RunEnvironmentStateResponse,
    summary="查询运行环境控制状态",
    description="返回该 run 当前 descriptor 中的环境参数以及最近一次运行时环境控制值。",
)
def get_run_environment(run_id: str) -> RunEnvironmentStateResponse:
    manager = get_run_manager()
    control_store = get_control_store()
    try:
        run = manager.get_run(run_id)
    except AppError as exc:
        raise_http_error(exc)
    control_state = control_store.get(run_id) or {}

    return RunEnvironmentStateResponse(
        success=True,
        data=RunEnvironmentStatePayload(
            run_id=run_id,
            descriptor_weather=run.descriptor.get("weather", {}),
            descriptor_debug=run.descriptor.get("debug", {}),
            runtime_control={
                "weather": control_state.get("weather"),
                "debug": control_state.get("debug"),
                "updated_at_utc": control_state.get("updated_at_utc"),
            },
        ),
    )


@router.get(
    "/runs/{run_id}/viewer",
    response_model=RunViewerInfoResponse,
    summary="查询运行时 viewer 状态",
    description="返回前端运行时显示界面所需的视角列表和当前可用性。",
)
def get_run_viewer(run_id: str) -> RunViewerInfoResponse:
    manager = get_run_manager()
    try:
        run = manager.get_run(run_id)
    except AppError as exc:
        raise_http_error(exc)

    available = run.status in ACTIVE_VIEWER_STATUSES
    reason = None
    if not available:
        reason = "viewer 仅在 STARTING / RUNNING / PAUSED / STOPPING 状态可用"

    return RunViewerInfoResponse(
        success=True,
        data=RunViewerInfoPayload(
            run_id=run_id,
            available=available,
            reason=reason,
            views=list_viewer_views(),
            snapshot_url=f"/runs/{run_id}/viewer/frame",
            stream_ws_path=f"/ws/runs/{run_id}/viewer",
            refresh_interval_ms=1200,
            stream_interval_ms=VIEWER_STREAM_INTERVAL_MS,
            playback_interval_ms=VIEWER_PLAYBACK_INTERVAL_MS,
            stream_buffer_min_frames=VIEWER_BUFFER_MIN_FRAMES,
            stream_buffer_max_frames=VIEWER_BUFFER_MAX_FRAMES,
        ),
    )


@router.get(
    "/runs/{run_id}/viewer/frame",
    include_in_schema=False,
    summary="获取运行时 viewer 单帧画面",
)
def get_run_viewer_frame(
    run_id: str,
    view: str = Query(default="third_person"),
) -> Response:
    manager = get_run_manager()
    try:
        run = manager.get_run(run_id)
    except AppError as exc:
        raise_http_error(exc)

    if run.status not in ACTIVE_VIEWER_STATUSES:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "RUN_VIEWER_NOT_AVAILABLE",
                "message": "viewer 仅在运行中或即将停止的状态可用",
            },
        )

    viewer = _build_snapshot_viewer(manager, run_id, run)
    try:
        png_bytes = viewer.capture_png_bytes(view_id=view)
    except EgoSnapshotViewerError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "RUN_VIEWER_UNAVAILABLE", "message": str(exc)},
        ) from exc

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@router.websocket("/ws/runs/{run_id}/viewer")
async def stream_run_viewer(websocket: WebSocket, run_id: str) -> None:
    await websocket.accept()
    manager = get_run_manager()
    view = websocket.query_params.get("view", "third_person")
    stream_session = None

    try:
        while True:
            try:
                run = manager.get_run(run_id)
            except AppError as exc:
                await websocket.send_json(
                    {
                        "type": "error",
                        "code": exc.code,
                        "message": exc.message,
                    }
                )
                return

            if run.status not in ACTIVE_VIEWER_STATUSES:
                await websocket.send_json(
                    {
                        "type": "unavailable",
                        "run_id": run_id,
                        "run_status": run.status.value,
                        "reason": "viewer 仅在运行中或即将停止的状态可用",
                    }
                )
                return

            try:
                if stream_session is None:
                    viewer = _build_snapshot_viewer(
                        manager,
                        run_id,
                        run,
                        width=VIEWER_STREAM_WIDTH,
                        height=VIEWER_STREAM_HEIGHT,
                    )
                    stream_session = await asyncio.to_thread(
                        viewer.open_stream_session, view_id=view
                    )

                png_bytes = await asyncio.to_thread(stream_session.capture_png_bytes, 2.5)
                await websocket.send_json(
                    {
                        "type": "frame",
                        "run_id": run_id,
                        "run_status": run.status.value,
                        "mime": "image/png",
                        "image_base64": base64.b64encode(png_bytes).decode("ascii"),
                    }
                )
            except EgoSnapshotViewerError as exc:
                await websocket.send_json(
                    {
                        "type": "unavailable",
                        "run_id": run_id,
                        "run_status": run.status.value,
                        "reason": str(exc),
                    }
                )
                if stream_session is not None:
                    await asyncio.to_thread(stream_session.close)
                    stream_session = None

            await asyncio.sleep(VIEWER_STREAM_INTERVAL_MS / 1000)
    except WebSocketDisconnect:
        return
    finally:
        if stream_session is not None:
            await asyncio.to_thread(stream_session.close)


@router.post(
    "/runs/{run_id}/environment",
    response_model=RunEnvironmentStateResponse,
    summary="更新运行环境参数",
    description="更新 run 的环境参数。运行中会由 executor 轮询并应用天气更新。",
)
def update_run_environment(
    run_id: str, request: RunEnvironmentUpdateRequest
) -> RunEnvironmentStateResponse:
    settings = get_settings()
    run_store = RunStore(settings.runs_root)
    control_store = get_control_store()
    try:
        run = run_store.get(run_id)
    except AppError as exc:
        raise_http_error(exc)

    if run.execution_backend != "native":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "RUN_ENVIRONMENT_UPDATE_UNSUPPORTED",
                "message": "当前 run 由官方 ScenarioRunner 执行，不支持平台侧运行时天气热更新",
            },
        )

    updated_run = run_store.update_descriptor_sections(
        run_id,
        weather=request.weather.model_dump(mode="json", exclude_none=True),
        debug=request.debug or run.descriptor.get("debug", {}),
    )
    control_state = control_store.save(
        run_id,
        {
            "weather": request.weather.model_dump(mode="json", exclude_none=True),
            "debug": request.debug or updated_run.descriptor.get("debug", {}),
        },
    )

    return RunEnvironmentStateResponse(
        success=True,
        data=RunEnvironmentStatePayload(
            run_id=run_id,
            descriptor_weather=updated_run.descriptor.get("weather", {}),
            descriptor_debug=updated_run.descriptor.get("debug", {}),
            weather=updated_run.descriptor.get("weather", {}),
            runtime_control={
                "weather": control_state.get("weather"),
                "debug": control_state.get("debug"),
                "updated_at_utc": control_state.get("updated_at_utc"),
            },
        ),
    )
