"""
Unit and Integration Tests for Phase 31: Advanced Temporal Query & Timeline Indexing Engine.
Section 5 and Section 11 of Master Implementation Specification.
"""
from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.domain.documents import CanonicalDocument, Page, DocumentElement, ElementType
from core.retrieval.db import ReportDatabase
from core.retrieval.indexer import DocumentIndexer
from core.retrieval.temporal_query_engine import (
    TemporalQueryEngine,
    TemporalQueryFilter,
    TemporalQueryResult,
)

client = TestClient(app)


def test_parse_natural_language_temporal_queries(tmp_path: Path):
    engine = TemporalQueryEngine(db=ReportDatabase(db_path=str(tmp_path / "parse_test.db")))

    # 1. Month and Year
    q1 = "Find all March 2025 operational performance information"
    f1 = engine.parse_temporal_query(q1)
    assert f1.target_month == "March"
    assert f1.target_year == 2025
    assert "operational performance" in f1.cleaned_text_query.lower()

    # 2. Financial Year
    q2 = "Show production summary for FY 2023-24"
    f2 = engine.parse_temporal_query(q2)
    assert f2.target_fy == "2023-24" or f2.target_fy == "FY 2023-24"

    # 3. Quarter
    q3 = "Retrieve Q3 washery dispatch details"
    f3 = engine.parse_temporal_query(q3)
    assert f3.target_quarter == "Q3"


def test_temporal_search_indexing_and_clustering(tmp_path: Path):
    db_path = str(tmp_path / "temporal_test.db")
    db = ReportDatabase(db_path=db_path)
    indexer = DocumentIndexer(db=db)

    # Ingest document for March 2024
    doc1 = CanonicalDocument(
        document_id="doc_march_2024",
        source_reference="march_2024_report.pdf",
        source_hash="h1",
        reporting_year="FY 2023-24",
        reporting_period="March 2024",
        pages=[
            Page(
                page_number=1,
                elements=[
                    DocumentElement(
                        element_id="el_1",
                        document_id="doc_march_2024",
                        type=ElementType.PARAGRAPH,
                        text="In March 2024, raw coal production reached 8.5 million tonnes in Piparwar.",
                    )
                ],
            )
        ],
    )
    indexer.index_document(doc1)

    # Ingest document for October 2024
    doc2 = CanonicalDocument(
        document_id="doc_oct_2024",
        source_reference="october_2024_report.pdf",
        source_hash="h2",
        reporting_year="FY 2024-25",
        reporting_period="October 2024",
        pages=[
            Page(
                page_number=1,
                elements=[
                    DocumentElement(
                        element_id="el_2",
                        document_id="doc_oct_2024",
                        type=ElementType.PARAGRAPH,
                        text="In October 2024, raw coal production reached 9.1 million tonnes in Rajrappa.",
                    )
                ],
            )
        ],
    )
    indexer.index_document(doc2)

    engine = TemporalQueryEngine(db=db)
    res: TemporalQueryResult = engine.search_temporal(
        query="Find all March 2024 coal production evidence",
        limit=10,
    )

    assert res.total_matched >= 1
    assert any("March" in r.content for r in res.flat_results)
    assert len(res.chronological_timeline) >= 1


def test_temporal_search_rest_api():
    resp = client.post(
        "/api/v1/search/temporal",
        json={"query": "Find production metrics for FY 2023-24", "limit": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "query" in data
    assert "filter_criteria" in data
    assert "chronological_timeline" in data
