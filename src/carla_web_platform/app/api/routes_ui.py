from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["控制台"])

_app_root = Path(__file__).resolve().parents[1]
_templates = Jinja2Templates(directory=str(_app_root / "templates"))


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
@router.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def ui_home(request: Request) -> HTMLResponse:
    return _templates.TemplateResponse(
        request=request,
        name="ui.html",
        context={
            "system_name": "CARLA 场景仿真控制层",
            "stage": "MVP",
        },
    )
