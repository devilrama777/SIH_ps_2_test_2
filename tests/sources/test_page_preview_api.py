"""
Tests for Page Preview Rendering & Dual-Template Live HTML Preview — Sections 20 & 21.
"""
from __future__ import annotations

import io
from pathlib import Path
from fastapi.testclient import TestClient
import fitz
from PIL import Image

from apps.processing.server import app
from core.domain.reports import Report, ReportSection, NarrativeBlock
from core.domain.documents import CanonicalDocument, Page, DocumentElement, ElementType, BoundingBox, DocumentType


client = TestClient(app)


def test_sources_page_preview_synthetic_and_bbox():
    # 1. Test basic page preview without documents (generates clean synthetic preview)
    resp = client.get("/api/v1/sources/page-preview?source_reference=CCL_Test_Doc.pdf&page_number=2&bbox=50,100,450,250")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    img = Image.open(io.BytesIO(resp.content))
    assert img.width > 0
    assert img.height > 0


def test_sources_page_preview_with_canonical_document(tmp_path: Path):
    # Create canonical doc
    doc_id = "doc_preview_test_001"
    canon = CanonicalDocument(
        document_id=doc_id,
        source_reference=str(tmp_path / "test.pdf"),
        source_hash="sha256_mock_hash",
        document_type=DocumentType.DIGITAL_PDF,
        pages=[
            Page(
                page_number=1,
                width=600.0,
                height=800.0,
                elements=[
                    DocumentElement(
                        element_id="el_001",
                        document_id=doc_id,
                        type=ElementType.HEADING,
                        page_number=1,
                        text="BHARAT COKING COAL LIMITED HIGHLIGHTS",
                        bbox=BoundingBox(x0=50, y0=50, x1=500, y1=90),
                    )
                ]
            )
        ]
    )
    doc_dir = Path("data/workspace/canonical_documents")
    doc_dir.mkdir(parents=True, exist_ok=True)
    (doc_dir / f"{doc_id}.json").write_text(canon.model_dump_json(), encoding="utf-8")

    # Request preview highlighting el_001
    resp = client.get(f"/api/v1/sources/page-preview?document_id={doc_id}&page_number=1&element_id=el_001")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    img = Image.open(io.BytesIO(resp.content))
    assert img.width > 0


def test_reports_preview_html_both_templates():
    rep_id = "rep_preview_test_001"
    rep = Report(
        report_id=rep_id,
        title="Live HTML Preview Test",
        reporting_period="FY 2024-25",
        subsidiary_name="Central Coalfields Limited",
        sections=[
            ReportSection(
                section_id="sec_01",
                title="Operational Highlights",
                narrative_blocks=[
                    NarrativeBlock(
                        block_id="b_01",
                        text="Coal production reached historic heights with zero safety breaches.",
                    )
                ]
            )
        ]
    )
    rep_dir = Path("data/workspace/reports")
    rep_dir.mkdir(parents=True, exist_ok=True)
    (rep_dir / f"{rep_id}.json").write_text(rep.model_dump_json(), encoding="utf-8")

    # 1. Preview classic
    resp_classic = client.get(f"/api/v1/reports/{rep_id}/preview-html?template=classic")
    assert resp_classic.status_code == 200
    assert resp_classic.headers["content-type"] == "text/html; charset=utf-8"
    assert "Live HTML Preview Test" in resp_classic.text
    assert "Central Coalfields Limited" in resp_classic.text

    # 2. Preview modern
    resp_modern = client.get(f"/api/v1/reports/{rep_id}/preview-html?template=modern")
    assert resp_modern.status_code == 200
    assert resp_modern.headers["content-type"] == "text/html; charset=utf-8"
    assert "Live HTML Preview Test" in resp_modern.text
