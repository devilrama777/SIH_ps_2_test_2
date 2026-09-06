"""
API tests for Report Generation and Validation endpoints in server.py (Phases 5 & 6).
"""
import pytest
from fastapi.testclient import TestClient
from apps.processing.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_report_generation_and_validation_api(client):
    # 1. First generate a report plan
    plan_resp = client.post(
        "/api/v1/reports/plan",
        json={
            "report_title": "Northern Coalfields Limited Performance Report 2024-25",
            "reporting_period": "FY 2024-25",
            "subsidiary_name": "Northern Coalfields Limited",
            "template_name": "modern",
            "attach_evidence": False,
        },
    )
    assert plan_resp.status_code == 200
    plan_data = plan_resp.json()
    plan_id = plan_data["plan_id"]

    # 2. Generate the report from the plan
    gen_resp = client.post(
        "/api/v1/reports/generate",
        json={"plan_id": plan_id},
    )
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()
    assert gen_data["report_id"] == plan_id
    assert "validation" in gen_data
    assert gen_data["total_sections"] > 0

    # 3. Fetch the generated report
    rep_resp = client.get(f"/api/v1/reports/{plan_id}")
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()
    assert rep_data["report_id"] == plan_id
    assert len(rep_data["sections"]) > 0

    # 4. Fetch the validation findings
    val_resp = client.get(f"/api/v1/reports/{plan_id}/validation")
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data["report_id"] == plan_id
    assert "overall_status" in val_data

    # 5. List all reports
    list_resp = client.get("/api/v1/reports")
    assert list_resp.status_code == 200
    reports_list = list_resp.json()
    assert any(r["report_id"] == plan_id for r in reports_list)
