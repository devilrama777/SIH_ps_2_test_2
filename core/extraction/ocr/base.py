"""
Base OCR and Layout Intelligence Abstraction — Section 7 of Master Plan.

Defines the contract and data structures for local OCR engines, layout analyzers,
and table structure extractors.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.domain.documents import BoundingBox, DocumentElement, ElementType


class OCRTextLine(BaseModel):
    """An extracted line or paragraph block from an OCR pass."""
    text: str
    bbox: BoundingBox
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reading_order: int = 0
    is_heading: bool = False
    heading_level: int = 2


class OCRTableResult(BaseModel):
    """A tabular grid detected and reconstructed by layout analysis."""
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    bbox: Optional[BoundingBox] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    title: Optional[str] = None


class OCRPageResult(BaseModel):
    """Aggregated OCR and layout recognition result for a single document page."""
    page_number: int
    lines: List[OCRTextLine] = Field(default_factory=list)
    tables: List[OCRTableResult] = Field(default_factory=list)
    overall_confidence: float = 1.0
    latency_ms: float = 0.0
    engine_name: str = "base"
    page_width: float = 595.0
    page_height: float = 842.0

    def to_document_elements(self, document_id: str, start_index: int = 0) -> List[DocumentElement]:
        """Converts OCR lines and tables into CanonicalDocument elements."""
        elements: List[DocumentElement] = []
        counter = start_index

        # Add tables first
        for tbl in self.tables:
            counter += 1
            el_id = f"el_ocr_{document_id}_p{self.page_number}_{counter:04d}"
            elements.append(
                DocumentElement(
                    element_id=el_id,
                    document_id=document_id,
                    type=ElementType.TABLE,
                    page_number=self.page_number,
                    bbox=tbl.bbox,
                    text=f"Table: {tbl.title or 'Financial / Production Grid'}",
                    confidence=tbl.confidence,
                    reading_order=counter,
                    metadata={
                        "headers": tbl.headers,
                        "rows": tbl.rows,
                        "engine": self.engine_name,
                        "ocr": True,
                    },
                )
            )

        # Add text lines and headings
        for line in self.lines:
            counter += 1
            el_id = f"el_ocr_{document_id}_p{self.page_number}_{counter:04d}"
            el_type = ElementType.HEADING if line.is_heading else ElementType.PARAGRAPH
            elements.append(
                DocumentElement(
                    element_id=el_id,
                    document_id=document_id,
                    type=el_type,
                    page_number=self.page_number,
                    bbox=line.bbox,
                    text=line.text,
                    confidence=line.confidence,
                    reading_order=line.reading_order or counter,
                    metadata={
                        "level": line.heading_level if line.is_heading else None,
                        "engine": self.engine_name,
                        "ocr": True,
                    },
                )
            )

        return elements


class OCRHealth(BaseModel):
    """Health check status for an OCR engine."""
    engine_name: str
    available: bool
    hardware_backend: str = "CPU"  # "CPU", "CUDA", "ROCm", "MPS"
    version: str = "1.0.0"
    details: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class BaseOCREngine(ABC):
    """
    Abstract contract for local OCR and layout recognition engines.
    """

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Unique identifier of the OCR engine."""
        pass

    @abstractmethod
    def recognize_page(self, image_bytes: bytes, page_number: int = 1) -> OCRPageResult:
        """
        Executes OCR, layout analysis, and table recognition on a single page image.
        """
        pass

    @abstractmethod
    def health_check(self) -> OCRHealth:
        """
        Verifies local library availability, models, and execution backend.
        """
        pass
