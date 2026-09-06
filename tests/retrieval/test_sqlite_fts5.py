"""
Tests for SQLite FTS5 database initialization and BM25 full-text query.
"""
from pathlib import Path
from core.retrieval.db import ReportDatabase


def test_database_initialization_and_fts5(tmp_path: Path):
    """Verify tables and FTS5 virtual table are created and queryable."""
    db_file = tmp_path / "test_report_intel.db"
    db = ReportDatabase(db_path=db_file)

    with db.get_connection() as conn:
        # Insert sample row into FTS5
        conn.execute(
            """
            INSERT INTO fts_elements (element_id, document_id, page_number, element_type, reporting_period, text)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "el_001",
                "doc_001",
                "1",
                "paragraph",
                "March 2025",
                "Coal production in the northern sector exceeded monthly operational targets.",
            ),
        )
        conn.commit()

        # Query using MATCH
        rows = conn.execute(
            "SELECT element_id, text, bm25(fts_elements) as rank FROM fts_elements WHERE fts_elements MATCH ?",
            ("production targets",),
        ).fetchall()

        assert len(rows) == 1
        assert rows[0]["element_id"] == "el_001"
        assert rows[0]["rank"] is not None
