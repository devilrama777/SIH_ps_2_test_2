"""
Tests for PDFExtractor using fitz (PyMuPDF).
"""
from pathlib import Path
import fitz
from core.domain.documents import DocumentType, ElementType
from core.extraction.pdf_extractor import PDFExtractor


def test_pdf_extraction_digital(tmp_path: Path):
    """Create a digital PDF fixture and verify bounding box and text extraction."""
    pdf_path = tmp_path / "test_digital.pdf"

    # Generate a standard 2-page PDF
    doc = fitz.open()
    page1 = doc.new_page(width=595, height=842)
    page1.insert_text((50, 80), "COAL INDIA LIMITED SUBSIDIARY REPORT", fontsize=16)
    page1.insert_text((50, 120), "During FY25, overall raw coal production reached 773.6 MT.", fontsize=11)

    page2 = doc.new_page(width=595, height=842)
    page2.insert_text((50, 80), "OPERATIONAL HIGHLIGHTS", fontsize=14)
    page2.insert_text((50, 120), "Dispatches to the power sector recorded a growth of 5.8%.", fontsize=11)
    doc.save(str(pdf_path))
    doc.close()

    extractor = PDFExtractor()
    canonical = extractor.extract(pdf_path)

    assert canonical.document_type == DocumentType.DIGITAL_PDF
    assert len(canonical.pages) == 2
    assert canonical.pages[0].width == 595.0
    assert canonical.pages[0].height == 842.0

    # Verify elements and bounding boxes
    elements = canonical.pages[0].elements
    assert len(elements) >= 2

    # Check headings and paragraphs
    heading_el = [e for e in elements if e.type == ElementType.HEADING]
    assert len(heading_el) >= 1
    assert "COAL INDIA LIMITED" in heading_el[0].text

    # Verify bounding box exists and is valid
    assert heading_el[0].bbox is not None
    assert heading_el[0].bbox.x0 >= 0
    assert heading_el[0].bbox.y0 >= 0
    assert heading_el[0].bbox.x1 > heading_el[0].bbox.x0
    assert heading_el[0].confidence == 1.0

    # Verify secondary markdown content
    assert canonical.markdown_content is not None
    assert "COAL INDIA LIMITED" in canonical.markdown_content
