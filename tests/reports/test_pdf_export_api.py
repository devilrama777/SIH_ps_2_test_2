"""
API tests for PDF Export and Rendering endpoints (Phase 8).
"""
import pytest
from fastapi.testclient import TestClient
from apps.processing.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_pdf_export_api_endpoints(client):
    # 1. First generate a report plan
    plan_resp = client.post(
        "/api/v1/reports/plan",
        json={
            "report_title": "Mahanadi Coalfields PDF Test Report",
            "reporting_period": "FY 2024-25",
            "subsidiary_name": "Mahanadi Coalfields Limited",
            "template_name": "modern",
            "attach_evidence": False,
        },
    )
    assert plan_resp.status_code == 200
    plan_id = plan_resp.json()["plan_id"]

    # 2. Generate report
    gen_resp = client.post(
        "/api/v1/reports/generate",
        json={"plan_id": plan_id},
    )
    assert gen_resp.status_code == 200

    # 3. Export to PDF via POST
    export_resp = client.post(f"/api/v1/reports/{plan_id}/export/pdf?template=modern")
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert export_data["report_id"] == plan_id
    assert export_data["page_count"] >= 1
    assert export_data["file_size_bytes"] > 0

    # 4. Download PDF file via GET
    get_pdf_resp = client.get(f"/api/v1/reports/{plan_id}/export/pdf?template=modern")
    assert get_pdf_resp.status_code == 200
    assert get_pdf_resp.headers["content-type"] == "application/pdf"
    assert len(get_pdf_resp.content) > 0

    # 5. Download HTML file via GET
    get_html_resp = client.get(f"/api/v1/reports/{plan_id}/export/html?template=modern")
    assert get_html_resp.status_code == 200
    assert "text/html" in get_html_resp.headers["content-type"]
    assert b"<!DOCTYPE html>" in get_html_resp.content
