from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.api.schemas import ApiResponse
from app.core.config import get_settings
from app.executor.carla_client import CarlaClient
from app.scenario.registry import list_builtin_scenarios

router = APIRouter(tags=["场景管理"])


def normalize_map_display_name(map_name: str) -> str:
    normalized = str(map_name).rstrip("/")
    tail = normalized.rsplit("/", maxsplit=1)[-1]
    return tail or normalized


def fetch_available_maps() -> list[dict[str, str]]:
    settings = get_settings()
    client = CarlaClient(
        settings.carla_host,
        settings.carla_port,
        settings.carla_timeout_seconds,
        settings.traffic_manager_port,
    )

    try:
        client.connect()
        available_maps = client.get_available_maps()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail={
                "code": "CARLA_MAPS_UNAVAILABLE",
                "message": f"获取 CARLA 地图列表失败: {exc}",
            },
        ) from exc

    items = [
        {
            "map_name": map_name,
            "display_name": normalize_map_display_name(map_name),
        }
        for map_name in available_maps
    ]
    items.sort(key=lambda item: (item["display_name"], item["map_name"]))
    return items


@router.get(
    "/scenarios",
    response_model=ApiResponse,
    summary="查询内置场景",
    description="返回内置场景信息、默认地图与 UI 可用的 descriptor 模板。",
)
def list_scenarios() -> ApiResponse:
    project_root = Path(__file__).resolve().parents[2]
    sample_files = sorted(
        (project_root / "configs" / "scenarios").glob("sample_*.yaml")
    )
    return ApiResponse(
        success=True,
        data={
            "builtins": list_builtin_scenarios(),
            "sample_descriptors": [str(path) for path in sample_files],
        },
    )


@router.get(
    "/maps",
    response_model=ApiResponse,
    summary="查询 CARLA 可用地图",
    description="直接从当前配置的 CARLA server 读取可加载地图列表，用于前端下拉选择。",
)
def list_maps() -> ApiResponse:
    return ApiResponse(success=True, data={"maps": fetch_available_maps()})
