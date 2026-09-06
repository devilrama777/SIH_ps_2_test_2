"""
Tests for CSVExtractor and TextExtractor.
"""
from pathlib import Path
from core.domain.documents import DocumentType, ElementType
from core.extraction.text_csv_extractor import CSVExtractor, TextExtractor


def test_csv_extraction(tmp_path: Path):
    """Verify CSV header, rows, and cell element extraction."""
    csv_path = tmp_path / "production.csv"
    csv_path.write_text("Subsidiary,Target_MT,Actual_MT\nECL,40.0,42.5\nBCCL,35.0,36.2\n")

    extractor = CSVExtractor()
    canonical = extractor.extract(csv_path)

    assert canonical.document_type == DocumentType.CSV
    assert len(canonical.tables) == 1
    table = canonical.tables[0]
    assert table["headers"] == ["Subsidiary", "Target_MT", "Actual_MT"]
    assert table["row_count"] == 3

    # Check cell elements
    elements = canonical.pages[0].elements
    assert len(elements) == 9  # 3 rows x 3 cols
    assert elements[0].type == ElementType.TABLE_CELL
    assert elements[0].text == "Subsidiary"


def test_text_extraction(tmp_path: Path):
    """Verify plain text paragraph separation and heading detection."""
    txt_path = tmp_path / "notes.txt"
    txt_path.write_text("Executive Summary\n\nAll targets achieved.\n\nSafety protocol updated.")

    extractor = TextExtractor()
    canonical = extractor.extract(txt_path)

    assert canonical.document_type == DocumentType.TXT
    elements = canonical.pages[0].elements
    assert len(elements) == 3
    assert elements[0].type == ElementType.HEADING
    assert elements[0].text == "Executive Summary"
    assert elements[1].type == ElementType.PARAGRAPH
