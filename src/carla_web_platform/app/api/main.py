from __future__ import annotations

from fastapi import FastAPI

from app.api.routes_runs import router as runs_router
from app.api.routes_scenarios import router as scenarios_router
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(title="CARLA Simulation Control MVP", version="0.1.0")
app.include_router(runs_router)
app.include_router(scenarios_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
