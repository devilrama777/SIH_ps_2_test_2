"""
Tests for Section 6 & 27 resumable IngestionJobManager.
"""
from pathlib import Path
from core.domain.jobs import JobStage, JobStatus
from core.ingestion.jobs import IngestionJobManager


def test_job_lifecycle_and_resumability(tmp_path: Path):
    """Verify job creation, progress tracking, and resumability after interruption."""
    db_file = tmp_path / "test_jobs.db"
    mgr = IngestionJobManager(db_path=db_file)

    # Prepare dummy files
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    (files_dir / "doc1.csv").write_text("1,2,3")
    (files_dir / "doc2.csv").write_text("4,5,6")
    (files_dir / "doc3.csv").write_text("7,8,9")

    # 1. Create Job
    job = mgr.create_job(source_path=files_dir)
    assert job.status == JobStatus.PENDING
    assert job.current_stage == JobStage.DISCOVERY

    # 2. Run pipeline
    completed_job = mgr.run_ingestion_pipeline(job.job_id)
    assert completed_job.status == JobStatus.COMPLETED
    assert completed_job.total_items == 3
    assert completed_job.processed_items == 3
    assert completed_job.progress == 100.0

    # 3. Simulate new file added and resume
    (files_dir / "doc4.csv").write_text("10,11,12")
    # Resume pipeline for the same job or a continuation
    job2 = mgr.create_job(source_path=files_dir)
    resumed_job = mgr.run_ingestion_pipeline(job2.job_id)
    assert resumed_job.status == JobStatus.COMPLETED
    assert resumed_job.total_items == 4
    assert resumed_job.processed_items == 4


def test_job_cancellation(tmp_path: Path):
    """Verify job cancellation updates status."""
    db_file = tmp_path / "test_cancel.db"
    mgr = IngestionJobManager(db_path=db_file)

    job = mgr.create_job(source_path=tmp_path)
    mgr.cancel_job(job.job_id)

    fetched = mgr.get_job(job.job_id)
    assert fetched is not None
    assert fetched.status == JobStatus.CANCELLED
