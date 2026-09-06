"""
API tests for Agentic Editing and Source Traceability endpoints (Phase 9).
"""
import pytest
from fastapi.testclient import TestClient
from apps.processing.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_agentic_editing_and_traceability_api(client):
    # 1. Traceability resolution endpoint
    trace_resp = client.get("/api/v1/traceability/resolve?source_ref=Annual_Report_2024.pdf&page=12")
    assert trace_resp.status_code == 200
    trace_data = trace_resp.json()
    assert trace_data["source_reference"] == "Annual_Report_2024.pdf"
    assert trace_data["page_number"] == 12

    # 2. Generate a fresh report
    plan_resp = client.post(
        "/api/v1/reports/plan",
        json={
            "report_title": "BCCL Operational Performance Report",
            "reporting_period": "FY 2024-25",
            "subsidiary_name": "Bharat Coking Coal Limited",
            "template_name": "modern",
            "attach_evidence": False,
        },
    )
    assert plan_resp.status_code == 200
    plan_id = plan_resp.json()["plan_id"]

    gen_resp = client.post(
        "/api/v1/reports/generate",
        json={"plan_id": plan_id},
    )
    assert gen_resp.status_code == 200

    rep_resp = client.get(f"/api/v1/reports/{plan_id}")
    report_data = rep_resp.json()
    first_sec_id = report_data["sections"][0]["section_id"]

    # 3. Request Agentic Edit Proposal
    edit_resp = client.post(
        f"/api/v1/reports/{plan_id}/edit-agent",
        json={
            "section_id": first_sec_id,
            "instruction": "Revise and emphasize sustainable opencast mining measures and solar transitions.",
        },
    )
    assert edit_resp.status_code == 200
    proposal = edit_resp.json()
    assert proposal["report_id"] == plan_id
    assert proposal["section_id"] == first_sec_id
    assert proposal["status"] == "pending_review"
    assert len(proposal["diff_lines"]) >= 1

    proposal_id = proposal["proposal_id"]

    # 4. Accept Proposal
    accept_resp = client.post(f"/api/v1/reports/proposals/{proposal_id}/accept")
    assert accept_resp.status_code == 200
    updated_report = accept_resp.json()
    assert updated_report["version"] >= 2
