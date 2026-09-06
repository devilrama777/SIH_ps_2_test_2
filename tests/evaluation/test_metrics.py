import pytest
from core.domain.reports import NarrativeBlock, Report, ReportSection
from core.evaluation.metrics import QualityMetricCalculator


def test_quality_metrics_calculator(tmp_path):
    calc = QualityMetricCalculator(canonical_dir=str(tmp_path))

    # Construct test report with narrative blocks and tables
    sec1 = ReportSection(
        section_id="sec_01",
        title="Operational Performance",
        narrative_blocks=[
            NarrativeBlock(
                block_id="b1",
                text="CCL raw coal production reached 84.50 MT [DOC:CCL_Production.pdf:P4].",
            ),
            NarrativeBlock(
                block_id="b2",
                text="Composite OBR was 132.40 M.Cu.M [COORD:Ops.xlsx:Sheet1:D10].",
            ),
        ],
        tables=[
            {
                "table_id": "t1",
                "title": "Production Summary",
                "headers": ["Area", "Production MT"],
                "rows": [["North Karanpura", "31.20"], ["Total", "84.50"]],
                "source_reference": "CCL_Production.pdf:P4",
            }
        ],
    )

    report = Report(
        report_id="rep_test_01",
        title="Annual Report",
        reporting_period="FY 2023-24",
        sections=[sec1],
    )

    ground_truth = {
        "key_metrics": {
            "production_mt": 84.50,
            "obr_mcum": 132.40,
        }
    }

    metrics = calc.evaluate_report(report, ground_truth=ground_truth)

    assert metrics.provenance_coverage == 1.0  # Both blocks + table cited
    assert metrics.source_coverage == 1.0
    assert metrics.unsupported_claim_rate == 0.0
    assert metrics.passed_quality_threshold is True
