"""
Image Extraction Engine — Section 18 of Master Implementation Specification.

Uses Pillow to analyze dimensions, resolution, color space, and metadata
for site photographs, mine charts, and diagrams.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

from core.domain.documents import (
    BoundingBox,
    CanonicalDocument,
    DocumentElement,
    DocumentType,
    ElementType,
    Page,
)
from core.extraction.base import BaseExtractor
from core.ingestion.discovery import DiscoveredFile
from core.provenance.tracker import generate_document_id, generate_element_id


class ImageExtractor(BaseExtractor):
    """Extracts metadata and coordinate profiles from image files."""

    def extract(self, file_path: Path, discovered: Optional[DiscoveredFile] = None) -> CanonicalDocument:
        path = Path(file_path)
        with open(path, "rb") as f:
            raw_bytes = f.read()

        file_size = len(raw_bytes)
        source_hash = hashlib.sha256(raw_bytes).hexdigest()
        doc_id = generate_document_id(str(path), raw_bytes)

        with Image.open(path) as img:
            width, height = img.size
            img_format = img.format or path.suffix.replace(".", "").upper()
            mode = img.mode
            dpi = img.info.get("dpi")

        aspect_ratio = round(width / height, 3) if height > 0 else 1.0
        el_id = generate_element_id(doc_id, 1, 1)

        element = DocumentElement(
            element_id=el_id,
            document_id=doc_id,
            type=ElementType.IMAGE,
            page_number=1,
            bbox=BoundingBox(x0=0.0, y0=0.0, x1=float(width), y1=float(height)),
            confidence=1.0,
            metadata={
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "format": img_format,
                "mode": mode,
                "dpi": dpi,
            },
        )

        fy = discovered.temporal.financial_year if discovered else None
        period = discovered.temporal.reporting_period if discovered else None
        dates = discovered.temporal.extracted_dates if discovered else []

        return CanonicalDocument(
            document_id=doc_id,
            source_reference=str(path.resolve()),
            source_hash=source_hash,
            document_type=DocumentType.IMAGE,
            reporting_year=fy,
            reporting_period=period,
            dates=dates,
            file_size_bytes=file_size,
            pages=[Page(page_number=1, width=float(width), height=float(height), elements=[element])],
            images=[{
                "element_id": el_id,
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "format": img_format,
            }],
            metadata={
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "format": img_format,
            },
        )
