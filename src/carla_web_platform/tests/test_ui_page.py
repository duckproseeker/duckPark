from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import app


def test_ui_page_available() -> None:
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert "场景仿真控制层" in response.text
    assert "/docs" in response.text

    response_ui = client.get("/ui")
    assert response_ui.status_code == 200
