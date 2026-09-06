"""
FastAPI integration tests for Report Planner endpoints (Sections 13, 14, 15).
"""
import pytest
from fastapi.testclient import TestClient
from apps.processing.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_create_report_plan_endpoint(client):
    payload = {
        "report_title": "CIL Subsidiary Annual Report FY 2024-25",
        "reporting_period": "FY 2024-25",
        "subsidiary_name": "Bharat Coking Coal Limited",
        "template_name": "modern",
        "attach_evidence": False,
    }

    res = client.post("/api/v1/reports/plan", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "plan_id" in data
    assert data["report_title"] == "CIL Subsidiary Annual Report FY 2024-25"
    assert len(data["sections"]) >= 9
    assert data["total_planned_sections"] > 10

    # Retrieve specific plan
    plan_id = data["plan_id"]
    get_res = client.get(f"/api/v1/reports/plans/{plan_id}")
    assert get_res.status_code == 200
    plan_data = get_res.json()
    assert plan_data["plan_id"] == plan_id

    # List plans
    list_res = client.get("/api/v1/reports/plans")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
