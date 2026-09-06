"""
OCR and Layout Intelligence Package — Section 7 of Master Implementation Plan.
"""
from core.extraction.ocr.base import (
    BaseOCREngine,
    OCRHealth,
    OCRPageResult,
    OCRTableResult,
    OCRTextLine,
)
from core.extraction.ocr.benchmark import (
    EngineBenchmarkMetrics,
    OCRBenchmarkHarness,
    OCRBenchmarkReport,
)
from core.extraction.ocr.docling_engine import DoclingOCREngine
from core.extraction.ocr.manager import MultiEngineOCRManager
from core.extraction.ocr.paddle_engine import PaddleOCREngine
from core.extraction.ocr.pymupdf_engine import PyMuPDFOCREngine

__all__ = [
    "BaseOCREngine",
    "OCRHealth",
    "OCRPageResult",
    "OCRTableResult",
    "OCRTextLine",
    "EngineBenchmarkMetrics",
    "OCRBenchmarkHarness",
    "OCRBenchmarkReport",
    "DoclingOCREngine",
    "MultiEngineOCRManager",
    "PaddleOCREngine",
    "PyMuPDFOCREngine",
]
