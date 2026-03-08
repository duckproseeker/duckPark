from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes_ui import has_frontend_bundle


def test_ui_page_available() -> None:
    client = TestClient(app)

    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/ui"

    response_ui = client.get("/ui")
    assert response_ui.status_code == 200
    if has_frontend_bundle():
        assert 'id="root"' in response_ui.text
        assert "/assets/" in response_ui.text
    else:
        assert "场景仿真控制层" in response_ui.text
        assert "运行概览" in response_ui.text

    response_deep_link = client.get("/ui/runs")
    assert response_deep_link.status_code == 200

    response_api = client.get("/runs")
    assert response_api.status_code == 200
    assert response_api.json()["success"] is True
