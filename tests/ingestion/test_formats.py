"""
Tests for Section 3 input format detection and exclusion.
"""
from core.ingestion.formats import (
    DocumentFormat,
    detect_format,
    is_disallowed_format,
    is_supported_format,
)


def test_supported_formats():
    """Verify that all Section 3 specified formats are correctly recognized."""
    assert is_supported_format("annual_report.pdf") is True
    assert is_supported_format("summary.docx") is True
    assert is_supported_format("financials.xlsx") is True
    assert is_supported_format("production.csv") is True
    assert is_supported_format("notes.txt") is True
    assert is_supported_format("site_photo.jpg") is True
    assert is_supported_format("diagram.png") is True
    assert is_supported_format("scanned_page.tiff") is True


def test_disallowed_formats():
    """Verify that archives and presentations are explicitly rejected per Section 3."""
    assert is_supported_format("bundle.zip") is False
    assert is_disallowed_format("bundle.zip") is True

    assert is_supported_format("presentation.pptx") is False
    assert is_disallowed_format("presentation.pptx") is True

    assert is_supported_format("archive.tar.gz") is False


def test_detect_format_mapping():
    """Verify format enum detection."""
    assert detect_format("doc.pdf") == DocumentFormat.PDF
    assert detect_format("sheet.xlsx") == DocumentFormat.XLSX
    assert detect_format("data.csv") == DocumentFormat.CSV
    assert detect_format("image.jpeg") == DocumentFormat.IMAGE
    assert detect_format("script.py") == DocumentFormat.UNSUPPORTED
