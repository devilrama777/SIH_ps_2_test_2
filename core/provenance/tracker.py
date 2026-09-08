"""
Provenance Tracking and ID Generation — Section 1.4 & Section 9.

Generates deterministic, collision-resistant evidence and element identifiers.
Maintains relational mappings between source documents, extracted elements,
and report statements.
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Dict, Optional
from core.domain.documents import BoundingBox
from core.domain.evidence import ProvenanceRecord, SpreadsheetCoordinate, SourceLocator


def generate_document_id(source_reference: str, content_bytes: bytes) -> str:
    """Generate deterministic document ID based on source URI and SHA-256."""
    sha = hashlib.sha256(content_bytes).hexdigest()[:12]
    return f"doc_{sha}"


def generate_element_id(document_id: str, page_number: Optional[int], index: int) -> str:
    """Generate stable element ID within a document page."""
    pg = f"p{page_number}_" if page_number is not None else ""
    return f"el_{document_id}_{pg}{index:05d}"


def create_provenance_record(
    document_id: str,
    source_reference: str,
    element_id: Optional[str] = None,
    locator: Optional[SourceLocator] = None,
    page_number: Optional[int] = None,
    bbox: Optional[BoundingBox] = None,
    spreadsheet_coord: Optional[SpreadsheetCoordinate] = None,
    extraction_method: str = "direct",
    confidence: Optional[float] = None,
    document_date: Optional[str] = None,
    reporting_period: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> ProvenanceRecord:
    """Create a fully-qualified ProvenanceRecord with a unique provenance ID."""
    prov_id = f"prov_{uuid.uuid4().hex[:10]}"
    return ProvenanceRecord(
        provenance_id=prov_id,
        document_id=document_id,
        source_reference=source_reference,
        element_id=element_id,
        locator=locator,
        page_number=page_number,
        bbox=bbox,
        spreadsheet_coord=spreadsheet_coord,
        extraction_method=extraction_method,
        confidence=confidence,
        document_date=document_date,
        reporting_period=reporting_period,
        metadata=metadata or {},
    )
