"""
Unit and integration tests for MasterReportGenerator — Section 15, 16, 17 of Master Plan.
"""
import os
import shutil
from pathlib import Path
from core.reports.planner.planner import ReportPlanner
from core.reports.generator.report_generator import MasterReportGenerator


def test_master_report_generator_end_to_end(tmp_path):
    test_output_dir = tmp_path / "reports_test"
    generator = MasterReportGenerator(output_dir=str(test_output_dir))

    planner = ReportPlanner()
    corpus = [
        {"id": "ccl_doc1", "text": "Raw coal production reached 85.0 MT in FY 2024-25."},
        {"id": "ccl_doc2", "text": "Solar power expansion projects generated 100 MW of renewable power."},
    ]

    plan = planner.generate_plan(
        current_evidence_corpus=corpus,
        report_title="Central Coalfields Limited Annual Report 2024-25",
        reporting_period="FY 2024-25",
        subsidiary_name="Central Coalfields Limited",
        template_name="classic",
        attach_evidence=False,
    )

    report, val_report = generator.generate_report(plan)

    assert report.report_id == plan.plan_id
    assert report.title == plan.report_title
    assert len(report.sections) == len(plan.sections)
    assert val_report.report_id == report.report_id

    # Verify files saved on disk
    expected_rep_path = test_output_dir / f"{report.report_id}.json"
    expected_val_path = test_output_dir / f"{report.report_id}_validation.json"

    assert expected_rep_path.exists()
    assert expected_val_path.exists()
