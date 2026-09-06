"""
Multi-Engine OCR & Layout Intelligence Manager — Section 7 of Master Implementation Plan.

Coordinates local OCR and layout recognition engines (PaddleOCR/PP-StructureV3,
Docling, and PyMuPDF Raster OCR), providing dynamic engine switching, automatic fallback,
and health monitoring under air-gapped constraints.
"""
from __future__ import annotations

import io
import logging
import time
from typing import Any, Dict, List, Optional

from core.domain.documents import DocumentElement
from core.extraction.ocr.base import (
    BaseOCREngine,
    OCRHealth,
    OCRPageResult,
)
from core.extraction.ocr.docling_engine import DoclingOCREngine
from core.extraction.ocr.paddle_engine import PaddleOCREngine
from core.extraction.ocr.pymupdf_engine import PyMuPDFOCREngine

logger = logging.getLogger(__name__)


class MultiEngineOCRManager:
    """
    Manager for local OCR and layout intelligence engines.
    """

    def __init__(self, default_engine: str = "paddleocr_ppstructure_v3") -> None:
        self._engines: Dict[str, BaseOCREngine] = {
            "paddleocr_ppstructure_v3": PaddleOCREngine(),
            "docling_layout_v1": DoclingOCREngine(),
            "pymupdf_raster_ocr": PyMuPDFOCREngine(),
        }
        self._active_engine_name = default_engine if default_engine in self._engines else "pymupdf_raster_ocr"

    def register_engine(self, engine: BaseOCREngine) -> None:
        """Registers or replaces an OCR engine."""
        self._engines[engine.engine_name] = engine
        logger.info("Registered OCR engine: %s", engine.engine_name)

    def get_active_engine_name(self) -> str:
        """Returns the currently configured default OCR engine."""
        return self._active_engine_name

    def set_active_engine(self, name: str) -> None:
        """Sets the active OCR engine."""
        if name not in self._engines:
            raise ValueError(f"Unknown OCR engine '{name}'. Available: {list(self._engines.keys())}")
        self._active_engine_name = name
        logger.info("Set active OCR engine to: %s", name)

    def list_engines(self) -> List[OCRHealth]:
        """Returns health and availability information for all registered engines."""
        healths = []
        for engine in self._engines.values():
            try:
                healths.append(engine.health_check())
            except Exception as exc:
                healths.append(
                    OCRHealth(
                        engine_name=engine.engine_name,
                        available=False,
                        error=str(exc),
                    )
                )
        return healths

    def get_engine(self, engine_name: Optional[str] = None) -> BaseOCREngine:
        """Returns an engine by name or the active default engine."""
        target = engine_name or self._active_engine_name
        if target in self._engines:
            return self._engines[target]
        logger.warning("Requested engine '%s' not found. Falling back to pymupdf_raster_ocr.", target)
        return self._engines.get("pymupdf_raster_ocr", list(self._engines.values())[0])

    def process_page_image(
        self,
        image_bytes: bytes,
        page_number: int = 1,
        engine_name: Optional[str] = None,
    ) -> OCRPageResult:
        """
        Processes a page image using the requested engine with automatic fallback.
        """
        primary = self.get_engine(engine_name)
        fallback_order = [
            primary,
            self._engines.get("pymupdf_raster_ocr"),
            self._engines.get("paddleocr_ppstructure_v3"),
            self._engines.get("docling_layout_v1"),
        ]

        attempted = set()
        last_exc: Optional[Exception] = None

        for eng in fallback_order:
            if not eng or eng.engine_name in attempted:
                continue
            attempted.add(eng.engine_name)

            try:
                result = eng.recognize_page(image_bytes=image_bytes, page_number=page_number)
                return result
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "OCR Engine '%s' failed on page %d: %s. Trying fallback.",
                    eng.engine_name,
                    page_number,
                    exc,
                )

        # If all fail, return an empty page result
        logger.error("All OCR engines failed on page %d. Last error: %s", page_number, last_exc)
        return OCRPageResult(
            page_number=page_number,
            lines=[],
            tables=[],
            overall_confidence=0.0,
            engine_name="none",
        )

    def process_page_pixmap(
        self,
        fitz_page: Any,
        page_number: int = 1,
        engine_name: Optional[str] = None,
        dpi: int = 150,
    ) -> OCRPageResult:
        """
        Renders a PyMuPDF (fitz) page to PNG pixmap bytes and performs OCR.
        """
        pix = fitz_page.get_pixmap(dpi=dpi)
        image_bytes = pix.tobytes("png")
        result = self.process_page_image(
            image_bytes=image_bytes,
            page_number=page_number,
            engine_name=engine_name,
        )
        return result
