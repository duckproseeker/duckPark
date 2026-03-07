from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes_gateways import router as gateways_router
from app.api.routes_runs import router as runs_router
from app.api.routes_scenarios import router as scenarios_router
from app.api.routes_ui import router as ui_router
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(
    title="CARLA 场景仿真控制层 MVP",
    version="0.2.0",
    description=(
        "这是一个用于 CARLA 0.9.16 的场景仿真控制层 MVP。"
        "\n\n"
        "- `/docs`：开发调试用的 Swagger 页面"
        "\n"
        "- `/` 或 `/ui`：最小中文 Web 控制台"
    ),
)

_app_root = Path(__file__).resolve().parents[1]
app.mount("/static", StaticFiles(directory=str(_app_root / "static")), name="static")

app.include_router(ui_router)
app.include_router(runs_router)
app.include_router(scenarios_router)
app.include_router(gateways_router)


@app.get("/healthz", tags=["系统"])
def healthz() -> dict[str, str]:
    return {"status": "ok"}
