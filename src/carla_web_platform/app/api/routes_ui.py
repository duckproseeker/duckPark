from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["控制台"])

_app_root = Path(__file__).resolve().parents[1]
_project_root = _app_root.parent
_templates = Jinja2Templates(directory=str(_app_root / "templates"))
_frontend_dist_root = _project_root / "frontend" / "dist"
_frontend_index_file = _frontend_dist_root / "index.html"


def has_frontend_bundle() -> bool:
    return _frontend_index_file.exists()


def render_legacy_ui(request: Request) -> HTMLResponse:
    return _templates.TemplateResponse(
        request=request,
        name="ui.html",
        context={
            "system_name": "CARLA 场景仿真控制层",
            "stage": "MVP",
        },
    )


def render_frontend_index() -> FileResponse:
    return FileResponse(_frontend_index_file, media_type="text/html")


@router.get("/", include_in_schema=False)
def ui_root() -> RedirectResponse:
    return RedirectResponse(url="/ui", status_code=307)


@router.get("/ui", include_in_schema=False, response_class=HTMLResponse)
@router.get("/ui/{full_path:path}", include_in_schema=False, response_class=HTMLResponse)
def ui_home(request: Request, full_path: str = "") -> Response:
    if has_frontend_bundle():
        return render_frontend_index()
    return render_legacy_ui(request)


@router.get("/ui-legacy", response_class=HTMLResponse, include_in_schema=False)
def ui_legacy(request: Request) -> HTMLResponse:
    return render_legacy_ui(request)
