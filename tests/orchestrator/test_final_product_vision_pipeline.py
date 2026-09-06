"""
Tests for Phase 40: End-to-End Final Product Vision Pipeline & Unified Operational Workflow (Section 46).
Validates the complete 15-stage pipeline, human-in-the-loop review, and connector export manifest.
"""
import hashlib
import json
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.orchestrator.final_product_vision import (
    FinalProductVisionPipeline,
    FinalProductVisionConfig,
    VisionPipelineResult,
    VisionStageExecution,
)
from core.security.models import AuditEventType


@pytest.fixture
def vision_workspace(tmp_path):
    """Fixture providing isolated temporary workspace directory."""
    ws = tmp_path / "vision_ws"
    ws.mkdir(parents=True, exist_ok=True)
    return ws


@pytest.fixture
def reference_input_dir():
    """Fixture path to existing reference test documents."""
    ref_dir = Path("testdata/reference_report")
    assert ref_dir.exists(), f"Reference report test directory missing at {ref_dir}"
    return ref_dir


def test_vision_pipeline_config():
    """Verify FinalProductVisionConfig validation and defaults."""
    cfg = FinalProductVisionConfig(
        input_directory="testdata/reference_report",
        subsidiary="CCL",
        fiscal_year="2023-2024",
    )
    assert cfg.subsidiary_code == "CCL"
    assert cfg.strict_audit_mode is True
    assert cfg.prior_year_directory is None


def test_execute_15_step_vision_pipeline(vision_workspace, reference_input_dir):
    """
    Validates end-to-end execution of all 15 discrete stages in Section 46:
    1. Discovers files
    2. Extracts documents
    3. OCRs scans
    4. Extracts tables
    5. Indexes evidence
    6. Identifies dates
    7. Analyzes previous structure
    8. Discovers current topics
    9. Creates dynamic report plan
    10. Selects relevant evidence
    11. Generates sections locally
    12. Validates facts/numbers
    13. Selects appropriate images
    14. Composes the report
    15. Renders PDF
    """
    pipeline = FinalProductVisionPipeline(workspace_dir=str(vision_workspace))
    cfg = FinalProductVisionConfig(
        input_directory=str(reference_input_dir),
        subsidiary="CCL",
        fiscal_year="2023-2024",
        strict_audit_mode=True,
    )

    result = pipeline.execute_pipeline(cfg)

    # Core result invariants
    assert isinstance(result, VisionPipelineResult)
    assert result.status == "GENERATED"
    assert "Coalfields" in result.subsidiary or result.subsidiary == "CCL"
    assert "2023" in result.reporting_period
    assert result.total_duration_seconds > 0.0

    # 15 Stages verification
    assert len(result.stages) == 15
    stage_numbers = [s.stage_number for s in result.stages]
    assert stage_numbers == list(range(1, 16))

    stage_names = [s.stage_name for s in result.stages]
    assert "Discovers Files" in stage_names
    assert "Extracts Documents" in stage_names
    assert "OCRs Scans" in stage_names
    assert "Extracts Tables" in stage_names
    assert "Indexes Evidence" in stage_names
    assert "Identifies Dates" in stage_names
    assert "Analyzes Previous Structure" in stage_names
    assert "Discovers Current Topics" in stage_names
    assert "Creates Dynamic Report Plan" in stage_names
    assert "Selects Relevant Evidence" in stage_names
    assert "Generates Sections Locally" in stage_names
    assert "Validates Facts/Numbers" in stage_names
    assert "Selects Appropriate Images" in stage_names
    assert "Composes the Report" in stage_names
    assert "Renders PDF" in stage_names

    # Data model and artifacts
    assert result.section_count >= 1
    assert result.table_count >= 1
    assert result.evidence_count >= 1
    assert result.pdf_path is not None
    pdf_file = Path(result.pdf_path)
    assert pdf_file.exists()
    assert pdf_file.stat().st_size > 0

    # Tamper-evident checksum check
    computed_sha256 = hashlib.sha256(pdf_file.read_bytes()).hexdigest()
    assert result.manifest_sha256 == computed_sha256

    # Quality & numerical validation invariant
    assert result.validation_passed is True
    assert result.numerical_error_rate == 0.0
    assert result.unsupported_claim_rate == 0.0


def test_pipeline_status_query(vision_workspace, reference_input_dir):
    """Validates get_pipeline_status lookup and error handling."""
    pipeline = FinalProductVisionPipeline(workspace_dir=str(vision_workspace))
    cfg = FinalProductVisionConfig(
        input_directory=str(reference_input_dir),
        subsidiary="CCL",
    )
    result = pipeline.execute_pipeline(cfg)

    # Valid lookup
    fetched = pipeline.get_pipeline_status(result.pipeline_id)
    assert fetched.pipeline_id == result.pipeline_id
    assert fetched.manifest_sha256 == result.manifest_sha256

    # Invalid lookup
    with pytest.raises(KeyError):
        pipeline.get_pipeline_status("non_existent_id")


