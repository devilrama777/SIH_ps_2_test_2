"""
Tests for Master Plan Section 37: Storage Management and Retention Lifecycle.

Verifies:
1. Precise tracking across all 7 Section 37 artifact categories:
   - original source
   - processed representation
   - OCR result
   - structured extraction
   - embeddings/indexes
   - generated report
   - temporary render files
2. Safe cleanup policies for temporary artifacts.
3. Invariant: Original source files are strictly protected against automated deletion.
4. Explicitly authorized source deletion via cryptographic tokens.
5. End-to-end REST API behavior for storage lifecycle endpoints.
"""

from pathlib import Path
import time
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app, storage_manager
from core.storage.lifecycle import (
    ArtifactCategory,
    RetentionRule,
    StorageManager,
    format_bytes,
)

client = TestClient(app)


def test_section_37_all_categories_tracked(tmp_path):
    """Verify that all 7 Section 37 artifact categories are tracked and accounted for."""
    sm = StorageManager(workspace_dir=str(tmp_path))

    # Populate dummy files in each of the 7 Section 37 categories
    files = {
        ArtifactCategory.ORIGINAL_SOURCE: "source_doc.pdf",
        ArtifactCategory.PROCESSED_REPRESENTATION: "canonical_doc.json",
        ArtifactCategory.OCR_RESULT: "ocr_boxes.json",
        ArtifactCategory.STRUCTURED_EXTRACTION: "extracted_table.csv",
        ArtifactCategory.EMBEDDINGS_INDEXES: "sqlite_fts.db",
        ArtifactCategory.GENERATED_REPORT: "annual_report.pdf",
        ArtifactCategory.TEMPORARY_RENDER: "scratch_page.html",
    }

    for cat, filename in files.items():
        cat_path = sm.category_paths[cat]
        (cat_path / filename).write_text(f"dummy content for {cat.value}", encoding="utf-8")

    breakdown = sm.get_storage_breakdown()

    # All 7 categories must be present in breakdown
    for cat in files.keys():
        assert cat.value in breakdown
        summary = breakdown[cat.value]
        assert summary.file_count >= 1
        assert summary.total_bytes > 0

    # Section 37 Invariant: Original source is NEVER marked safe to clean
    assert breakdown[ArtifactCategory.ORIGINAL_SOURCE.value].is_safe_to_clean is False
    # Temporary render files ARE safe to clean
    assert breakdown[ArtifactCategory.TEMPORARY_RENDER.value].is_safe_to_clean is True


def test_cleanup_temporary_artifacts_policy(tmp_path):
    """Test policy-based cleanup of ephemeral render files while preserving protected files."""
    sm = StorageManager(workspace_dir=str(tmp_path))

    temp_dir = sm.category_paths[ArtifactCategory.TEMPORARY_RENDER]
    sources_dir = sm.category_paths[ArtifactCategory.ORIGINAL_SOURCE]

    # Create source file
    source_file = sources_dir / "ccl_coal_production_fy24.pdf"
    source_file.write_text("CONFIDENTIAL RAW SOURCE DATA", encoding="utf-8")

    # Create temp render files
    temp_file_1 = temp_dir / "render_frame_01.tmp"
    temp_file_1.write_text("ephemeral frame buffer 1", encoding="utf-8")

    temp_file_2 = temp_dir / "render_frame_02.tmp"
    temp_file_2.write_text("ephemeral frame buffer 2", encoding="utf-8")

    # 1. Dry run
    dry_res = sm.cleanup_temporary_artifacts(max_age_seconds=0.0, dry_run=True)
    assert dry_res["dry_run"] is True
    assert dry_res["deleted_file_count"] == 2
    assert temp_file_1.exists()
    assert temp_file_2.exists()

    # 2. Real cleanup
    real_res = sm.cleanup_temporary_artifacts(max_age_seconds=0.0, dry_run=False)
    assert real_res["deleted_file_count"] == 2
    assert not temp_file_1.exists()
    assert not temp_file_2.exists()

    # Section 37 Invariant: Original source MUST NOT be touched
    assert source_file.exists()
    assert source_file.read_text(encoding="utf-8") == "CONFIDENTIAL RAW SOURCE DATA"


def test_retention_policy_enforcement_and_quota_pruning(tmp_path):
    """Test automated retention policies including age thresholds and byte quotas."""
    sm = StorageManager(workspace_dir=str(tmp_path))
    ocr_dir = sm.category_paths[ArtifactCategory.OCR_RESULT]

    # Create 4 OCR cache files with distinct sizes
    f1 = ocr_dir / "ocr_old_1.json"
    f1.write_text("A" * 1000, encoding="utf-8")  # 1000 bytes

    f2 = ocr_dir / "ocr_old_2.json"
    f2.write_text("B" * 2000, encoding="utf-8")  # 2000 bytes

    f3 = ocr_dir / "ocr_recent_3.json"
    f3.write_text("C" * 1500, encoding="utf-8")  # 1500 bytes

    # Configure rule: Quota 2500 bytes, preserve at least 1 item
    sm.retention_rules[ArtifactCategory.OCR_RESULT] = RetentionRule(
        category=ArtifactCategory.OCR_RESULT.value,
        max_age_seconds=None,
        max_bytes_quota=2500,
        preserve_minimum_count=1,
        is_safe_to_clean=True,
    )

    res = sm.apply_retention_policies(categories=[ArtifactCategory.OCR_RESULT], dry_run=False)
    assert res["total_deleted_files"] >= 1
    assert res["total_freed_bytes"] > 0

    # Remaining files must respect quota
    remaining_files = list(ocr_dir.glob("*.json"))
    total_remaining_size = sum(f.stat().st_size for f in remaining_files)
    assert total_remaining_size <= 2500


