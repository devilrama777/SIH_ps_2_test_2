"""
CSV and Plain Text Extraction Engine — Section 3 & Section 9 of Master Implementation Specification.
"""
from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.domain.documents import (
    CanonicalDocument,
    DocumentElement,
    DocumentType,
    ElementType,
    Page,
)
from core.extraction.base import BaseExtractor
from core.ingestion.discovery import DiscoveredFile
from core.provenance.tracker import generate_document_id, generate_element_id


class CSVExtractor(BaseExtractor):
    """Extracts CSV tabular data into structured tables and cells with line numbers."""

    def extract(self, file_path: Path, discovered: Optional[DiscoveredFile] = None) -> CanonicalDocument:
        path = Path(file_path)
        with open(path, "rb") as f:
            raw_bytes = f.read()

        file_size = len(raw_bytes)
        source_hash = hashlib.sha256(raw_bytes).hexdigest()
        doc_id = generate_document_id(str(path), raw_bytes)

        # Detect dialect & decode
        text_content = raw_bytes.decode("utf-8", errors="replace")
        f_io = io.StringIO(text_content)
        reader = csv.reader(f_io)

        rows = list(reader)
        headers = rows[0] if rows else []
        body_rows = rows[1:] if len(rows) > 1 else []

        elements: List[DocumentElement] = []
        counter = 0

        for row_idx, row in enumerate(rows, start=1):
            for col_idx, cell_val in enumerate(row, start=1):
                clean_val = cell_val.strip()
                if not clean_val:
                    continue
                counter += 1
                el_id = generate_element_id(doc_id, 1, counter)
                elements.append(
                    DocumentElement(
                        element_id=el_id,
                        document_id=doc_id,
                        type=ElementType.TABLE_CELL,
                        page_number=1,
                        text=clean_val,
                        confidence=1.0,
                        metadata={"row": row_idx, "column": col_idx, "header": headers[col_idx - 1] if col_idx <= len(headers) else None},
                    )
                )

        # Markdown representation
        md_lines = [f"# Dataset: {path.name}\n"]
        if headers:
            md_lines.append("| " + " | ".join(headers) + " |")
            md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
            for r in body_rows[:30]:
                md_lines.append("| " + " | ".join(r) + " |")
            md_lines.append("\n")

        fy = discovered.temporal.financial_year if discovered else None
        period = discovered.temporal.reporting_period if discovered else None
        dates = discovered.temporal.extracted_dates if discovered else []

        return CanonicalDocument(
            document_id=doc_id,
            source_reference=str(path.resolve()),
            source_hash=source_hash,
            document_type=DocumentType.CSV,
            reporting_year=fy,
            reporting_period=period,
            dates=dates,
            file_size_bytes=file_size,
            pages=[Page(page_number=1, elements=elements)],
            tables=[{
                "headers": headers,
                "row_count": len(rows),
                "rows": body_rows[:100],
            }],
            markdown_content="\n".join(md_lines),
            metadata={"total_rows": len(rows), "total_columns": len(headers)},
        )


class TextExtractor(BaseExtractor):
    """Extracts plain text documents into paragraph blocks."""

    def extract(self, file_path: Path, discovered: Optional[DiscoveredFile] = None) -> CanonicalDocument:
        path = Path(file_path)
        with open(path, "rb") as f:
            raw_bytes = f.read()

        file_size = len(raw_bytes)
        source_hash = hashlib.sha256(raw_bytes).hexdigest()
        doc_id = generate_document_id(str(path), raw_bytes)

        text_content = raw_bytes.decode("utf-8", errors="replace").replace("\r\n", "\n")
        paragraphs = [p.strip() for p in text_content.split("\n\n") if p.strip()]

        elements: List[DocumentElement] = []
        counter = 0

        for p_text in paragraphs:
            counter += 1
            el_id = generate_element_id(doc_id, 1, counter)
            is_heading = (
                len(p_text.splitlines()) == 1
                and len(p_text) < 80
                and not p_text.endswith((".", ";"))
                and (p_text.isupper() or p_text.istitle() or p_text.startswith("#"))
            )
            el_type = ElementType.HEADING if is_heading else ElementType.PARAGRAPH

            elements.append(
                DocumentElement(
                    element_id=el_id,
                    document_id=doc_id,
                    type=el_type,
                    page_number=1,
                    text=p_text,
                    reading_order=counter,
                    confidence=1.0,
                )
            )

        fy = discovered.temporal.financial_year if discovered else None
        period = discovered.temporal.reporting_period if discovered else None
        dates = discovered.temporal.extracted_dates if discovered else []

        return CanonicalDocument(
            document_id=doc_id,
            source_reference=str(path.resolve()),
            source_hash=source_hash,
            document_type=DocumentType.TXT,
            reporting_year=fy,
            reporting_period=period,
            dates=dates,
            file_size_bytes=file_size,
            pages=[Page(page_number=1, elements=elements)],
            markdown_content=text_content,
            metadata={"paragraph_count": len(paragraphs)},
        )
