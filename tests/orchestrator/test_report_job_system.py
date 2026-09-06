"""
Tests for 12-Stage Resumable Report Job Orchestration — Section 27 of Master Implementation Plan.
"""
from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.orchestrator.report_job import (
    ReportJobConfig,
    ReportJobManager,
    ReportJobStage,
    ReportJobStatus,
    STAGES_ORDER,
)


client = TestClient(app)


def test_report_job_creation_and_stage_structure(tmp_path: Path):
    manager = ReportJobManager(workspace_dir=str(tmp_path))
    cfg = ReportJobConfig(
        subsidiary_code="BCCL",
        reporting_period="FY 2024-25",
        template_style="classic",
    )
    job = manager.create_job(cfg)

    assert job.job_id.startswith("rjob_")
    assert job.status == ReportJobStatus.PENDING
    assert job.current_stage == ReportJobStage.DISCOVERY
    assert job.progress_percent == 0.0
    assert len(STAGES_ORDER) == 12

    # Check persistence in SQLite
    loaded = manager.get_job(job.job_id)
    assert loaded is not None
    assert loaded.job_id == job.job_id
    assert loaded.config.subsidiary_code == "BCCL"


def test_report_job_pause_and_cancel(tmp_path: Path):
    manager = ReportJobManager(workspace_dir=str(tmp_path))
    cfg = ReportJobConfig(subsidiary_code="ECL")
    job = manager.create_job(cfg)

    # 1. Pause
    paused = manager.pause_job(job.job_id)
    assert paused.status == ReportJobStatus.PAUSED

    # 2. Cancel
    cancelled = manager.cancel_job(job.job_id)
    assert cancelled.status == ReportJobStatus.CANCELLED


def test_report_job_rest_api_lifecycle():
    # 1. Start report job synchronously
    payload = {
        "subsidiary_code": "CCL",
        "reporting_period": "FY 2023-24",
        "template_style": "modern",
        "run_sync": True,
    }
    resp = client.post("/api/v1/report-jobs/start", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    job_id = data["job_id"]
    assert data["status"] in ["completed", "running"]
    assert len(data["completed_stages"]) > 0

    # 2. GET /api/v1/report-jobs
    list_resp = client.get("/api/v1/report-jobs")
    assert list_resp.status_code == 200
    all_jobs = list_resp.json()
    assert any(j["job_id"] == job_id for j in all_jobs)

    # 3. GET /api/v1/report-jobs/{job_id}
    status_resp = client.get(f"/api/v1/report-jobs/{job_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["job_id"] == job_id

    # 4. Pause endpoint
    pause_resp = client.post(f"/api/v1/report-jobs/{job_id}/pause")
    assert pause_resp.status_code == 200

    # 5. Resume endpoint
    resume_resp = client.post(f"/api/v1/report-jobs/{job_id}/resume?run_sync=true")
    assert resume_resp.status_code == 200

    # 6. Cancel endpoint
    cancel_resp = client.post(f"/api/v1/report-jobs/{job_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"
