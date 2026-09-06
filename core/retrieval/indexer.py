"""
Document Indexer — Section 10 & 11 of Master Implementation Specification.

Indexes CanonicalDocument instances into SQLite tables and the FTS5 full-text engine.
Creates provenance records linking elements to their exact source pages and spreadsheet cells.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from core.domain.documents import CanonicalDocument, DocumentElement
from core.provenance.tracker import create_provenance_record
from core.retrieval.db import ReportDatabase


class DocumentIndexer:
    """
    Indexes extracted CanonicalDocuments into SQLite relational tables and FTS5.
    """

    def __init__(self, db: Optional[ReportDatabase] = None):
        self.db = db or ReportDatabase()

    def index_document(self, doc: CanonicalDocument) -> None:
        """Atomically index an entire CanonicalDocument and its elements."""
        with self.db.get_connection() as conn:
            # 1. Insert or update Document
            conn.execute(
                """
                INSERT INTO documents (
                    document_id, source_reference, source_hash, document_type,
                    reporting_year, reporting_period, file_size_bytes,
                    ingested_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    reporting_year = excluded.reporting_year,
                    reporting_period = excluded.reporting_period,
                    metadata_json = excluded.metadata_json
                """,
                (
                    doc.document_id,
                    doc.source_reference,
                    doc.source_hash,
                    doc.document_type.value,
                    doc.reporting_year,
                    doc.reporting_period,
                    doc.file_size_bytes,
                    doc.ingested_at.isoformat() + "Z",
                    json.dumps(doc.metadata),
                ),
            )

            # Clear existing elements/pages/fts for this document if re-indexing
            conn.execute("DELETE FROM pages WHERE document_id = ?", (doc.document_id,))
            conn.execute("DELETE FROM elements WHERE document_id = ?", (doc.document_id,))
            conn.execute("DELETE FROM provenance WHERE document_id = ?", (doc.document_id,))
            conn.execute("DELETE FROM fts_elements WHERE document_id = ?", (doc.document_id,))

            # 2. Insert Pages
            for page in doc.pages:
                page_id = f"{doc.document_id}_p{page.page_number}"
                conn.execute(
                    """
                    INSERT INTO pages (page_id, document_id, page_number, width, height, has_scanned_content)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        page_id,
                        doc.document_id,
                        page.page_number,
                        page.width,
                        page.height,
                        1 if page.has_scanned_content else 0,
                    ),
                )

                # 3. Insert Elements & Provenance
                for el in page.elements:
                    bbox_json = json.dumps(el.bbox.model_dump()) if el.bbox else None
                    coord_data = el.metadata.get("spreadsheet_coord")

                    # Provenance record
                    prov = create_provenance_record(
                        document_id=doc.document_id,
                        source_reference=doc.source_reference,
                        element_id=el.element_id,
                        page_number=el.page_number,
                        bbox=el.bbox,
                        confidence=el.confidence,
                        reporting_period=doc.reporting_period,
                    )

                    conn.execute(
                        """
                        INSERT INTO elements (
                            element_id, document_id, page_number, type, text,
                            bbox_json, confidence, reading_order, metadata_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            el.element_id,
                            doc.document_id,
                            el.page_number,
                            el.type.value,
                            el.text,
                            bbox_json,
                            el.confidence,
                            el.reading_order,
                            json.dumps(el.metadata),
                        ),
                    )

                    conn.execute(
                        """
                        INSERT INTO provenance (
                            provenance_id, document_id, element_id, source_reference,
                            page_number, bbox_json, spreadsheet_coord_json,
                            extraction_method, confidence, reporting_period
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            prov.provenance_id,
                            doc.document_id,
                            el.element_id,
                            doc.source_reference,
                            el.page_number,
                            bbox_json,
                            json.dumps(coord_data) if coord_data else None,
                            "direct",
                            el.confidence,
                            doc.reporting_period,
                        ),
                    )

                    # 4. Insert into FTS5 index if element contains text
                    if el.text and el.text.strip():
                        conn.execute(
                            """
                            INSERT INTO fts_elements (
                                element_id, document_id, page_number,
                                element_type, reporting_period, text
                            ) VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                el.element_id,
                                doc.document_id,
                                str(el.page_number or 1),
                                el.type.value,
                                doc.reporting_period or "",
                                el.text,
                            ),
                        )

            # 5. Insert Tables
            for tbl_idx, tbl in enumerate(doc.tables, start=1):
                tbl_id = f"{doc.document_id}_tbl_{tbl_idx}"
                conn.execute(
                    """
                    INSERT INTO tables (
                        table_id, document_id, sheet_name, headers_json, row_count, col_count
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tbl_id,
                        doc.document_id,
                        tbl.get("sheet_name"),
                        json.dumps(tbl.get("headers", [])),
                        tbl.get("row_count", 0),
                        tbl.get("col_count", 0),
                    ),
                )

            conn.commit()
