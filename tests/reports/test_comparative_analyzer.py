"""
Tests for Section 14 Previous Report Comparative Analyzer & YoY Synthesis,
Section 19 PDF Branding & Print Rules, and Section 35 Air-Gapped Diagnostics.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.reports.planner.reference_analyzer import (
    ComparativeReportAnalyzer,
    StructuralChangeReport,
    YoYComparativeTable,
)
from core.domain.reports import NarrativeBlock, Report, ReportSection, SectionType
from core.reports.pdf.html_builder import ReportHtmlBuilder

client = TestClient(app)


def test_comparative_analyzer_structural_comparison():
    analyzer = ComparativeReportAnalyzer()

    prior_sections = [
        "1. Corporate Mandate & Profile",
        "2. Chairman's Statement",
        "3. Operational & Production Performance",
        "4. Financial Highlights",
        "5. Legacy Obsolete Chapter",
    ]

    current_sections = [
        "1. Corporate Mandate & Profile",
        "2. Chairman & Managing Director Statement",  # Renamed
        "3. Operational & Production Performance",
        "4. Financial Highlights",
        "5. ESG & Green Initiatives",  # Added
    ]

    report: StructuralChangeReport = analyzer.compare_structures(
        prior_sections=prior_sections,
        current_sections=current_sections,
        prior_period="FY 2022-23",
        current_period="FY 2023-24",
    )

    assert report.prior_period == "FY 2022-23"
    assert report.current_period == "FY 2023-24"
    assert "1. Corporate Mandate & Profile" in report.retained_sections
    assert "3. Operational & Production Performance" in report.retained_sections
    assert "5. ESG & Green Initiatives" in report.added_sections
    assert "5. Legacy Obsolete Chapter" in report.removed_sections
    assert any(r["current"] == "2. Chairman & Managing Director Statement" for r in report.renamed_sections)
    assert report.structural_similarity_score > 60.0


def test_comparative_analyzer_yoy_table_synthesis():
    analyzer = ComparativeReportAnalyzer()

    prior_metrics = {
        "raw_coal_production": 703.20,
        "coal_offtake": 694.70,
        "overburden_removal": 1650.40,
        "gross_revenue": 127627.0,
        "net_profit": 28125.0,
        "fatal_accidents": 24,
    }

    current_metrics = {
        "raw_coal_production": 773.60,
        "coal_offtake": 753.50,
        "overburden_removal": 1964.80,
        "gross_revenue": 142340.0,
        "net_profit": 37402.0,
        "fatal_accidents": 18,
    }

    table: YoYComparativeTable = analyzer.generate_yoy_comparative_table(
        category="operational",
        prior_metrics=prior_metrics,
        current_metrics=current_metrics,
        prior_period="FY 2022-23",
        current_period="FY 2023-24",
        source_ref="CIL_Operational_Review_FY24.pdf:P8",
    )

    assert table.table_id.startswith("yoy_operational_")
    assert len(table.rows) == 6

    # Verify Production delta
    prod_row = next(r for r in table.rows if "Raw Coal" in r.indicator)
    assert prod_row.prior_value == 703.20
    assert prod_row.current_value == 773.60
    assert prod_row.absolute_change == 70.40
    assert prod_row.percentage_change == 10.01
    assert prod_row.trend == "positive"

    # Verify Fatal Accidents delta (decrease is positive)
    acc_row = next(r for r in table.rows if "Fatal Accidents" in r.indicator)
    assert acc_row.prior_value == 24.0
    assert acc_row.current_value == 18.0
    assert acc_row.absolute_change == -6.0
    assert acc_row.percentage_change == -25.0
    assert acc_row.trend == "positive"  # Lower accidents is better

    # Test conversion to standard report table dictionary
    table_dict = table.to_table_dict()
    assert table_dict["is_yoy_comparative"] is True
    assert "Performance Indicator" in table_dict["headers"]
    assert "Growth (%)" in table_dict["headers"]
    assert len(table_dict["rows"]) == 6


def test_html_builder_print_hardening_and_running_headers():
    builder = ReportHtmlBuilder()

    sec = ReportSection(
        section_id="sec_ops",
        title="Operational Review",
        section_type=SectionType.MANDATORY,
        narrative_blocks=[
            NarrativeBlock(block_id="b1", text="Production achieved all time high.")
        ],
    )

    rep = Report(
        report_id="rep_print_test",
        title="BCCL Annual Report FY 2023-24",
        subsidiary_name="Bharat Coking Coal Limited",
        reporting_period="FY 2023-24",
        sections=[sec],
    )

    html_out = builder.build_html(rep, template_name="modern")

    # Assert dynamic running headers contain subsidiary name
    assert "BHARAT COKING COAL LIMITED" in html_out
    assert "FY 2023-24 — PAGE" in html_out

    # Assert cover page header suppression
    assert "@page :first" in html_out

    # Assert table break protection
    assert "break-inside: avoid;" in html_out

    # Assert TOC anchor linking
    assert '<a href="#sec_ops"' in html_out


def test_rest_api_section_14_and_diagnostics():
    # 1. Test POST /api/v1/reports/compare-structures
    compare_payload = {
        "prior_sections": ["1. Vision & Mission", "2. Mining Operations", "3. Legacy"],
        "current_sections": ["1. Vision & Mission", "2. Mining Operations & Tech", "4. Solar ESG"],
        "prior_period": "FY 2022-23",
        "current_period": "FY 2023-24",
    }
    resp = client.post("/api/v1/reports/compare-structures", json=compare_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "1. Vision & Mission" in data["retained_sections"]
    assert "4. Solar ESG" in data["added_sections"]
    assert "3. Legacy" in data["removed_sections"]

    # 2. Test POST /api/v1/reports/generate-yoy-table
    table_payload = {
        "category": "financial",
        "prior_metrics": {"gross_revenue": 10000.0, "net_profit": 1500.0},
        "current_metrics": {"gross_revenue": 12500.0, "net_profit": 2100.0},
        "prior_period": "FY 2022-23",
        "current_period": "FY 2023-24",
    }
    table_resp = client.post("/api/v1/reports/generate-yoy-table", json=table_payload)
    assert table_resp.status_code == 200
    t_data = table_resp.json()
    assert len(t_data["rows"]) == 2
    assert t_data["rows"][0]["absolute_change"] == 2500.0
    assert t_data["rows"][0]["percentage_change"] == 25.0

    # 3. Test POST /api/v1/observability/export-diagnostics
    diag_resp = client.post("/api/v1/observability/export-diagnostics", json={"bundle_name": "test_phase20"})
    assert diag_resp.status_code == 200
    diag_data = diag_resp.json()
    assert "bundle_filename" in diag_data
    assert "sha256_hash" in diag_data
    assert len(diag_data["sha256_hash"]) == 64
    bundle_name = diag_data["bundle_filename"]

    # 4. Test GET /api/v1/observability/download-diagnostics/{bundle_filename}
    dl_resp = client.get(f"/api/v1/observability/download-diagnostics/{bundle_name}")
    assert dl_resp.status_code == 200
    assert len(dl_resp.content) > 0
