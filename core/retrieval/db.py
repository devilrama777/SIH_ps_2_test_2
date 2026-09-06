"""
SQLite Persistence & FTS5 Schema — Section 10 of Master Implementation Specification.

Provides full-text lexical search (FTS5), relational element mapping,
and temporal indexing without requiring heavy external databases.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


class ReportDatabase:
    """
    Manages local SQLite database with FTS5 virtual tables for document intelligence.
    """

    def __init__(self, db_path: Optional[Path | str] = None):
        if db_path is None:
            db_path = Path("./data/workspace/cil_report_intel.db")
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Create relational tables and FTS5 virtual tables with WAL journal mode."""
        with self.get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")

            # 1. Documents Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    source_reference TEXT NOT NULL,
                    source_hash TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    reporting_year TEXT,
                    reporting_period TEXT,
                    file_size_bytes INTEGER,
                    ingested_at TEXT NOT NULL,
                    metadata_json TEXT,
                    user_id TEXT DEFAULT 'system'
                );
            """)

            # Safe migration: add user_id column if table already existed without it
            try:
                conn.execute("ALTER TABLE documents ADD COLUMN user_id TEXT DEFAULT 'system';")
            except sqlite3.OperationalError:
                pass
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id);")

            # 2. Pages Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    page_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    width REAL,
                    height REAL,
                    has_scanned_content INTEGER DEFAULT 0,
                    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
                );
            """)

            # 3. Document Elements Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS elements (
                    element_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    page_number INTEGER,
                    type TEXT NOT NULL,
                    text TEXT,
                    bbox_json TEXT,
                    confidence REAL,
                    reading_order INTEGER,
                    metadata_json TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
                );
            """)

            # 4. Tables Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tables (
                    table_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    sheet_name TEXT,
                    headers_json TEXT,
                    row_count INTEGER,
                    col_count INTEGER,
                    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
                );
            """)

            # 5. Provenance Records Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS provenance (
                    provenance_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    element_id TEXT,
                    source_reference TEXT NOT NULL,
                    page_number INTEGER,
                    bbox_json TEXT,
                    spreadsheet_coord_json TEXT,
                    extraction_method TEXT,
                    confidence REAL,
                    reporting_period TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
                );
            """)

            # 6. SQLite FTS5 Full-Text Search Virtual Table
            # Enables BM25 lexical ranking on extracted element text
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS fts_elements USING fts5(
                    element_id UNINDEXED,
                    document_id UNINDEXED,
                    page_number UNINDEXED,
                    element_type UNINDEXED,
                    reporting_period,
                    text,
                    tokenize = 'porter unicode61'
                );
            """)

            conn.commit()
