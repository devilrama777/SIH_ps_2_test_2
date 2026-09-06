"""
PDF Extraction Engine — Section 7 & Section 9 of Master Implementation Specification.

Uses PyMuPDF (fitz) to extract text blocks, bounding boxes, reading order,
images, links, and table regions from digital PDFs.
Detects scanned pages (low/zero native text + full-page raster images) and flags them for OCR.
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF

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


class PDFExtractor(BaseExtractor):
    """
    Extracts structured representation from PDF files.
    Distinguishes digital PDFs from scanned PDFs and preserves coordinate bounding boxes.
    """

    def extract(self, file_path: Path, discovered: Optional[DiscoveredFile] = None) -> CanonicalDocument:
        path = Path(file_path)
        with open(path, "rb") as f:
            raw_bytes = f.read()

        file_size = len(raw_bytes)
        source_hash = hashlib.sha256(raw_bytes).hexdigest()
        doc_id = generate_document_id(str(path), raw_bytes)

        pdf_doc = fitz.open(stream=raw_bytes, filetype="pdf")
        total_pages = len(pdf_doc)

        pages: List[Page] = []
        all_links: List[Dict[str, Any]] = []
        all_images: List[Dict[str, Any]] = []
        markdown_sections: List[str] = []
        scanned_page_count = 0

        element_counter = 0

        for page_idx in range(total_pages):
            page_num = page_idx + 1
            fitz_page = pdf_doc[page_idx]
            rect = fitz_page.rect
            p_width, p_height = rect.width, rect.height

            # 1. Extract links
            page_links = fitz_page.get_links()
            for lnk in page_links:
                uri = lnk.get("uri")
                from_rect = lnk.get("from")
                if uri:
                    all_links.append({
                        "document_id": doc_id,
                        "page_number": page_num,
                        "uri": uri,
                        "bbox": [from_rect.x0, from_rect.y0, from_rect.x1, from_rect.y1] if from_rect else None,
                    })

            # 2. Extract text blocks with coordinates
            # text_page.get_text("blocks") -> (x0, y0, x1, y1, text, block_no, block_type)
            # block_type 0 = text, 1 = image
            blocks = fitz_page.get_text("blocks")
            page_elements: List[DocumentElement] = []
            page_text_total = ""

            for b in blocks:
                x0, y0, x1, y1, b_text, b_num, b_type = b[:7]
                bbox = BoundingBox(
                    x0=round(x0, 2),
                    y0=round(y0, 2),
                    x1=round(x1, 2),
                    y1=round(y1, 2),
                    page_width=round(p_width, 2),
                    page_height=round(p_height, 2),
                )

                if b_type == 0:
                    cleaned_text = b_text.strip()
                    if not cleaned_text:
                        continue
                    page_text_total += cleaned_text + " "

                    # Heading detection heuristic: single-line, uppercase, or ends without period
                    lines = [ln.strip() for ln in cleaned_text.splitlines() if ln.strip()]
                    is_heading = len(lines) == 1 and (len(cleaned_text) < 100) and (
                        cleaned_text.isupper() or cleaned_text.istitle() or not cleaned_text.endswith(".")
                    )

                    el_type = ElementType.HEADING if is_heading else ElementType.PARAGRAPH
                    element_counter += 1
                    el_id = generate_element_id(doc_id, page_num, element_counter)

                    page_elements.append(
                        DocumentElement(
                            element_id=el_id,
                            document_id=doc_id,
                            type=el_type,
                            page_number=page_num,
                            bbox=bbox,
                            text=cleaned_text,
                            reading_order=b_num,
                            confidence=1.0,  # Native text
                        )
                    )

                    if is_heading:
                        markdown_sections.append(f"\n### {cleaned_text}\n")
                    else:
                        markdown_sections.append(f"{cleaned_text}\n")

                elif b_type == 1:
                    # Raster image block
                    element_counter += 1
                    el_id = generate_element_id(doc_id, page_num, element_counter)
                    page_elements.append(
                        DocumentElement(
                            element_id=el_id,
                            document_id=doc_id,
                            type=ElementType.IMAGE,
                            page_number=page_num,
                            bbox=bbox,
                            reading_order=b_num,
                            confidence=1.0,
                        )
                    )
                    all_images.append({
                        "element_id": el_id,
                        "page_number": page_num,
                        "bbox": bbox.to_list(),
                    })

            # Check if this page is scanned (less than 40 chars of text and has images)
            has_scanned = len(page_text_total.strip()) < 40 and len(fitz_page.get_images()) > 0
            if has_scanned:
                scanned_page_count += 1

            pages.append(
                Page(
                    page_number=page_num,
                    width=round(p_width, 2),
                    height=round(p_height, 2),
                    elements=page_elements,
                    has_scanned_content=has_scanned,
                    ocr_applied=False,
                )
            )

        pdf_doc.close()

        # Document type distinction (Section 7)
        is_scanned_doc = total_pages > 0 and (scanned_page_count / total_pages) >= 0.5
        final_doc_type = DocumentType.SCANNED_PDF if is_scanned_doc else DocumentType.DIGITAL_PDF

        # Inherit temporal metadata if discovered
        fy = discovered.temporal.financial_year if discovered else None
        period = discovered.temporal.reporting_period if discovered else None
        dates = discovered.temporal.extracted_dates if discovered else []

        return CanonicalDocument(
            document_id=doc_id,
            source_reference=str(path.resolve()),
            source_hash=source_hash,
            document_type=final_doc_type,
            reporting_year=fy,
            reporting_period=period,
            dates=dates,
            file_size_bytes=file_size,
            pages=pages,
            links=all_links,
            images=all_images,
            markdown_content="\n".join(markdown_sections),
            metadata={
                "total_pages": total_pages,
                "scanned_pages": scanned_page_count,
                "is_scanned": is_scanned_doc,
            },
        )
