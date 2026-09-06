"""
Integration tests for Pipeline API Endpoints.
Phase 13 (Section 33 & 46).
"""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.evaluation.golden_dataset import GoldenDatasetBuilder


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def golden_source_dir(tmp_path: Path) -> Path:
    builder = GoldenDatasetBuilder(base_dir=str(tmp_path / "golden_api_input"))
    return builder.build_dataset()


def test_pipeline_api_lifecycle(client: TestClient, golden_source_dir: Path, tmp_path: Path):
    # 1. Test Available Connectors Endpoint
    conns_res = client.get("/api/v1/connectors/available")
    assert conns_res.status_code == 200
    connectors = conns_res.json()
    assert len(connectors) == 4
    conn_types = [c["type"] for c in connectors]
    assert "local_folder" in conn_types
    assert "network_share" in conn_types
    assert "sharepoint_dms" in conn_types
    assert "cil_sap_erp_api" in conn_types

    # 2. Start Pipeline Synchronously
    start_payload = {
        "source_folder": str(golden_source_dir),
        "subsidiary": "Northern Coalfields Limited",
        "reporting_year": "2024-25",
        "reporting_period": "Annual",
        "template_style": "classic",
        "run_sync": True,
    }
    start_res = client.post("/api/v1/pipeline/start", json=start_payload)
    assert start_res.status_code == 200
    session_data = start_res.json()
    session_id = session_data["session_id"]
    assert session_data["current_stage"] == "completed"
    assert session_data["progress_percent"] == 100.0
    assert session_data["pdf_path"] is not None

    # 3. Retrieve Pipeline Status
    status_res = client.get(f"/api/v1/pipeline/status/{session_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["session_id"] == session_id
    assert status_data["report_id"] is not None
    assert status_data["metrics"]["provenance_coverage"] >= 0.85

    # 4. Attempt Upload Before Approval (Should fail with 400 PermissionError)
    upload_fail_res = client.post(
        "/api/v1/pipeline/upload",
        json={"session_id": session_id},
    )
    assert upload_fail_res.status_code == 400
    assert "Authorized upload blocked" in upload_fail_res.json()["detail"]

    # 5. Formally Approve Report
    approve_res = client.post(
        "/api/v1/pipeline/approve",
        json={
            "session_id": session_id,
            "approver_name": "Sri A. K. Singh (CMD / Executive Authority)",
            "approval_notes": "Financial figures reconciled with statutory audit. Approved for release.",
        },
    )
    assert approve_res.status_code == 200
    approved_session = approve_res.json()
    assert approved_session["is_approved"] is True
    assert approved_session["approved_by"] == "Sri A. K. Singh (CMD / Executive Authority)"

    # 6. Execute Authorized Enterprise Upload
    upload_dest = str(tmp_path / "enterprise_portal_share" / "Final_Report.pdf")
    upload_res = client.post(
        "/api/v1/pipeline/upload",
        json={
            "session_id": session_id,
            "destination_target": upload_dest,
        },
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert upload_data["success"] is True
    assert Path(upload_dest).exists()
    assert Path(upload_dest).stat().st_size > 0
    assert Path(upload_dest).with_suffix(".manifest.json").exists()
