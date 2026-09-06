"""
Tests for DocumentIndexer.
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
from core.retrieval.db import ReportDatabase
from core.retrieval.indexer import DocumentIndexer


def test_document_indexing(tmp_path: Path):
    """Verify CanonicalDocument is indexed into relational tables and FTS5."""
    db_file = tmp_path / "index_test.db"
    db = ReportDatabase(db_path=db_file)
    indexer = DocumentIndexer(db=db)

    el1 = DocumentElement(
        element_id="el_doc1_p1_001",
        document_id="doc1",
        type=ElementType.HEADING,
        page_number=1,
        bbox=BoundingBox(x0=50.0, y0=50.0, x1=300.0, y1=80.0),
        text="Operational Safety Audit",
    )
    el2 = DocumentElement(
        element_id="el_doc1_p1_002",
        document_id="doc1",
        type=ElementType.PARAGRAPH,
        page_number=1,
        bbox=BoundingBox(x0=50.0, y0=90.0, x1=500.0, y1=150.0),
        text="All coal washing plants in Central Coalfields complied with dust suppression norms.",
    )

    doc = CanonicalDocument(
        document_id="doc1",
        source_reference="C:/data/safety_audit.pdf",
        source_hash="sha256_dummy_123",
        document_type=DocumentType.DIGITAL_PDF,
        reporting_year="2024-25",
        reporting_period="March 2025",
        pages=[Page(page_number=1, elements=[el1, el2])],
    )

    indexer.index_document(doc)

    with db.get_connection() as conn:
        doc_row = conn.execute("SELECT * FROM documents WHERE document_id = 'doc1'").fetchone()
        assert doc_row is not None
        assert doc_row["reporting_period"] == "March 2025"

        elements_count = conn.execute("SELECT COUNT(*) as cnt FROM elements WHERE document_id = 'doc1'").fetchone()["cnt"]
        assert elements_count == 2

        fts_count = conn.execute("SELECT COUNT(*) as cnt FROM fts_elements WHERE fts_elements MATCH 'dust suppression'").fetchone()["cnt"]
        assert fts_count == 1
