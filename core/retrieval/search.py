"""
Hybrid Search Engine & Evidence Ranking — Section 11 of Master Implementation Specification.

Executes lexical FTS5 BM25 queries with temporal filtering, document type constraints,
and evidence ranking. Returns evidence with full provenance coordinates.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.domain.documents import BoundingBox
from core.domain.evidence import SpreadsheetCoordinate
from core.retrieval.db import ReportDatabase


class SearchQuery(BaseModel):
    """Structured query for hybrid retrieval."""
    query_text: str
    financial_year: Optional[str] = None  # e.g., '2024-25'
    reporting_period: Optional[str] = None  # e.g., 'March 2025'
    document_type: Optional[str] = None  # e.g., 'xlsx', 'digital_pdf'
    limit: int = Field(default=20, ge=1, le=100)


class RankedEvidence(BaseModel):
    """An individual piece of ranked evidence with complete provenance coordinates."""
    element_id: str
    document_id: str
    source_reference: str
    page_number: Optional[int] = None
    element_type: str
    text: str
    score: float = Field(..., description="Hybrid relevance score (higher = more relevant)")
    provenance_id: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    spreadsheet_coord: Optional[SpreadsheetCoordinate] = None
    reporting_period: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


def sanitize_fts_query(query: str) -> str:
    """Sanitize user query string for SQLite FTS5 MATCH syntax."""
    clean = re.sub(r"[^\w\s]", " ", query).strip()
    words = clean.split()
    if not words:
        return '""'
    # Join with OR / NEAR or phrase search
    return " OR ".join(f'"{w}"' for w in words)


class HybridSearchEngine:
    """
    Hybrid lexical and temporal evidence retrieval engine.
    """

    def __init__(self, db: Optional[ReportDatabase] = None):
        self.db = db or ReportDatabase()

    def search(self, query: SearchQuery) -> List[RankedEvidence]:
        """
        Execute BM25 search over FTS5 table joined with document and element tables.
        Applies temporal ranking boosts and returns ranked evidence.
        """
        fts_term = sanitize_fts_query(query.query_text)
        if fts_term == '""':
            return []

        # Base SQL query joining FTS5 elements with relational metadata and provenance
        sql = """
            SELECT
                e.element_id,
                e.document_id,
                e.page_number,
                e.type as element_type,
                e.text,
                e.bbox_json,
                e.metadata_json,
                d.source_reference,
                d.document_type,
                d.reporting_period,
                d.reporting_year,
                p.provenance_id,
                p.spreadsheet_coord_json,
                bm25(fts_elements) as bm25_rank
            FROM fts_elements fts
            JOIN elements e ON fts.element_id = e.element_id
            JOIN documents d ON e.document_id = d.document_id
            LEFT JOIN provenance p ON e.element_id = p.element_id
            WHERE fts_elements MATCH ?
        """

        params: List[Any] = [fts_term]

        # Apply optional filters
        if query.financial_year:
            sql += " AND (d.reporting_year = ? OR d.reporting_period LIKE ?)"
            params.extend([query.financial_year, f"%{query.financial_year}%"])

        if query.reporting_period:
            sql += " AND (d.reporting_period LIKE ? OR fts.reporting_period LIKE ?)"
            params.extend([f"%{query.reporting_period}%", f"%{query.reporting_period}%"])

        if query.document_type:
            sql += " AND d.document_type = ?"
            params.append(query.document_type)

        # FTS5 BM25 rank: smaller/more negative numbers = better match in SQLite
        sql += " ORDER BY bm25(fts_elements) ASC LIMIT ?"
        params.append(query.limit * 2)

        results: List[RankedEvidence] = []

        with self.db.get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()

            for row in rows:
                raw_bm25 = row["bm25_rank"]
                # Convert SQLite BM25 to positive relevance score (1.0 / (1.0 + abs(raw_bm25)))
                base_score = round(1.0 / (1.0 + max(raw_bm25, -100.0)), 4) if raw_bm25 is not None else 0.5

                # Temporal Match Boost (Section 11)
                temporal_boost = 0.0
                doc_period = (row["reporting_period"] or "").lower()
                query_lower = query.query_text.lower()

                # If query explicitly contains month/year matching this evidence, boost score
                for token in query_lower.split():
                    if len(token) >= 4 and token in doc_period:
                        temporal_boost += 0.2
                        break

                final_score = round(base_score + temporal_boost, 4)

                # Parse bounding box
                bbox = None
                if row["bbox_json"]:
                    try:
                        bbox = BoundingBox(**json.loads(row["bbox_json"]))
                    except Exception:
                        pass

                # Parse spreadsheet coordinate
                sheet_coord = None
                if row["spreadsheet_coord_json"]:
                    try:
                        sheet_coord = SpreadsheetCoordinate(**json.loads(row["spreadsheet_coord_json"]))
                    except Exception:
                        pass

                metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}

                results.append(
                    RankedEvidence(
                        element_id=row["element_id"],
                        document_id=row["document_id"],
                        source_reference=row["source_reference"],
                        page_number=row["page_number"],
                        element_type=row["element_type"],
                        text=row["text"] or "",
                        score=final_score,
                        provenance_id=row["provenance_id"],
                        bbox=bbox,
                        spreadsheet_coord=sheet_coord,
                        reporting_period=row["reporting_period"],
                        metadata=metadata,
                    )
                )

        # Sort descending by composite score
        results.sort(key=lambda r: r.score, reverse=True)
        return results[: query.limit]
