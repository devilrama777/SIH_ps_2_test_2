"""
Tests for Scanned PDF Detection and Local OCR Extraction — Section 7 of Master Implementation Plan.
"""
from __future__ import annotations

import io
from pathlib import Path
import fitz
from PIL import Image, ImageDraw

from core.domain.documents import DocumentType, ElementType
from core.extraction.pdf_extractor import PDFExtractor
from core.extraction.ocr.manager import MultiEngineOCRManager


def create_scanned_pdf(tmp_path: Path) -> Path:
    """Creates a 1-page PDF consisting solely of a rasterized image of text."""
    # 1. Create bitmap
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((60, 60), "CENTRAL COALFIELDS LIMITED", fill=(10, 20, 30))
    draw.text((60, 100), "Dhori Area Production & Despatch Summary", fill=(20, 20, 20))
    draw.rectangle([(60, 150), (540, 300)], outline=(100, 100, 100))
    draw.text((70, 170), "Total Raw Coal: 245,000 MT", fill=(0, 0, 0))
    draw.text((70, 210), "Despatch to Power Sector: 210,000 MT", fill=(0, 0, 0))

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    # 2. Insert image into empty fitz document without native text
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    page.insert_image(fitz.Rect(0, 0, 600, 800), stream=img_bytes.getvalue())

    pdf_path = tmp_path / "scanned_ccl_report.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def test_scanned_pdf_detection_and_automatic_ocr(tmp_path: Path):
    scanned_pdf_path = create_scanned_pdf(tmp_path)

    ocr_mgr = MultiEngineOCRManager(default_engine="pymupdf_raster_ocr")
    extractor = PDFExtractor(ocr_manager=ocr_mgr, auto_ocr=True)

    doc = extractor.extract(scanned_pdf_path)

    # Verifications
    assert doc.document_type == DocumentType.SCANNED_PDF
    assert len(doc.pages) == 1

    page = doc.pages[0]
    assert page.has_scanned_content is True
    assert page.ocr_applied is True
    assert len(page.elements) > 0

    # Ensure coordinates and provenance metadata
    ocr_elements = [el for el in page.elements if el.metadata.get("ocr")]
    assert len(ocr_elements) > 0
    first_el = ocr_elements[0]
    assert first_el.bbox is not None
    assert first_el.bbox.width > 0
    assert first_el.bbox.height > 0
    assert first_el.confidence > 0.0

    # Verify markdown representation contains extracted text
    assert len(doc.markdown_content.strip()) > 0
