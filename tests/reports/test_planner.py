"""
Unit and integration tests for ReportPlanner and ReportPlan (Sections 13, 14, 15).
"""
from core.domain.reports import SectionType
from core.reports.planner.planner import ReportPlanner


def test_report_planner_hierarchy_generation():
    planner = ReportPlanner()

    evidence_corpus = [
        {"id": "doc1", "text": "Raw coal production reached 773.60 MT in Eastern Coalfields."},
        {"id": "doc2", "text": "Deployed drone survey and sap erp digital mine telemetry across opencast projects."},
        {"id": "doc3", "text": "First mile connectivity (FMC) conveyor commissioned at 20 MT capacity."},
    ]

    plan = planner.generate_plan(
        current_evidence_corpus=evidence_corpus,
        report_title="CIL Subsidiary Annual Report 2024-25",
        reporting_period="2024-25",
        subsidiary_name="Eastern Coalfields Limited",
        template_name="modern",
        attach_evidence=False,  # Fast offline unit test
    )

    assert plan.plan_id.startswith("plan_")
    assert plan.report_title == "CIL Subsidiary Annual Report 2024-25"
    assert plan.reporting_period == "2024-25"
    assert len(plan.sections) >= 9

    # Verify dynamic insertion of Discovered top-level sections
    section_titles = [s.title for s in plan.sections]
    assert any("Digital Mine Transformation" in t for t in section_titles)

    digital_sec = next(s for s in plan.sections if "Digital Mine" in s.title)
    assert digital_sec.type == SectionType.NEW_TOP_LEVEL
    assert digital_sec.discovery_reason is not None

    # Test conversion to domain Report skeleton
    report_skeleton = plan.to_report_skeleton()
    assert report_skeleton.report_id == plan.plan_id
    assert report_skeleton.template_name == "modern"
    assert len(report_skeleton.sections) == len(plan.sections)
    assert report_skeleton.sections[0].section_id is not None
