"""
Unit and Integration Tests for Phase 34: Checkpointed 12-Stage Job System with Crash Recovery.
Section 27 of Master Implementation Specification.
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


def test_job_creation_and_stage_execution(tmp_path: Path, monkeypatch):
    from core.ai.backends.rule_based import RuleBasedLocalBackend
    from core.ai.gateway.local_gateway import LocalAIGateway
    monkeypatch.setattr("core.reports.generator.section_generator.LocalAIGateway", lambda: LocalAIGateway(RuleBasedLocalBackend()))

    manager = ReportJobManager(workspace_dir=str(tmp_path))
    cfg = ReportJobConfig(
        subsidiary_code="CCL",
        reporting_period="FY 2023-24",
    )
    job = manager.create_job(cfg)
    assert job.status == ReportJobStatus.PENDING
    assert job.current_stage == ReportJobStage.DISCOVERY

    # Execute all stages
    completed = manager.execute_job_stages(job)
    assert completed.status == ReportJobStatus.COMPLETED
    assert completed.progress_percent == 100.0
    assert len(completed.completed_stages) == 12
    assert "report_id" in completed.checkpoints


def test_job_pause_and_resume(tmp_path: Path, monkeypatch):
    from core.ai.backends.rule_based import RuleBasedLocalBackend
    from core.ai.gateway.local_gateway import LocalAIGateway
    monkeypatch.setattr("core.reports.generator.section_generator.LocalAIGateway", lambda: LocalAIGateway(RuleBasedLocalBackend()))

    manager = ReportJobManager(workspace_dir=str(tmp_path))
    cfg = ReportJobConfig(subsidiary_code="CCL", reporting_period="FY 2023-24")
    job = manager.create_job(cfg)

    # Pause the job
    paused = manager.pause_job(job.job_id)
    assert paused.status == ReportJobStatus.PAUSED

    # Resume the job
    resumed = manager.resume_job(job.job_id)
    assert resumed.status == ReportJobStatus.COMPLETED
    assert len(resumed.completed_stages) == 12


def test_crash_recovery_simulation(tmp_path: Path, monkeypatch):
    from core.ai.backends.rule_based import RuleBasedLocalBackend
    from core.ai.gateway.local_gateway import LocalAIGateway
    monkeypatch.setattr("core.reports.generator.section_generator.LocalAIGateway", lambda: LocalAIGateway(RuleBasedLocalBackend()))

    # 1. Initialize manager and create job
    manager1 = ReportJobManager(workspace_dir=str(tmp_path))
    cfg = ReportJobConfig(subsidiary_code="CCL", reporting_period="FY 2023-24")
    job = manager1.create_job(cfg)

    # 2. Simulate a mid-execution crash at stage 4 (NORMALIZATION)
    job.status = ReportJobStatus.RUNNING
    job.completed_stages = [
        ReportJobStage.DISCOVERY,
        ReportJobStage.INGESTION,
        ReportJobStage.OCR,
        ReportJobStage.EXTRACTION,
    ]
    job.current_stage = ReportJobStage.NORMALIZATION
    job.checkpoints = {"discovered_files": ["sample.pdf"], "extracted_docs": 1}
    manager1._save_state(job)

    # 3. Simulate process death & reboot by instantiating a completely new manager
    manager2 = ReportJobManager(workspace_dir=str(tmp_path))
    recovered_jobs = manager2.recover_crashed_jobs(auto_resume=True)

    assert len(recovered_jobs) == 1
    rec = recovered_jobs[0]
    assert rec.job_id == job.job_id
    assert rec.status == ReportJobStatus.COMPLETED
    assert len(rec.completed_stages) == 12


def test_jobs_rest_api():
    create_resp = client.post(
        "/api/v1/report-jobs/create",
        json={"subsidiary_code": "CCL", "reporting_period": "FY 2023-24"},
    )
    assert create_resp.status_code == 200
    job_data = create_resp.json()
    job_id = job_data["job_id"]

    get_resp = client.get(f"/api/v1/report-jobs/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "pending"

    pause_resp = client.post(f"/api/v1/report-jobs/{job_id}/pause")
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "paused"

    recover_resp = client.post("/api/v1/report-jobs/recover?auto_resume=false")
    assert recover_resp.status_code == 200
    assert isinstance(recover_resp.json(), list)
