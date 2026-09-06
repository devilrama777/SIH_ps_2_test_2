import json
import zipfile
import pytest
from pathlib import Path
from core.observability.telemetry import ObservabilityManager
from core.observability.exporter import SanitizedDiagnosticExporter


def test_observability_manager_stage_telemetry(tmp_path):
    mgr = ObservabilityManager(log_dir=str(tmp_path / "logs"), max_in_memory=5)

    mgr.record_stage(
        stage_name="EXTRACTION",
        duration_sec=1.45,
        status="SUCCESS",
        model_used="pymupdf",
        document_ids=["doc_1", "doc_2"],
    )

    mgr.record_stage(
        stage_name="OCR",
        duration_sec=3.20,
        status="FAILED",
        error_message="Image resolution below threshold",
    )

    events = mgr.get_recent_telemetry()
    assert len(events) == 2
    assert events[0]["stage_name"] == "EXTRACTION"
    assert events[1]["status"] == "FAILED"

    aggregates = mgr.get_stage_aggregates()
    assert "EXTRACTION" in aggregates
    assert aggregates["EXTRACTION"]["count"] == 1
    assert aggregates["EXTRACTION"]["failures"] == 0
    assert "OCR" in aggregates
    assert aggregates["OCR"]["failures"] == 1


def test_sanitized_diagnostic_exporter_bundle(tmp_path):
    obs = ObservabilityManager(log_dir=str(tmp_path / "logs"))
    obs.record_stage(
        stage_name="PLANNING",
        duration_sec=0.85,
        status="SUCCESS",
        metrics={"token_secret": "my_secret_api_key_12345", "user_email": "officer@coalindia.in"},
    )

    exporter = SanitizedDiagnosticExporter(
        workspace_dir=str(tmp_path),
        observability_manager=obs,
    )

    bundle_info = exporter.export_bundle()

    assert bundle_info.bundle_path.endswith(".zip")
    assert Path(bundle_info.bundle_path).exists()
    assert len(bundle_info.sha256_hash) == 64

    # Inspect zip contents
    with zipfile.ZipFile(bundle_info.bundle_path, "r") as zf:
        namelist = zf.namelist()
        assert "system_environment.json" in namelist
        assert "storage_breakdown.json" in namelist
        assert "telemetry_log.json" in namelist
        assert "manifest.json" in namelist

        telemetry_raw = zf.read("telemetry_log.json").decode("utf-8")
        # Ensure email and secret patterns are sanitized/redacted
        assert "officer@coalindia.in" not in telemetry_raw
        assert "[EMAIL_REDACTED]" in telemetry_raw
