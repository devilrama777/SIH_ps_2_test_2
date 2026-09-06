"""
Tests for Local OCR Engines and MultiEngineOCRManager — Section 7 of Master Implementation Plan.
"""
from __future__ import annotations

import io
import pytest
from PIL import Image, ImageDraw

from core.extraction.ocr.base import OCRPageResult, OCRHealth
from core.extraction.ocr.docling_engine import DoclingOCREngine
from core.extraction.ocr.manager import MultiEngineOCRManager
from core.extraction.ocr.paddle_engine import PaddleOCREngine
from core.extraction.ocr.pymupdf_engine import PyMuPDFOCREngine


def create_sample_page_image() -> bytes:
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "EASTERN COALFIELDS LIMITED", fill=(0, 0, 0))
    draw.text((50, 100), "Safety audit inspection report - Rajmahal OCP.", fill=(0, 0, 0))
    draw.rectangle([(50, 150), (550, 250)], outline=(0, 0, 0))
    draw.text((60, 170), "Production: 45,000 MT", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_pymupdf_ocr_engine_execution():
    engine = PyMuPDFOCREngine()
    assert engine.engine_name == "pymupdf_raster_ocr"

    health = engine.health_check()
    assert health.available is True
    assert health.hardware_backend == "CPU"

    img_bytes = create_sample_page_image()
    res = engine.recognize_page(img_bytes, page_number=1)
    assert isinstance(res, OCRPageResult)
    assert res.page_number == 1
    assert res.overall_confidence > 0.0
    assert len(res.lines) > 0


def test_paddle_ocr_engine_fallback_and_health():
    engine = PaddleOCREngine()
    assert engine.engine_name == "paddleocr_ppstructure_v3"

    health = engine.health_check()
    assert health.available is True

    img_bytes = create_sample_page_image()
    res = engine.recognize_page(img_bytes, page_number=2)
    assert isinstance(res, OCRPageResult)
    assert res.page_number == 2
    assert len(res.lines) > 0
    assert res.lines[0].bbox.width > 0


def test_docling_ocr_engine_fallback_and_health():
    engine = DoclingOCREngine()
    assert engine.engine_name == "docling_layout_v1"

    health = engine.health_check()
    assert health.available is True

    img_bytes = create_sample_page_image()
    res = engine.recognize_page(img_bytes, page_number=3)
    assert isinstance(res, OCRPageResult)
    assert res.page_number == 3
    assert len(res.lines) > 0


def test_multi_engine_manager_switching_and_fallback():
    manager = MultiEngineOCRManager(default_engine="pymupdf_raster_ocr")
    assert manager.get_active_engine_name() == "pymupdf_raster_ocr"

    engines = manager.list_engines()
    assert len(engines) == 3
    engine_names = [e.engine_name for e in engines]
    assert "paddleocr_ppstructure_v3" in engine_names
    assert "docling_layout_v1" in engine_names
    assert "pymupdf_raster_ocr" in engine_names

    # Test switching
    manager.set_active_engine("paddleocr_ppstructure_v3")
    assert manager.get_active_engine_name() == "paddleocr_ppstructure_v3"

    with pytest.raises(ValueError):
        manager.set_active_engine("unknown_cloud_ocr")

    # Test processing
    img_bytes = create_sample_page_image()
    res = manager.process_page_image(img_bytes, page_number=1)
    assert isinstance(res, OCRPageResult)
    assert res.page_number == 1
    assert len(res.lines) > 0

    # Convert to DocumentElement
    doc_elements = res.to_document_elements(document_id="doc_test_001")
    assert len(doc_elements) > 0
    assert doc_elements[0].document_id == "doc_test_001"
    assert doc_elements[0].confidence > 0.0
