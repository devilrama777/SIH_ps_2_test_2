"""
Tests for /api/v1/sources and /api/v1/jobs HTTP endpoints.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from pathlib import Path
from apps.processing.server import app


@pytest.mark.asyncio
async def test_scan_folder_api(tmp_path: Path):
    """Verify /api/v1/sources/scan returns file distribution and metadata."""
    (tmp_path / "coal_report.csv").write_text("a,b,c")
    (tmp_path / "site.jpg").write_bytes(b"dummy")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/sources/scan",
            json={"folder_path": str(tmp_path)},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total_files"] == 2
        assert data["format_distribution"]["csv"] == 1
        assert data["format_distribution"]["image"] == 1
        assert len(data["files"]) == 2


@pytest.mark.asyncio
async def test_scan_invalid_folder():
    """Verify scanning non-existent folder returns 400 Bad Request."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/sources/scan",
            json={"folder_path": "C:/non_existent_folder_path_xyz_123"},
        )
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_job_api_lifecycle(tmp_path: Path):
    """Verify /api/v1/jobs/ingest starts a job and /api/v1/jobs/{id} returns status."""
    (tmp_path / "test.csv").write_text("x,y,z")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Start job
        start_res = await client.post(
            "/api/v1/jobs/ingest",
            json={"folder_path": str(tmp_path)},
        )
        assert start_res.status_code == 200
        job_data = start_res.json()
        job_id = job_data["job_id"]
        assert job_id.startswith("job_")

        # Query status
        status_res = await client.get(f"/api/v1/jobs/{job_id}")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["job_id"] == job_id

        # Cancel job test
        cancel_res = await client.post(f"/api/v1/jobs/{job_id}/cancel")
        assert cancel_res.status_code == 200