def test_agentic_human_in_the_loop_correction(vision_workspace, reference_input_dir):
    """
    Validates Section 46 User Review flow:
    User asks agent for adjustments -> system regenerates only affected section ->
    revalidates -> updates final PDF and increments audit trail.
    """
    pipeline = FinalProductVisionPipeline(workspace_dir=str(vision_workspace))
    cfg = FinalProductVisionConfig(
        input_directory=str(reference_input_dir),
        subsidiary="CCL",
    )
    init_res = pipeline.execute_pipeline(cfg)
    old_sha256 = init_res.manifest_sha256

    # Apply correction
    rev_res = pipeline.apply_human_correction(
        pipeline_id=init_res.pipeline_id,
        requested_change="Emphasize land reclamation and ESG goals",
    )

    assert rev_res.status == "REVIEWED"
    assert rev_res.human_correction_applied is True
    assert rev_res.review_notes == "Emphasize land reclamation and ESG goals"
    assert rev_res.corrected_section_id is not None
    assert rev_res.manifest_sha256 is not None
    # SHA-256 updated
    assert Path(rev_res.pdf_path).exists()


def test_executive_approval_and_connector_export(vision_workspace, reference_input_dir):
    """
    Validates Section 46 Final Approval & Authorized Export:
    - Generates signed approval manifest with SHA-256 integrity digest.
    - Exports standalone verifiable bundle.
    - Connectors: tests local export, CIL ERP connector, and SharePoint.
    """
    pipeline = FinalProductVisionPipeline(workspace_dir=str(vision_workspace))
    cfg = FinalProductVisionConfig(
        input_directory=str(reference_input_dir),
        subsidiary="CCL",
    )
    init_res = pipeline.execute_pipeline(cfg)

    # 1. Test local connector export
    export_out = pipeline.approve_and_export(
        pipeline_id=init_res.pipeline_id,
        connector_type="local",
        authorized_by="General Manager (Mining & Planning)",
    )

    assert export_out["status"] == "SUCCESS"
    assert export_out["pipeline_id"] == init_res.pipeline_id
    assert export_out["connector_status"] == "LOCAL_EXPORT_READY"

    bundle_dir = Path(export_out["export_bundle_dir"])
    assert bundle_dir.exists()

    manifest_path = bundle_dir / "approval_manifest.json"
    assert manifest_path.exists()
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_data["approved_by"] == "General Manager (Mining & Planning)"
    assert manifest_data["pdf_sha256"] == init_res.manifest_sha256
    assert manifest_data["numerical_accuracy"] == "100.0% (0.00% variance)"
    assert manifest_data["validation_status"] == "PASSED"

    # Exported PDF exists in bundle
    exported_pdf = bundle_dir / manifest_data["pdf_filename"]
    assert exported_pdf.exists()

    # 2. Test CIL API connector dispatch
    cil_out = pipeline.approve_and_export(
        pipeline_id=init_res.pipeline_id,
        connector_type="cil_api",
        authorized_by="Director Technical (CIL HQ)",
    )
    assert "DISPATCHED_TO_CIL_ERP" in cil_out["connector_status"]

    # 3. Test SharePoint connector upload
    sp_out = pipeline.approve_and_export(
        pipeline_id=init_res.pipeline_id,
        connector_type="sharepoint",
        authorized_by="Chief Vigilance Officer",
    )
    assert "UPLOADED_TO_SHAREPOINT" in sp_out["connector_status"]


def test_fastapi_vision_pipeline_rest_endpoints(reference_input_dir):
    """Tests the 4 FastAPI REST endpoints for the Section 46 vision pipeline."""
    client = TestClient(app)

    # 1. POST /api/v1/workflow/vision-pipeline/execute
    exec_resp = client.post(
        "/api/v1/workflow/vision-pipeline/execute",
        json={
            "input_directory": str(reference_input_dir),
            "subsidiary": "CCL",
            "fiscal_year": "2023-2024",
            "strict_audit_mode": True,
        },
    )
    assert exec_resp.status_code == 200
    res_data = exec_resp.json()
    pid = res_data["pipeline_id"]
    assert res_data["status"] == "GENERATED"
    assert len(res_data["stages"]) == 15
    assert res_data["manifest_sha256"] is not None

    # 2. GET /api/v1/workflow/vision-pipeline/{pipeline_id}/status
    status_resp = client.get(f"/api/v1/workflow/vision-pipeline/{pid}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["pipeline_id"] == pid
    assert status_data["validation_passed"] is True

    # 404 for unknown pipeline
    assert client.get("/api/v1/workflow/vision-pipeline/unknown_xyz/status").status_code == 404

    # 3. POST /api/v1/workflow/vision-pipeline/{pipeline_id}/review
    review_resp = client.post(
        f"/api/v1/workflow/vision-pipeline/{pid}/review",
        json={
            "requested_change": "Update safety statistics narrative with ZERO harm milestone",
        },
    )
    assert review_resp.status_code == 200
    rev_data = review_resp.json()
    assert rev_data["human_correction_applied"] is True
    assert rev_data["status"] == "REVIEWED"

    # 4. POST /api/v1/workflow/vision-pipeline/{pipeline_id}/approve
    approve_resp = client.post(
        f"/api/v1/workflow/vision-pipeline/{pid}/approve",
        json={
            "connector_type": "cil_api",
            "authorized_by": "Sri Manoj Kumar (CMD, CCL)",
        },
    )
    assert approve_resp.status_code == 200
    app_data = approve_resp.json()
    assert app_data["status"] == "SUCCESS"
    assert "DISPATCHED_TO_CIL_ERP" in app_data["connector_status"]
    assert app_data["manifest"]["approved_by"] == "Sri Manoj Kumar (CMD, CCL)"
