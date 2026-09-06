"""
Tests for HybridSearchEngine and Evidence Ranking (Section 11).
"""
from pathlib import Path
from core.domain.documents import (
    BoundingBox,
    CanonicalDocument,
    DocumentElement,
    DocumentType,
    ElementType,
    Page,
)
from core.domain.evidence import SpreadsheetCoordinate
from core.retrieval.db import ReportDatabase
from core.retrieval.indexer import DocumentIndexer
from core.retrieval.search import HybridSearchEngine, SearchQuery


def test_hybrid_search_with_temporal_filtering(tmp_path: Path):
    """
    Test Section 11 query:
    'Find all March 2025 operational performance information.'
    """
    db_file = tmp_path / "search_test.db"
    db = ReportDatabase(db_path=db_file)
    indexer = DocumentIndexer(db=db)
    search_engine = HybridSearchEngine(db=db)

    # Document 1: Relevant to March 2025
    doc1 = CanonicalDocument(
        document_id="doc_march_perf",
        source_reference="C:/data/2025/March/production.xlsx",
        source_hash="sha_march",
        document_type=DocumentType.XLSX,
        reporting_year="2024-25",
        reporting_period="March 2025",
        pages=[
            Page(
                page_number=1,
                elements=[
                    DocumentElement(
                        element_id="el_march_01",
                        document_id="doc_march_perf",
                        type=ElementType.SPREADSHEET_CELL,
                        page_number=1,
                        text="Operational performance for March 2025 achieved 1245.70 MT raw coal dispatch.",
                        metadata={
                            "spreadsheet_coord": SpreadsheetCoordinate(
                                workbook_name="production.xlsx",
                                sheet_name="March",
                                cell="G27",
                                raw_value=1245.70,
                            ).model_dump()
                        },
                    )
                ],
            )
        ],
    )

    # Document 2: Different month (October 2024)
    doc2 = CanonicalDocument(
        document_id="doc_oct_perf",
        source_reference="C:/data/2024/October/production.xlsx",
        source_hash="sha_oct",
        document_type=DocumentType.XLSX,
        reporting_year="2024-25",
        reporting_period="October 2024",
        pages=[
            Page(
                page_number=1,
                elements=[
                    DocumentElement(
                        element_id="el_oct_01",
                        document_id="doc_oct_perf",
                        type=ElementType.SPREADSHEET_CELL,
                        page_number=1,
                        text="Operational performance for October 2024 was 980.20 MT.",
                    )
                ],
            )
        ],
    )

    indexer.index_document(doc1)
    indexer.index_document(doc2)

    # Query with temporal filter and lexical search
    query = SearchQuery(
        query_text="operational performance information",
        reporting_period="March 2025",
        limit=10,
    )

    results = search_engine.search(query)
    assert len(results) >= 1

    top = results[0]
    assert top.element_id == "el_march_01"
    assert top.reporting_period == "March 2025"
    assert top.spreadsheet_coord is not None
    assert top.spreadsheet_coord.cell == "G27"
    assert top.score > 0.5
