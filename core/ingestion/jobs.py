"""
Resumable Ingestion Job System — Section 6 & Section 27 of Master Implementation Plan.

Persists job state and completed item fingerprints in a local SQLite database
(data/workspace/ingestion_jobs.db) so that interrupted batch processing can resume
without re-ingesting already completed documents.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from core.domain.jobs import JobError, JobStage, JobStatus, ProcessingJob
from core.ingestion.discovery import DiscoveredFile, discover_files


class IngestionJobManager:
    """
    Manages observable, persistent, and resumable ingestion jobs.
    """

    def __init__(self, db_path: Optional[Path | str] = None):
        if db_path is None:
            db_path = Path("./data/workspace/ingestion_jobs.db")
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create job tables with WAL mode for concurrency."""
        with self._get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0.0,
                    current_stage TEXT NOT NULL,
                    total_items INTEGER DEFAULT 0,
                    processed_items INTEGER DEFAULT 0,
                    failed_items INTEGER DEFAULT 0,
                    source_path TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    metadata_json TEXT
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS job_items (
                    job_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT,
                    status TEXT NOT NULL,
                    processed_at TEXT,
                    error_message TEXT,
                    PRIMARY KEY (job_id, file_path),
                    FOREIGN KEY (job_id) REFERENCES jobs (job_id) ON DELETE CASCADE
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS job_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    message TEXT NOT NULL,
                    item_id TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES jobs (job_id) ON DELETE CASCADE
                );
            """)
            conn.commit()

    def create_job(self, source_path: str | Path, job_type: str = "ingest_folder") -> ProcessingJob:
        """Initialize a new ingestion job record in PENDING state."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat() + "Z"
        job = ProcessingJob(
            job_id=job_id,
            job_type=job_type,
            status=JobStatus.PENDING,
            progress=0.0,
            current_stage=JobStage.DISCOVERY,
            started_at=datetime.utcnow(),
            metadata={"source_path": str(Path(source_path).resolve())},
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    job_id, job_type, status, progress, current_stage,
                    total_items, processed_items, failed_items,
                    source_path, started_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.job_type,
                    job.status.value,
                    job.progress,
                    job.current_stage.value,
                    0, 0, 0,
                    str(Path(source_path).resolve()),
                    now,
                    json.dumps(job.metadata),
                ),
            )
            conn.commit()

        return job

    def get_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Fetch job record with errors and progress stats."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            if not row:
                return None

            error_rows = conn.execute(
                "SELECT stage, message, item_id, timestamp FROM job_errors WHERE job_id = ? ORDER BY id ASC",
                (job_id,),
            ).fetchall()

            errors = [
                JobError(
                    stage=JobStage(e["stage"]),
                    message=e["message"],
                    item_id=e["item_id"],
                    timestamp=datetime.fromisoformat(e["timestamp"].replace("Z", "")),
                )
                for e in error_rows
            ]

            metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}

            return ProcessingJob(
                job_id=row["job_id"],
                job_type=row["job_type"],
                status=JobStatus(row["status"]),
                progress=row["progress"],
                current_stage=JobStage(row["current_stage"]),
                total_items=row["total_items"],
                processed_items=row["processed_items"],
                failed_items=row["failed_items"],
                started_at=datetime.fromisoformat(row["started_at"].replace("Z", "")) if row["started_at"] else None,
                completed_at=datetime.fromisoformat(row["completed_at"].replace("Z", "")) if row["completed_at"] else None,
                errors=errors,
                metadata=metadata,
            )

    def list_jobs(self, limit: int = 20) -> List[ProcessingJob]:
        """List recently created jobs."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT job_id FROM jobs ORDER BY started_at DESC LIMIT ?", (limit,)
            ).fetchall()
        jobs = []
        for r in rows:
            job = self.get_job(r["job_id"])
            if job:
                jobs.append(job)
        return jobs

    def is_item_completed(self, job_id: str, file_hash: str) -> bool:
        """Check if an item has already been successfully processed in this job."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM job_items WHERE job_id = ? AND file_hash = ? AND status = 'completed'",
                (job_id, file_hash),
            ).fetchone()
            return row is not None

    def record_completed_item(self, job_id: str, file_path: str, file_hash: str) -> None:
        """Mark an individual file completed and recalculate job progress."""
        now = datetime.utcnow().isoformat() + "Z"
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO job_items (job_id, file_path, file_hash, status, processed_at)
                VALUES (?, ?, ?, 'completed', ?)
                ON CONFLICT(job_id, file_path) DO UPDATE SET
                    file_hash=excluded.file_hash,
                    status='completed',
                    processed_at=excluded.processed_at
                """,
                (job_id, file_path, file_hash, now),
            )
            # Update processed_items counter and progress
            conn.execute(
                """
                UPDATE jobs SET
                    processed_items = processed_items + 1,
                    progress = CASE WHEN total_items > 0 THEN ROUND((processed_items + 1) * 100.0 / total_items, 1) ELSE 0.0 END
                WHERE job_id = ?
                """,
                (job_id,),
            )
            conn.commit()

    def record_failed_item(self, job_id: str, file_path: str, error_msg: str, stage: JobStage) -> None:
        """Record an extraction or ingestion error on a specific item."""
        now = datetime.utcnow().isoformat() + "Z"
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO job_items (job_id, file_path, status, processed_at, error_message)
                VALUES (?, ?, 'failed', ?, ?)
                ON CONFLICT(job_id, file_path) DO UPDATE SET
                    status='failed',
                    processed_at=excluded.processed_at,
                    error_message=excluded.error_message
                """,
                (job_id, file_path, now, error_msg),
            )
            conn.execute(
                """
                INSERT INTO job_errors (job_id, stage, message, item_id, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (job_id, stage.value, error_msg, file_path, now),
            )
            conn.execute(
                """
                UPDATE jobs SET failed_items = failed_items + 1 WHERE job_id = ?
                """,
                (job_id,),
            )
            conn.commit()

    def update_stage(self, job_id: str, stage: JobStage, status: Optional[JobStatus] = None) -> None:
        """Advance job to next stage."""
        with self._get_connection() as conn:
            if status:
                conn.execute(
                    "UPDATE jobs SET current_stage = ?, status = ? WHERE job_id = ?",
                    (stage.value, status.value, job_id),
                )
            else:
                conn.execute(
                    "UPDATE jobs SET current_stage = ? WHERE job_id = ?",
                    (stage.value, job_id),
                )
            conn.commit()

    def complete_job(self, job_id: str) -> None:
        """Mark job successfully completed."""
        now = datetime.utcnow().isoformat() + "Z"
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE jobs SET
                    status = 'COMPLETED',
                    progress = 100.0,
                    current_stage = 'READY_FOR_REVIEW',
                    completed_at = ?
                WHERE job_id = ?
                """,
                (now, job_id),
            )
            conn.commit()

    def cancel_job(self, job_id: str) -> None:
        """Cancel a running job."""
        now = datetime.utcnow().isoformat() + "Z"
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE jobs SET status = 'CANCELLED', completed_at = ? WHERE job_id = ?",
                (now, job_id),
            )
            conn.commit()

    def run_ingestion_pipeline(self, job_id: str) -> ProcessingJob:
        """
        Execute file discovery, extraction into CanonicalDocument, and incremental persistence.
        Skips files that are already completed in this job.
        """
        from core.extraction.unified import extract_document

        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        source_path = job.metadata.get("source_path")
        if not source_path:
            raise ValueError("Job metadata missing source_path")

        # 1. DISCOVERY STAGE
        self.update_stage(job_id, JobStage.DISCOVERY, status=JobStatus.RUNNING)
        files = discover_files(source_path, compute_hashes=True)

        with self._get_connection() as conn:
            conn.execute(
                "UPDATE jobs SET total_items = ? WHERE job_id = ?",
                (len(files), job_id),
            )
            conn.commit()

        # 2. INGESTION & EXTRACTION STAGE
        self.update_stage(job_id, JobStage.EXTRACTION)
        docs_dir = self.db_path.parent / "canonical_documents"
        docs_dir.mkdir(parents=True, exist_ok=True)

        for df in files:
            # Check current job status in case of cancellation
            current_job = self.get_job(job_id)
            if current_job and current_job.status == JobStatus.CANCELLED:
                return current_job

            # Resumability check: if already completed, skip processing
            if df.sha256 and self.is_item_completed(job_id, df.sha256):
                continue

            try:
                # Extract file into canonical document representation
                canonical = extract_document(df.absolute_path, discovered=df)
                
                # Persist canonical JSON representation for Phase 3 indexing
                doc_file = docs_dir / f"{canonical.document_id}.json"
                doc_file.write_text(canonical.model_dump_json(indent=2), encoding="utf-8")

                self.record_completed_item(job_id, df.absolute_path, df.sha256 or "")
            except Exception as exc:
                self.record_failed_item(job_id, df.absolute_path, str(exc), JobStage.EXTRACTION)

        # 3. INDEXING STAGE
        self.update_stage(job_id, JobStage.INDEXING)
        self.complete_job(job_id)

        return self.get_job(job_id)  # type: ignore
