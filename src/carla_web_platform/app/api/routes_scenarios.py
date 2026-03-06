from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from app.api.schemas import ApiResponse
from app.scenario.registry import list_builtin_scenarios

router = APIRouter()


@router.get("/scenarios", response_model=ApiResponse)
def list_scenarios() -> ApiResponse:
    project_root = Path(__file__).resolve().parents[2]
    sample_files = sorted((project_root / "configs" / "scenarios").glob("sample_*.yaml"))
    return ApiResponse(
        success=True,
        data={
            "builtins": list_builtin_scenarios(),
            "sample_descriptors": [str(path) for path in sample_files],
        },
    )
