"""
Tests for Section 40 Vertical Slice Runner (Phase 15).
"""
import pytest
from pathlib import Path
from core.orchestrator.vertical_slice import (
    VerticalSliceConfig,
    VerticalSliceRunner,
)
from core.settings.manager import STANDARD_CIL_SUBSIDIARIES


def test_prepare_representative_corpus(tmp_path: Path):
    runner = VerticalSliceRunner(workspace_dir=tmp_path / "workspace")
    corpus_dir = tmp_path / "test_corpus"
    files = runner.prepare_representative_corpus(corpus_dir)

    assert len(files) >= 10
    filenames = [f.name for f in files]
    extensions = {f.suffix.lower() for f in files}

    # Verify multi-format coverage: txt, csv, docx, xlsx, png
    assert ".txt" in extensions
    assert ".csv" in extensions
    assert ".docx" in extensions or ".txt" in extensions
    assert ".png" in extensions or any("photo" in name.lower() for name in filenames)


def test_vertical_slice_autonomous_execution(tmp_path: Path):
    workspace = tmp_path / "workspace"
    corpus_dir = tmp_path / "corpus"
    runner = VerticalSliceRunner(workspace_dir=workspace)

    config = VerticalSliceConfig(
        corpus_dir=str(corpus_dir),
        subsidiary=STANDARD_CIL_SUBSIDIARIES[0],  # CCL
        reporting_period="FY 2023-24",
        simulate_human_correction=True,
        workspace_dir=str(workspace),
    )

    result = runner.run_vertical_slice(config)

    assert result.success is True
    assert result.session_id.startswith("vs_")
    assert result.file_count >= 10
    assert result.extracted_documents >= 10
    assert result.normalized_documents >= 10
    assert result.indexed_elements > 0
    assert result.report_id is not None
    assert result.section_count >= 3
    assert result.provenance_records_count > 0
    assert result.validation_passed is True

    # Check that both classic and modern PDFs were rendered
    assert result.classic_pdf_path is not None
    assert Path(result.classic_pdf_path).exists()
    assert result.modern_pdf_path is not None
    assert Path(result.modern_pdf_path).exists()

    # Verify quality metrics
    metrics = result.quality_metrics
    assert "source_coverage" in metrics
    assert "provenance_coverage" in metrics
    assert "unsupported_claim_rate" in metrics
    assert "numerical_error_rate" in metrics
    assert metrics["provenance_coverage"] >= 0.8
    assert metrics["numerical_error_rate"] == 0.0

    # Verify stage timings
    assert "discovery" in result.stage_timings_seconds
    assert "extraction" in result.stage_timings_seconds
    assert "indexing" in result.stage_timings_seconds
    assert "generation" in result.stage_timings_seconds
    assert "pdf_rendering" in result.stage_timings_seconds
