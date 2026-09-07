"""
Tests for Statutory Report Generator, Export API, and Direct Download endpoints.
"""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.reports.compiler.statutory_report_generator import (
    generate_statutory_pdf,
    generate_statutory_docx,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_statutory_pdf_and_docx_generation(tmp_path):
    """Test generating 4-page publication PDF and DOCX matching exact preview report data."""
    pdf_path = tmp_path / "test_report.pdf"
    docx_path = tmp_path / "test_report.docx"

    # 1. Generate PDF
    out_pdf = generate_statutory_pdf(str(pdf_path))
    assert Path(out_pdf).exists()
    assert Path(out_pdf).stat().st_size > 10000

    # Verify PyMuPDF opens exactly 4 pages
    import pymupdf as fitz
    doc = fitz.open(out_pdf)
    assert len(doc) == 4
    
    # Page 1 contains key metrics and reserves
    p1_text = doc[0].get_text()
    assert "42.6 MT" in p1_text
    assert "Mining Lease Block ML-492" in p1_text
    assert "1.0 Executive Summary" in p1_text

    # Page 2 contains Table 2.1 and BH-2026-04 Prime G4
    p2_text = doc[1].get_text()
    assert "Table 2.1" in p2_text
    assert "BH-2026-04" in p2_text
    assert "9.6 m" in p2_text
    assert "Grade G4" in p2_text
    assert "Proved Cumulative Reserve" in p2_text

    # Page 3 contains Table 3.1 and IS 1350 assay
    p3_text = doc[2].get_text()
    assert "Table 3.1" in p3_text
    assert "Total Moisture" in p3_text
    assert "5,420 kcal/kg" in p3_text
    assert "Grade G8" in p3_text

    # Page 4 contains FoS 1.42 and statutory assurance
    p4_text = doc[3].get_text()
    assert "1.42" in p4_text
    assert "STATUTORY AUDITOR ASSURANCE" in p4_text
    assert "CIL/DGMS/STAT-2026/089" in p4_text
    doc.close()

    # 2. Generate DOCX
    out_docx = generate_statutory_docx(str(docx_path))
    assert Path(out_docx).exists()
    assert Path(out_docx).stat().st_size > 5000


def test_statutory_report_export_api_and_download(client, tmp_path):
    """Test POST /api/v1/reports/export and GET /api/v1/export/download."""
    target_pdf = tmp_path / "api_exported_report.pdf"

    # 1. Export PDF
    resp = client.post(
        "/api/v1/reports/export",
        json={
            "format": "pdf",
            "target_path": str(target_pdf),
            "report_title": "MineIntel_Technical_Evaluation_ML-492",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["format"] == "pdf"
    assert Path(data["saved_path"]).exists()
    assert data["size_bytes"] > 0

    # 2. Download PDF via download_url
    dl_url = data["download_url"]
    dl_resp = client.get(dl_url)
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "application/pdf"
    assert "attachment" in dl_resp.headers["content-disposition"]
    assert dl_resp.content.startswith(b"%PDF")
    assert len(dl_resp.content) == data["size_bytes"]
