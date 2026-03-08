from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import ApiResponse
from app.core.config import get_settings
from app.executor.carla_client import CarlaClient
from app.scenario.environment_presets import list_environment_presets
from app.scenario.library import list_scenario_catalog
from app.scenario.maps import collapse_available_maps
from app.scenario.registry import list_builtin_scenarios
from app.scenario.sensor_profiles import load_sensor_profiles

router = APIRouter(tags=["场景管理"])

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

    return collapse_available_maps(available_maps)


@router.get(
    "/scenarios",
    response_model=ApiResponse,
    summary="查询内置场景",
    description="返回内置场景信息、默认地图与 UI 可用的 descriptor 模板。",
)
def list_scenarios() -> ApiResponse:
    project_root = get_settings().project_root
    sample_files = sorted(
        (project_root / "configs" / "scenarios").glob("sample_*.yaml")
    )
    return ApiResponse(
        success=True,
        data={
            "builtins": list_builtin_scenarios(),
            "catalog": list_scenario_catalog(),
            "environment_presets": list_environment_presets(),
            "sensor_profiles": load_sensor_profiles(get_settings().sensor_profiles_root),
            "sample_descriptors": [str(path) for path in sample_files],
        },
    )


@router.get(
    "/scenarios/catalog",
    response_model=ApiResponse,
    summary="查询场景库目录",
    description="返回本地可执行场景与官方 ScenarioRunner 模板目录。",
)
def list_scenario_catalog_endpoint() -> ApiResponse:
    return ApiResponse(success=True, data={"items": list_scenario_catalog()})


@router.get(
    "/scenarios/environment-presets",
    response_model=ApiResponse,
    summary="查询环境参数预设",
    description="返回用于运行前配置和运行中环境调参的预设。",
)
def get_environment_presets() -> ApiResponse:
    return ApiResponse(success=True, data={"items": list_environment_presets()})


@router.get(
    "/scenarios/sensor-profiles",
    response_model=ApiResponse,
    summary="查询传感器配置模板",
    description="返回 YAML 传感器模板，格式参考 CARLA official agent sensors() 配置。",
)
def get_sensor_profiles() -> ApiResponse:
    settings = get_settings()
    return ApiResponse(
        success=True,
        data={"items": load_sensor_profiles(settings.sensor_profiles_root)},
    )


@router.get(
    "/maps",
    response_model=ApiResponse,
    summary="查询 CARLA 可用地图",
    description="直接从当前配置的 CARLA server 读取可加载地图列表，用于前端下拉选择。",
)
def list_maps() -> ApiResponse:
    return ApiResponse(success=True, data={"maps": fetch_available_maps()})
