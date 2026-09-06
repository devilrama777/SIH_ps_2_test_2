"""
Canonical Document Model — Section 9 of Master Implementation Specification.

This model provides a structured, format-agnostic internal representation
of documents ingested from any supported data source.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    DIGITAL_PDF = "digital_pdf"
    SCANNED_PDF = "scanned_pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    CSV = "csv"
    TXT = "txt"
    IMAGE = "image"
    REFERENCE_REPORT = "reference_report"
    UNKNOWN = "unknown"


class ElementType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    TABLE_CELL = "table_cell"
    SPREADSHEET_CELL = "spreadsheet_cell"
    IMAGE = "image"
    CHART = "chart"
    LINK = "link"
    HEADER_FOOTER = "header_footer"
    CAPTION = "caption"
    OTHER = "other"


class BoundingBox(BaseModel):
    """Normalized or coordinate bounding box [x0, y0, x1, y1]."""
    x0: float
    y0: float
    x1: float
    y1: float
    page_width: Optional[float] = None
    page_height: Optional[float] = None

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def to_list(self) -> List[float]:
        return [self.x0, self.y0, self.x1, self.y1]


class DocumentElement(BaseModel):
    """Atomic structural unit within a document preserving coordinate-level provenance."""
    element_id: str = Field(..., description="Unique deterministic element identifier (e.g., el_009821)")
    document_id: str = Field(..., description="Parent document identifier")
    type: ElementType
    page_number: Optional[int] = Field(default=None, description="1-indexed page number where element occurs")
    bbox: Optional[BoundingBox] = None
    text: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    reading_order: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Page(BaseModel):
    """Page representation within a multi-page document."""
    page_number: int
    width: Optional[float] = None
    height: Optional[float] = None
    elements: List[DocumentElement] = Field(default_factory=list)
    has_scanned_content: bool = False
    ocr_applied: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CanonicalDocument(BaseModel):
    """
    Canonical internal document model representing any ingested document.
    Independent of raw file format.
    """
    document_id: str = Field(..., description="Deterministic document identifier (e.g., doc_0042)")
    source_reference: str = Field(..., description="Filesystem path or URI of source document")
    source_hash: str = Field(..., description="SHA-256 hash of original raw content")
    document_type: DocumentType = DocumentType.UNKNOWN
    reporting_year: Optional[str] = None
    reporting_period: Optional[str] = None
    dates: List[str] = Field(default_factory=list, description="Extracted dates mentioned in content")
    file_size_bytes: int = 0
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    pages: List[Page] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    images: List[Dict[str, Any]] = Field(default_factory=list)
    links: List[Dict[str, Any]] = Field(default_factory=list)
    markdown_content: Optional[str] = Field(
        default=None,
        description="Secondary markdown representation for LLM context, leaving canonical model authoritative."
    )
