"""
Evidence and Provenance Model — Section 1.4 & Section 9 of Master Implementation Specification.

Every fact, figure, statement, table, or image generated in a report must be traceable
to its source evidence.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from core.domain.documents import BoundingBox


class PdfLocator(BaseModel):
    """Provenance locator for PDF documents."""
    type: Literal["pdf"] = "pdf"
    page_number: int
    bbox: Optional[BoundingBox] = None


class SpreadsheetLocator(BaseModel):
    """Exact location within a spreadsheet workbook."""
    type: Literal["spreadsheet"] = "spreadsheet"
    workbook_name: str
    sheet_name: str
    cell: Optional[str] = None  # e.g., 'G27'
    cell_range: Optional[str] = None  # e.g., 'A1:H30'
    row: Optional[int] = None
    column: Optional[int] = None
    raw_value: Optional[Any] = None
    formatted_value: Optional[str] = None


class DocxLocator(BaseModel):
    """Provenance locator for Word (.docx) documents."""
    type: Literal["docx"] = "docx"
    paragraph_index: Optional[int] = None
    table_index: Optional[int] = None
    heading_path: List[str] = Field(default_factory=list)


class ImageLocator(BaseModel):
    """Provenance locator for standalone or embedded images."""
    type: Literal["image"] = "image"
    width: Optional[int] = None
    height: Optional[int] = None
    bbox: Optional[BoundingBox] = None


class TextLocator(BaseModel):
    """Provenance locator for plaintext or markdown files."""
    type: Literal["text"] = "text"
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    char_offset: Optional[int] = None


# Discriminated union of all typed source locators
SourceLocator = Annotated[
    Union[PdfLocator, SpreadsheetLocator, DocxLocator, ImageLocator, TextLocator],
    Field(discriminator="type"),
]


# Backward compatibility alias
SpreadsheetCoordinate = SpreadsheetLocator


class ProvenanceRecord(BaseModel):
    """
    Immutable provenance metadata attached to every extracted element
    and generated claim.
    """
    provenance_id: str = Field(..., description="Unique provenance record ID (e.g., prov_00123)")
    document_id: str
    source_reference: str
    source_hash: Optional[str] = None
    locator: Optional[SourceLocator] = None
    page_number: Optional[int] = None
    bbox: Optional[BoundingBox] = None
    element_id: Optional[str] = None
    spreadsheet_coord: Optional[SpreadsheetCoordinate] = None
    extraction_method: str = Field(default="direct", description="Method used: direct, ocr, tabular, docx_parser, etc.")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    document_date: Optional[str] = None
    reporting_period: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceReference(BaseModel):
    """
    A specific piece of evidence linked to a statement, number, or table row
    in a generated report.
    """
    evidence_id: str
    provenance: ProvenanceRecord
    excerpt_text: Optional[str] = None
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    verified: bool = False
