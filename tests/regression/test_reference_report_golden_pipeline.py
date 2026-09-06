"""
End-to-End Reference Report & Golden Dataset Pipeline Integration Test.
Section 30, Section 40, and Section 46 of Master Implementation Specification.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.evaluation.golden_harness import GoldenRegressionHarness
from core.evaluation.models import GoldenRegressionResult

client = TestClient(app)


def test_reference_report_golden_suite_execution(tmp_path: Path):
    golden_dir = "testdata/reference_report"
    work_dir = str(tmp_path / "golden_work")

    harness = GoldenRegressionHarness(golden_dir=golden_dir, workspace_dir=work_dir)
    result: GoldenRegressionResult = harness.run_suite()

    # 1. Structural and artifact verifications
    assert result.total_golden_fixtures >= 4
    assert result.ingested_documents >= 3
    assert result.generated_sections >= 2
    assert result.audit_chain_verified is True
    assert result.pdf_generated is True
    assert result.pdf_path is not None
    assert Path(result.pdf_path).exists()

    # 2. Section 32 quality metrics verification
    metrics = result.metrics
    assert metrics.provenance_coverage >= 0.80
    assert metrics.source_coverage >= 0.80
    assert metrics.numerical_error_rate == 0.0
    assert metrics.overall_quality_score >= 60.0

    # 3. Verify ground truth alignment
    gt_file = Path(golden_dir) / "ground_truth.json"
    assert gt_file.exists()
    gt_data = json.loads(gt_file.read_text(encoding="utf-8"))
    assert gt_data["subsidiary_name"] == "Central Coalfields Limited"
    assert gt_data["key_metrics"]["raw_coal_production_fy24_mt"] == 84.5


def test_production_wizard_pipeline_rest_api_lifecycle():
    # 1. Start pipeline on golden reference report folder
    start_payload = {
        "source_folder": "testdata/reference_report",
        "subsidiary": "CCL",
        "reporting_year": "FY 2023-24",
        "template_style": "modern",
        "run_sync": True,
    }
    start_resp = client.post("/api/v1/pipeline/start", json=start_payload)
    assert start_resp.status_code == 200
    session_data = start_resp.json()

    session_id = session_data["session_id"]
    report_id = session_data.get("report_id")
    assert session_id is not None
    assert len(session_id) > 10
    assert session_data["current_stage"] == "completed"
    assert session_data["progress_percent"] == 100


    # 2. Check session status
    status_resp = client.get(f"/api/v1/pipeline/status/{session_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["current_stage"] == "completed"

    # 3. Formal Executive Sign-off
    approve_payload = {
        "session_id": session_id,
        "approver_name": "Sri B. Veera Reddy (Director Tech/CMD)",
        "approval_notes": "Statutory audit and operational metrics verified against C&AG note.",
    }
    approve_resp = client.post("/api/v1/pipeline/approve", json=approve_payload)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["is_approved"] is True

    # 4. Authorized Connector Upload
    upload_payload = {"session_id": session_id}
    upload_resp = client.post("/api/v1/pipeline/upload", json=upload_payload)
    assert upload_resp.status_code == 200
    u_data = upload_resp.json()
    assert u_data["success"] is True


    # 5. Download PDF via direct alias route
    if report_id:
        pdf_resp = client.get(f"/api/v1/reports/{report_id}/pdf")
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"] == "application/pdf"
        assert len(pdf_resp.content) > 0
