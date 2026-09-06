"""
Tests for Section 28 Incremental Section Invalidation REST API.

Validates that:
- POST /api/v1/reports/incremental/invalidate computes dirty sections needing regeneration.
- Correctly preserves clean sections intact.
- Handles empty or non-matching source changes without error.
"""
from fastapi.testclient import TestClient

from apps.processing.server import app

client = TestClient(app)


def test_incremental_invalidation_endpoint():
    """Verify endpoint correctly identifies dirty and clean sections based on modified sources."""
    dummy_report = {
        "report_id": "rep_test_001",
        "sections": [
            {
                "section_id": "sec_exec",
                "title": "Executive Summary",
                "source_refs": ["CCL_Production_Offtake_FY24.xlsx", "CCL_Annual_Report_FY24_Highlights.txt"],
            },
            {
                "section_id": "sec_prod",
                "title": "Production Performance",
                "source_refs": ["CCL_Production_Offtake_FY24.xlsx"],
            },
            {
                "section_id": "sec_csr",
                "title": "CSR and Community Development",
                "source_refs": ["CSR_Community_Development_FY24.docx"],
            },
            {
                "section_id": "sec_audit",
                "title": "CAG Audit Compliance",
                "source_refs": ["CAG_Audit_Compliance_FY24.txt"],
            },
        ],
    }

    # Simulate change to production spreadsheet
    response = client.post(
        "/api/v1/reports/incremental/invalidate",
        json={
            "report_data": dummy_report,
            "changed_sources": ["CCL_Production_Offtake_FY24.xlsx"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_sections"] == 4
    assert set(data["dirty_sections"]) == {"sec_exec", "sec_prod"}
    assert set(data["clean_sections"]) == {"sec_csr", "sec_audit"}
    assert data["changed_sources"] == ["CCL_Production_Offtake_FY24.xlsx"]


def test_incremental_invalidation_unrelated_source():
    """Verify no sections are invalidated when an unreferenced source changes."""
    dummy_report = {
        "report_id": "rep_test_002",
        "sections": [
            {
                "section_id": "sec_csr",
                "title": "CSR and Community Development",
                "source_refs": ["CSR_Community_Development_FY24.docx"],
            },
        ],
    }

    response = client.post(
        "/api/v1/reports/incremental/invalidate",
        json={
            "report_data": dummy_report,
            "changed_sources": ["Completely_Unrelated_File.pdf"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_sections"] == 1
    assert data["dirty_sections"] == []
    assert data["clean_sections"] == ["sec_csr"]
