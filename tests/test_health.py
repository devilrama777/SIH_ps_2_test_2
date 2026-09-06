"""
Tests for service health checks and system diagnostics endpoints.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from apps.processing.server import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Verify /api/v1/health returns 200 OK and expected schema."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "cil-report-ai-processing"
        assert data["version"] == "0.1.0"
        assert data["uptime_seconds"] >= 0
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_diagnostics_endpoint():
    """Verify /api/v1/diagnostics reports valid host environment metrics."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/diagnostics")
        assert response.status_code == 200
        data = response.json()
        assert "platform" in data
        assert "python_version" in data
        assert data["cpu_count_logical"] > 0
        assert data["memory_total_gb"] > 0
        assert 0.0 <= data["memory_used_percent"] <= 100.0
        assert data["disk_total_gb"] > 0


@pytest.mark.asyncio
async def test_system_info_endpoint():
    """Verify /api/v1/system/info returns configuration status and local-only flag."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/system/info")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "cil-report-ai-processing"
        assert data["local_only"] is True
        assert "workspace_root" in data