def test_retention_policy_strictly_protects_original_sources(tmp_path):
    """Verify that applying retention policies across all categories skips original sources."""
    sm = StorageManager(workspace_dir=str(tmp_path))
    sources_dir = sm.category_paths[ArtifactCategory.ORIGINAL_SOURCE]

    source_file = sources_dir / "sacred_source.pdf"
    source_file.write_text("DO NOT DELETE THIS", encoding="utf-8")

    # Even if ORIGINAL_SOURCE is explicitly requested in categories to apply
    res = sm.apply_retention_policies(
        categories=[ArtifactCategory.ORIGINAL_SOURCE, ArtifactCategory.TEMPORARY_RENDER],
        dry_run=False,
    )

    assert res["details"]["original_source"]["status"] == "PROTECTED"
    assert res["details"]["original_source"]["deleted_count"] == 0
    assert source_file.exists()


def test_explicit_source_deletion_with_authorization_token(tmp_path):
    """Test authorized deletion of a single original source with cryptographic token."""
    sm = StorageManager(workspace_dir=str(tmp_path))
    sources_dir = sm.category_paths[ArtifactCategory.ORIGINAL_SOURCE]

    test_source = sources_dir / "decommissioned_source.xlsx"
    test_source.write_text("Old deprecated spreadsheet", encoding="utf-8")

    # 1. Reject without valid token
    with pytest.raises(ValueError) as exc:
        sm.authorize_source_deletion("decommissioned_source.xlsx", authorization_token="INVALID_TOKEN")
    assert "Unauthorized" in str(exc.value)
    assert test_source.exists()

    # 2. Obtain valid token and authorize deletion
    valid_token = sm.generate_source_deletion_token("decommissioned_source.xlsx")
    audit_record = sm.authorize_source_deletion(
        "decommissioned_source.xlsx",
        authorization_token=valid_token,
        authorized_by="security_auditor",
        reason="GDPR right-to-erasure compliance",
    )

    assert audit_record["action"] == "EXPLICIT_SOURCE_DELETION"
    assert audit_record["authorized_by"] == "security_auditor"
    assert not test_source.exists()


def test_storage_api_rest_endpoints():
    """Verify all Section 37 REST API endpoints via TestClient."""
    # 1. GET /api/v1/storage/breakdown
    res = client.get("/api/v1/storage/breakdown")
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data
    assert "original_source" in data["categories"]
    assert "temporary_render" in data["categories"]
    assert "processed_representation" in data["categories"]
    assert data["categories"]["original_source"]["is_safe_to_clean"] is False

    # 2. GET /api/v1/storage/policies
    res = client.get("/api/v1/storage/policies")
    assert res.status_code == 200
    policies = res.json()["policies"]
    assert "temporary_render" in policies
    assert "original_source" in policies
    assert policies["original_source"]["require_explicit_authorization"] is True

    # 3. POST /api/v1/storage/policies (update policy)
    res = client.post(
        "/api/v1/storage/policies",
        json={
            "category": "temporary_render",
            "max_age_seconds": 43200.0,
            "max_bytes_quota": 250000000,
            "preserve_minimum_count": 2,
        },
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["max_age_seconds"] == 43200.0

    # 4. POST /api/v1/storage/policies rejects updating original_source
    res = client.post(
        "/api/v1/storage/policies",
        json={
            "category": "original_source",
            "max_age_seconds": 3600.0,
        },
    )
    assert res.status_code == 403
    assert "Violation of Section 37 Invariant" in res.json()["detail"]

    # 5. POST /api/v1/storage/cleanup/temp
    res = client.post(
        "/api/v1/storage/cleanup/temp",
        json={"max_age_seconds": 0.0, "dry_run": True},
    )
    assert res.status_code == 200
    assert "deleted_file_count" in res.json()

    # 6. POST /api/v1/storage/apply-policies
    res = client.post(
        "/api/v1/storage/apply-policies",
        json={"categories": ["temporary_render", "ocr_result"], "dry_run": True},
    )
    assert res.status_code == 200
    assert res.json()["dry_run"] is True


def test_api_authorize_source_deletion_flow():
    """Verify REST workflow for generating a source token and authorizing source deletion."""
    sources_dir = storage_manager.category_paths[ArtifactCategory.ORIGINAL_SOURCE]
    test_file = sources_dir / "api_test_source.txt"
    test_file.write_text("Source document created for API deletion test", encoding="utf-8")

    try:
        # Step 1: Query required token
        res = client.get(f"/api/v1/storage/source-token/api_test_source.txt")
        assert res.status_code == 200
        token = res.json()["required_token"]
        assert token.startswith("CONFIRM_DELETE_SOURCE_")

        # Step 2: Attempt with wrong token -> 400
        fail_res = client.post(
            "/api/v1/storage/authorize-source-deletion",
            json={
                "relative_path": "api_test_source.txt",
                "authorization_token": "CONFIRM_DELETE_SOURCE_WRONG",
                "authorized_by": "auditor",
                "reason": "Testing unauthorized block",
            },
        )
        assert fail_res.status_code == 400
        assert test_file.exists()

        # Step 3: Authorize with correct token -> 200
        success_res = client.post(
            "/api/v1/storage/authorize-source-deletion",
            json={
                "relative_path": "api_test_source.txt",
                "authorization_token": token,
                "authorized_by": "compliance_lead",
                "reason": "Test authorized deletion",
            },
        )
        assert success_res.status_code == 200
        assert not test_file.exists()
    finally:
        if test_file.exists():
            test_file.unlink()
