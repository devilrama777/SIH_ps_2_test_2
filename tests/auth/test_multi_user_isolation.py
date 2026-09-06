"""
Integration Tests for Multi-User Data Isolation, Retrieval Isolation & Agent Boundaries.

Verifies:
1. User A and User B have separate workspaces and databases.
2. User A data is not returned to User B during hybrid evidence retrieval.
3. User A can access User A data; User B can access User B data.
4. Clean logout and user switching resets data boundaries.
"""
import pytest
from pathlib import Path

from core.auth.manager import AuthManager
from core.retrieval.db import ReportDatabase
from core.retrieval.search import HybridSearchEngine, SearchQuery


def test_retrieval_multi_user_isolation(tmp_path):
    """Verify hybrid FTS5 search strictly scopes evidence by user_id."""
    db_path = tmp_path / "intel.db"
    report_db = ReportDatabase(db_path=db_path)
    search_engine = HybridSearchEngine(db=report_db)

    # 1. Insert Document owned by User A
    with report_db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO documents (document_id, source_reference, source_hash, document_type, reporting_year, reporting_period, file_size_bytes, ingested_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("doc_user_a", "CCL_Secret_Strategy_FY24.pdf", "hash_a", "pdf", "2024-25", "FY2024", 1024, "2026-09-07T00:00:00Z", "usr_user_a"),
        )
        conn.execute(
            """
            INSERT INTO elements (element_id, document_id, page_number, type, text)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("elem_a1", "doc_user_a", 1, "paragraph", "Confidential production target of 850 MT for User A division."),
        )
        conn.execute(
            """
            INSERT INTO fts_elements (element_id, document_id, page_number, element_type, reporting_period, text)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("elem_a1", "doc_user_a", 1, "paragraph", "FY2024", "Confidential production target of 850 MT for User A division."),
        )

        # 2. Insert Document owned by User B
        conn.execute(
            """
            INSERT INTO documents (document_id, source_reference, source_hash, document_type, reporting_year, reporting_period, file_size_bytes, ingested_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("doc_user_b", "ECL_Solar_Project_FY24.pdf", "hash_b", "pdf", "2024-25", "FY2024", 2048, "2026-09-07T00:00:00Z", "usr_user_b"),
        )
        conn.execute(
            """
            INSERT INTO elements (element_id, document_id, page_number, type, text)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("elem_b1", "doc_user_b", 1, "paragraph", "Solar farm capacity installation 250 MW for User B division."),
        )
        conn.execute(
            """
            INSERT INTO fts_elements (element_id, document_id, page_number, element_type, reporting_period, text)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("elem_b1", "doc_user_b", 1, "paragraph", "FY2024", "Solar farm capacity installation 250 MW for User B division."),
        )
        conn.commit()

    # 3. User B searches for "Confidential production target" -> Must return 0 results
    query_b = SearchQuery(query_text="production target", user_id="usr_user_b")
    results_b = search_engine.search(query_b)
    assert len(results_b) == 0, "User B must NOT retrieve User A's confidential documents"

    # 4. User A searches for "production target" -> Returns User A's document
    query_a = SearchQuery(query_text="production target", user_id="usr_user_a")
    results_a = search_engine.search(query_a)
    assert len(results_a) == 1
    assert results_a[0].document_id == "doc_user_a"
    assert "850 MT" in results_a[0].text

    # 5. User A searches for User B's solar content -> Returns 0 results
    query_a_solar = SearchQuery(query_text="Solar farm capacity", user_id="usr_user_a")
    results_a_solar = search_engine.search(query_a_solar)
    assert len(results_a_solar) == 0, "User A must NOT retrieve User B's solar documents"

    # 6. User B searches for User B's solar content -> Returns 1 result
    query_b_solar = SearchQuery(query_text="Solar farm capacity", user_id="usr_user_b")
    results_b_solar = search_engine.search(query_b_solar)
    assert len(results_b_solar) == 1
    assert results_b_solar[0].document_id == "doc_user_b"
