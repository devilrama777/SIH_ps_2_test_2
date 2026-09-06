import pytest
from fastapi.testclient import TestClient
from apps.processing.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_storage_breakdown_and_cleanup_api(client):
    # 1. Storage breakdown endpoint
    res = client.get("/api/v1/storage/breakdown")
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data
    assert "total_workspace_bytes" in data
    assert "original_source" in data["categories"]
    assert "render_temp" in data["categories"]

    # 2. Storage cleanup endpoint (dry_run)
    cleanup_res = client.post(
        "/api/v1/storage/cleanup",
        json={"max_age_seconds": 0.0, "dry_run": True},
    )
    assert cleanup_res.status_code == 200
    c_data = cleanup_res.json()
    assert "deleted_file_count" in c_data
    assert c_data["dry_run"] is True


def test_observability_and_diagnostics_export_api(client):
    # 1. Telemetry endpoint
    res = client.get("/api/v1/observability/telemetry?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "recent_events" in data
    assert "stage_aggregates" in data

    # 2. Export diagnostics bundle
    exp_res = client.post("/api/v1/observability/export-diagnostics", json={})
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert "bundle_filename" in exp_data
    assert "sha256_hash" in exp_data
    assert exp_data["bundle_filename"].endswith(".zip")

    # 3. Download diagnostics bundle
    dl_res = client.get(f"/api/v1/observability/download-diagnostics/{exp_data['bundle_filename']}")
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/zip"
    assert len(dl_res.content) > 0


def test_incremental_invalidation_api(client):
    req_payload = {
        "report_data": {
            "report_id": "rep_test_api",
            "sections": [
                {
                    "section_id": "sec_exec",
                    "title": "Executive Summary",
                    "source_refs": ["prod_stats.xlsx"]
                },
                {
                    "section_id": "sec_prod",
                    "title": "Production Performance",
                    "source_refs": ["prod_stats.xlsx"]
                },
                {
                    "section_id": "sec_fin",
                    "title": "Audited Financials",
                    "source_refs": ["balance_sheet.xlsx"]
                }
            ]
        },
        "changed_sources": ["prod_stats.xlsx"],
    }

    res = client.post("/api/v1/reports/incremental/invalidate", json=req_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_sections"] == 3
    assert "sec_prod" in data["dirty_sections"]
    assert "sec_exec" in data["dirty_sections"]
    assert "sec_fin" in data["clean_sections"]
