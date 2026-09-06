"""
Unit and Integration Tests for Phase 33: Interactive Source Inspector & Coordinate Preview.
Section 1.4, 11 & 15 of Master Implementation Specification.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.domain.documents import BoundingBox
from core.domain.evidence import ProvenanceRecord, SpreadsheetCoordinate
from core.reports.visual_inspector import (
    VisualHighlight,
    VisualInspectorReport,
    VisualSourceInspector,
)

client = TestClient(app)


def test_generate_svg_overlay():
    inspector = VisualSourceInspector()
    highlights = [
        VisualHighlight(
            highlight_id="hl_01",
            label="Piparwar Production",
            bbox=BoundingBox(x0=50.0, y0=100.0, x1=250.0, y1=180.0),
            snippet="Raw coal production reached 14.5 MT",
            confidence=0.98,
        )
    ]

    svg = inspector.generate_svg_overlay(width=800.0, height=1100.0, highlights=highlights)
    assert "<svg" in svg
    assert 'viewBox="0 0 800.0 1100.0"' in svg
    assert 'id="hl_01"' in svg
    assert 'x="50.0"' in svg
    assert 'y="100.0"' in svg
    assert "Piparwar Production" in svg
    assert "</svg>" in svg


def test_render_spreadsheet_grid():
    inspector = VisualSourceInspector()
    coord = SpreadsheetCoordinate(
        workbook_name="monthly_prod_2024.xlsx",
        sheet_name="Piparwar_Summary",
        cell="C12",
        row=12,
        column=3,
        raw_value=14.52,
        formatted_value="14.52 MT",
    )

    grid_html = inspector.render_spreadsheet_grid(coord)
    assert "monthly_prod_2024.xlsx" in grid_html
    assert "Piparwar_Summary" in grid_html
    assert "C12" in grid_html
    assert "14.52 MT" in grid_html
    assert "spreadsheet-inspector" in grid_html


def test_create_inspector_from_provenance():
    inspector = VisualSourceInspector()
    record = ProvenanceRecord(
        provenance_id="prov_test_001",
        document_id="doc_annual_report",
        source_reference="/data/reports/CIL_AR_2024.pdf",
        page_number=42,
        bbox=BoundingBox(x0=120.0, y0=300.0, x1=450.0, y1=380.0),
        element_id="el_para_042",
        confidence=0.95,
        metadata={"text_snippet": "Capital expenditure on environmental mitigation"},
    )

    report = inspector.create_inspector_from_provenance(record)
    assert report.page_number == 42
    assert len(report.highlights) == 1
    assert "el_para_042" in report.svg_overlay
    assert "Capital expenditure" in report.svg_overlay
    assert "inspector-container" in report.html_preview


def test_visual_inspector_rest_api():
    payload = {
        "source_reference": "sample_document.pdf",
        "page_number": 3,
        "width": 800.0,
        "height": 1100.0,
        "highlights": [
            {
                "highlight_id": "hl_api_01",
                "label": "Total Offtake Metric",
                "bbox": {"x0": 100.0, "y0": 150.0, "x1": 300.0, "y1": 200.0},
                "snippet": "Offtake: 75.3 MT",
                "confidence": 0.99,
            }
        ],
    }

    resp = client.post("/api/v1/inspector/visualize", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_reference"] == "sample_document.pdf"
    assert "<svg" in data["svg_overlay"]
    assert "Total Offtake Metric" in data["svg_overlay"]
    assert len(data["highlights"]) == 1
