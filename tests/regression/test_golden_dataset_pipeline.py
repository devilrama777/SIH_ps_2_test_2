import pytest
from core.evaluation.golden_harness import GoldenRegressionHarness


def test_golden_dataset_end_to_end_regression(tmp_path):
    golden_dir = str(tmp_path / "golden")
    work_dir = str(tmp_path / "work")

    harness = GoldenRegressionHarness(golden_dir=golden_dir, workspace_dir=work_dir)
    result = harness.run_suite()

    # 1. Verify pipeline executed all steps
    assert result.total_golden_fixtures >= 4
    assert result.ingested_documents >= 3
    assert result.generated_sections >= 2
    assert result.audit_chain_verified is True
    assert result.pdf_generated is True
    assert result.pdf_path is not None

    # 2. Verify Section 32 quality metrics
    metrics = result.metrics
    assert metrics.provenance_coverage > 0.50
    assert metrics.numerical_error_rate == 0.0
    assert result.execution_duration_sec > 0
