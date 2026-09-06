"""
Tests for Embedded Static Desktop UI Serving (Section 25 & 38).

Verifies that the local processing server on port 8765 directly serves the compiled
React frontend from `apps/desktop/dist` for zero-Node workstation environments,
while ensuring that all REST API endpoints retain routing precedence.
"""
from pathlib import Path
from fastapi.testclient import TestClient

from apps.processing.server import app

client = TestClient(app)


def test_root_serves_desktop_ui():
    """Verify GET / returns the desktop UI index.html with 200 OK."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert '<div id="root">' in response.text or "<title>" in response.text


def test_ui_mount_serves_static_files():
    """Verify /ui route mounts apps/desktop/dist."""
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert '<div id="root">' in response.text or "<title>" in response.text


def test_assets_mount_serves_js_css():
    """Verify /assets route serves built js/css bundles."""
    dist_assets = Path(__file__).resolve().parent.parent.parent / "apps" / "desktop" / "dist" / "assets"
    if dist_assets.exists():
        asset_files = list(dist_assets.iterdir())
        assert len(asset_files) > 0, "Expected at least one built asset file in apps/desktop/dist/assets"
        sample_asset = asset_files[0]
        response = client.get(f"/assets/{sample_asset.name}")
        assert response.status_code == 200
        assert len(response.content) > 0


def test_api_precedence_and_system_info():
    """Verify REST API routes take precedence over static file mounts."""
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "cil-report-ai-processing"
    assert "workspace_root" in data


def test_docs_and_openapi_accessible():
    """Verify OpenAPI documentation is still served at /docs and /openapi.json."""
    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200
    assert "swagger" in docs_resp.text.lower() or "html" in docs_resp.headers.get("content-type", "")

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    assert openapi_resp.json()["info"]["title"] is not None
