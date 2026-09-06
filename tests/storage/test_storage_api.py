"""
Tests for Section 37 Storage Management and Safe Artifact Retention REST APIs.

Validates that:
- GET /api/v1/storage/breakdown reports disk consumption across all 7 artifact categories.
- POST /api/v1/storage/cleanup safely purges ephemeral render files while strictly protecting original sources.
- POST /api/v1/storage/purge-category enforces explicit confirmation tokens and unconditionally
  blocks purging of original_source with HTTP 403.
"""
from fastapi.testclient import TestClient

from apps.processing.server import app

client = TestClient(app)


def test_get_storage_breakdown():
    """Verify storage breakdown returns all tracked artifact categories and safety flags."""
    response = client.get("/api/v1/storage/breakdown")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "total_workspace_bytes" in data
    assert "formatted_total" in data

    categories = data["categories"]
    assert "original_source" in categories
    assert "render_temp" in categories
    assert "canonical_cache" in categories
    assert "search_index" in categories
    assert "asset_catalog" in categories
    assert "logs" in categories
    assert "reports" in categories

    # Section 37 invariant: original source is never safe to clean
    assert categories["original_source"]["is_safe_to_clean"] is False
    assert categories["render_temp"]["is_safe_to_clean"] is True


def test_cleanup_temporary_artifacts_dry_run():
    """Verify storage cleanup dry run executes without error."""
    response = client.post(
        "/api/v1/storage/cleanup",
        json={"max_age_seconds": 0.0, "dry_run": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert "deleted_file_count" in data
    assert "freed_bytes" in data
    assert "formatted_freed" in data
    assert data["dry_run"] is True


def test_purge_category_rejects_original_source():
    """Verify Section 37 Invariant: ORIGINAL_SOURCE cannot be purged via API."""
    response = client.post(
        "/api/v1/storage/purge-category",
        json={
            "category": "original_source",
            "confirmation": "PURGE_ORIGINAL_SOURCE",
        },
    )
    assert response.status_code == 403
    assert "Violation of Section 37 Invariant" in response.json()["detail"]


def test_purge_category_requires_valid_confirmation():
    """Verify purge-category rejects requests with invalid confirmation tokens."""
    response = client.post(
        "/api/v1/storage/purge-category",
        json={
            "category": "render_temp",
            "confirmation": "INVALID_TOKEN",
        },
    )
    assert response.status_code == 400
    assert "Invalid confirmation token" in response.json()["detail"]
