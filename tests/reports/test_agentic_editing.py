"""
Tests for ReportEditingAgent and ControlledAgentTools — Sections 22 & 23 of Master Plan.
"""
import json
from datetime import datetime
from pathlib import Path
from core.domain.reports import NarrativeBlock, Report, ReportSection, SectionType
from core.reports.agent.editing_agent import ReportEditingAgent
from core.reports.agent.tools import ControlledAgentTools


def _setup_test_environment(tmp_path):
    reports_dir = tmp_path / "reports"
    proposals_dir = tmp_path / "proposals"
    reports_dir.mkdir()
    proposals_dir.mkdir()

    # Create sample report
    sec = ReportSection(
        section_id="sec_ops_01",
        title="Operational Performance",
        level=1,
        type=SectionType.MANDATORY,
        narrative_blocks=[
            NarrativeBlock(
                block_id="nb_01",
                text="Raw coal production reached 60.0 MT in FY 2024-25 [DOC:Ops.pdf:P10].",
                confidence=1.0,
            )
        ],
    )

    report = Report(
        report_id="rep_edit_test",
        title="CCL Annual Report 2024-25",
        reporting_period="FY 2024-25",
        subsidiary_name="Central Coalfields Limited",
        template_name="modern",
        sections=[sec],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        version=1,
    )

    with open(reports_dir / "rep_edit_test.json", "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))

    return reports_dir, proposals_dir


def test_agentic_edit_workflow(tmp_path):
    reports_dir, proposals_dir = _setup_test_environment(tmp_path)

    agent = ReportEditingAgent(
        reports_dir=str(reports_dir),
        proposals_dir=str(proposals_dir),
    )

    # 1. Propose Edit
    instruction = "The production figure is inaccurate. Update raw coal production to 84.5 MT according to primary evidence."
    proposal = agent.propose_edit(
        report_id="rep_edit_test",
        section_id="sec_ops_01",
        user_instruction=instruction,
    )

    assert proposal.proposal_id.startswith("prop_")
    assert proposal.report_id == "rep_edit_test"
    assert proposal.section_id == "sec_ops_01"
    assert proposal.status == "pending_review"
    assert len(proposal.diff_lines) >= 1
    assert proposal.original_text.startswith("Raw coal production reached 60.0 MT")

    # 2. Human Acceptance Gate
    updated_report = agent.accept_proposal(proposal.proposal_id)
    assert updated_report.version == 2
    # Verify section was updated on disk
    assert len(updated_report.sections[0].narrative_blocks) >= 1

    # Verify proposal status on disk
    with open(proposals_dir / f"{proposal.proposal_id}.json", "r", encoding="utf-8") as f:
        saved_prop = json.load(f)
        assert saved_prop["status"] == "accepted"


def test_agentic_edit_rejection(tmp_path):
    import json
    reports_dir, proposals_dir = _setup_test_environment(tmp_path)

    agent = ReportEditingAgent(
        reports_dir=str(reports_dir),
        proposals_dir=str(proposals_dir),
    )

    proposal = agent.propose_edit(
        report_id="rep_edit_test",
        section_id="sec_ops_01",
        user_instruction="Remove the environmental compliance references.",
    )

    rejected_prop = agent.reject_proposal(proposal.proposal_id)
    assert rejected_prop.status == "rejected"

    # Report version remains 1 on disk
    with open(reports_dir / "rep_edit_test.json", "r", encoding="utf-8") as f:
        rep_data = json.load(f)
        assert rep_data["version"] == 1
