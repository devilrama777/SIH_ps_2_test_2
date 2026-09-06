"""
Integration tests for EnterpriseReportPipeline.
Phase 13 (Section 33, 40, and 46).
"""
import uuid
from pathlib import Path

import pytest

from core.evaluation.golden_dataset import GoldenDatasetBuilder
from core.orchestrator.models import PipelineConfig, PipelineStage
from core.orchestrator.pipeline import EnterpriseReportPipeline
from core.security.audit_logger import AuditLogger


@pytest.fixture
def golden_source_dir(tmp_path: Path) -> Path:
    builder = GoldenDatasetBuilder(base_dir=str(tmp_path / "golden_input"))
    return builder.build_dataset()


def test_enterprise_report_pipeline_end_to_end(golden_source_dir: Path, tmp_path: Path):
    workspace = tmp_path / "pipeline_workspace"
    audit_db = workspace / "audit.db"
    audit_logger = AuditLogger(db_path=str(audit_db))

    pipeline = EnterpriseReportPipeline(workspace_dir=workspace, audit_logger=audit_logger)
    session_id = str(uuid.uuid4())

    config = PipelineConfig(
        session_id=session_id,
        source_folder=str(golden_source_dir),
        subsidiary="Central Coalfields Limited",
        reporting_year="2024-25",
        reporting_period="Annual",
        template_style="modern",
    )

    session = pipeline.run(config)

    # 1. Pipeline Lifecycle Assertions
    assert session.session_id == session_id
    assert session.current_stage == PipelineStage.COMPLETED
    assert session.progress_percent == 100.0
    assert session.error is None
    assert session.report_id is not None
    assert session.pdf_path is not None
    assert Path(session.pdf_path).exists()
    assert Path(session.pdf_path).stat().st_size > 0

    # 2. Quality Metrics Assertions (Section 32)
    assert session.metrics is not None
    assert session.metrics["provenance_coverage"] >= 0.85
    assert session.metrics["numerical_error_rate"] == 0.0
    assert session.metrics["validation_passed"] is True

    # 3. Stage Log Entries Assertions
    stages_logged = {entry.stage for entry in session.logs}
    assert PipelineStage.DISCOVERY in stages_logged
    assert PipelineStage.EXTRACTION in stages_logged
    assert PipelineStage.INDEXING in stages_logged
    assert PipelineStage.PLANNING in stages_logged
    assert PipelineStage.GENERATION in stages_logged
    assert PipelineStage.VALIDATION in stages_logged
    assert PipelineStage.PDF_RENDERING in stages_logged
    assert PipelineStage.COMPLETED in stages_logged

    # 4. Session Persistence Assertions
    loaded = pipeline.load_session(session_id)
    assert loaded is not None
    assert loaded.session_id == session_id
    assert loaded.report_id == session.report_id

    # 5. Audit Logger Chaining Verification
    trail = audit_logger.list_logs()
    assert len(trail) >= 1
    assert any(entry.action == "enterprise_pipeline_execution" for entry in trail)
    assert audit_logger.verify_chain_integrity() is True
