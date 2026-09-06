"""
Tests for Section 5 Case A and Case B temporal extraction heuristics.
"""
from core.ingestion.temporal import extract_temporal_metadata


def test_case_a_folder_hierarchy():
    """Verify Case A: dates embedded in folder structure (e.g. 2024-25/Q4/March/)."""
    path = "C:/data/2024-25/Q4/March/production.xlsx"
    meta = extract_temporal_metadata(path)

    assert meta.financial_year == "2024-25"
    assert meta.reporting_quarter == "Q4"
    assert meta.reporting_month == "March"
    assert meta.reporting_period == "March 2024"
    assert meta.confidence > 0.7


def test_case_b_embedded_filename():
    """Verify Case B: dates embedded in document filename."""
    path = "C:/data/documents/CIL_Annual_Report_2024_25_Full_Data_Report.pdf"
    meta = extract_temporal_metadata(path)

    assert meta.financial_year == "2024-25"
    assert meta.reporting_period == "FY 2024-25"
    assert meta.source_method == "filename"


def test_case_b_month_and_year_in_filename():
    """Verify filename containing month and year."""
    path = "C:/data/unorganized/coal_production_report_march_2025.csv"
    meta = extract_temporal_metadata(path)

    assert meta.reporting_month == "March"
    assert meta.reporting_period == "March 2025"
    assert meta.confidence >= 0.75


def test_iso_date_in_filename():
    """Verify ISO formatted date in file path."""
    path = "C:/data/audit/2025-03-31_environmental_clearance.pdf"
    meta = extract_temporal_metadata(path)

    assert "2025-03-31" in meta.extracted_dates
    assert meta.confidence >= 0.9
