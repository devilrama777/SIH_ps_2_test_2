"""
Tests for Section 22 Human + Agent Review System, Diff Workflow,
Section 28 Invalidation, and Section 32 Report Quality Metrics.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.domain.reports import NarrativeBlock, Report, ReportSection, SectionType, ValidationStatus
from core.reports.agent.editing_agent import ReportEditingAgent
from core.evaluation.metrics import ReportQualityEvaluator, ReportQualityMetrics

client = TestClient(app)


@pytest.fixture
def mock_report_environment(tmp_path: Path):
    """Creates a sample report and directories for testing review workflows."""
    reports_dir = tmp_path / "reports"
    proposals_dir = tmp_path / "proposals"
    reports_dir.mkdir(parents=True, exist_ok=True)
    proposals_dir.mkdir(parents=True, exist_ok=True)

    report_id = "rep_test_review_01"
    section_id = "sec_financial_01"

    sec = ReportSection(
        section_id=section_id,
        title="Financial and Operational Performance",
        section_type=SectionType.MANDATORY,
        source_refs=["BCCL_Annual_Report_FY24.pdf"],
        narrative_blocks=[
            NarrativeBlock(
                block_id="nb_01",
                text="In FY 2023-24, BCCL produced 41.2 MT of coking coal [DOC:BCCL_Annual_Report_FY24.pdf:P12]. Total revenue stood at 14500 crore INR [DOC:BCCL_Annual_Report_FY24.pdf:P15].",
            )
        ],
    )

    report = Report(
        report_id=report_id,
        title="BCCL Annual Report FY 2023-24",
        reporting_period="FY 2023-24",
        sections=[sec],
        version=1,
    )

    with open(reports_dir / f"{report_id}.json", "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))

    return reports_dir, proposals_dir, report_id, section_id


def test_editing_agent_diff_generation_and_validation(mock_report_environment):
    reports_dir, proposals_dir, report_id, section_id = mock_report_environment
    agent = ReportEditingAgent(reports_dir=str(reports_dir), proposals_dir=str(proposals_dir))

    instruction = "Update coking coal production to 42.5 MT as verified in latest auditor note."
    proposal = agent.propose_edit(
        report_id=report_id,
        section_id=section_id,
        user_instruction=instruction,
    )

    assert proposal.proposal_id.startswith("prop_")
    assert proposal.report_id == report_id
    assert proposal.section_id == section_id
    assert proposal.status == "pending_review"
    assert len(proposal.diff_lines) > 0
    assert any(dl.operation in ("+", "-") for dl in proposal.diff_lines)

    # Check persistence
    prop_path = proposals_dir / f"{proposal.proposal_id}.json"
    assert prop_path.exists()


def test_human_accept_and_reject_lifecycle(mock_report_environment):
    reports_dir, proposals_dir, report_id, section_id = mock_report_environment
    agent = ReportEditingAgent(reports_dir=str(reports_dir), proposals_dir=str(proposals_dir))

    # 1. Propose edit
    proposal = agent.propose_edit(
        report_id=report_id,
        section_id=section_id,
        user_instruction="Revise dispatch estimate.",
    )

    # 2. Reject proposal
    rejected = agent.reject_proposal(proposal.proposal_id)
    assert rejected.status == "rejected"

    # Report version unchanged
    with open(reports_dir / f"{report_id}.json", "r", encoding="utf-8") as f:
        rep_unchanged = Report.model_validate_json(f.read())
    assert rep_unchanged.version == 1

    # 3. Create second proposal & accept
    prop2 = agent.propose_edit(
        report_id=report_id,
        section_id=section_id,
        user_instruction="Accepted revision with exact provenance.",
    )
    accepted_report = agent.accept_proposal(prop2.proposal_id)

    assert accepted_report.version == 2
    assert accepted_report.sections[0].narrative_blocks[0].text == prop2.proposed_text


def test_report_quality_metrics_evaluator(mock_report_environment):
    reports_dir, _, report_id, _ = mock_report_environment
    evaluator = ReportQualityEvaluator()

    with open(reports_dir / f"{report_id}.json", "r", encoding="utf-8") as f:
        report = Report.model_validate_json(f.read())

    metrics: ReportQualityMetrics = evaluator.evaluate_report(
        report=report,
        discovered_source_ids=["BCCL_Annual_Report_FY24.pdf"],
    )

    assert metrics.report_id == report_id
    assert metrics.provenance_coverage_percent > 0.0
    assert metrics.source_coverage_percent == 100.0
    assert metrics.overall_quality_score > 50.0
    assert metrics.quality_grade in ["A (Exemplary)", "B (Publishable)", "C (Minor Deficiencies)"]


def test_rest_api_agent_review_and_metrics():
    # Setup report in server reports directory for API integration test
    server_rep_dir = Path("data/workspace/reports")
    server_rep_dir.mkdir(parents=True, exist_ok=True)
    rep_id = "rep_api_test_01"
    sec_id = "sec_test_01"

    sec = ReportSection(
        section_id=sec_id,
        title="Production Overview",
        section_type=SectionType.MANDATORY,
        source_refs=["ECL_Production_FY24.xlsx"],
        narrative_blocks=[
            NarrativeBlock(
                block_id="nb_api_01",
                text="ECL extracted 35.8 MT of coal during FY 2023-24 [DOC:ECL_Production_FY24.xlsx:P1].",
            )
        ],
    )
    rep = Report(
        report_id=rep_id,
        title="ECL Operations",
        reporting_period="FY 2023-24",
        sections=[sec],
        version=1,
    )
    with open(server_rep_dir / f"{rep_id}.json", "w", encoding="utf-8") as f:
        f.write(rep.model_dump_json(indent=2))

    # 1. POST /api/v1/agent/review/propose-edit
    payload = {
        "report_id": rep_id,
        "section_id": sec_id,
        "user_instruction": "Correct coal extraction to 36.2 MT based on final audit reconciliation.",
    }
    resp = client.post("/api/v1/agent/review/propose-edit", json=payload)
    assert resp.status_code == 200
    p_data = resp.json()
    proposal_id = p_data["proposal_id"]
    assert p_data["status"] == "pending_review"

    # 2. GET /api/v1/agent/review/proposals/{proposal_id}
    get_resp = client.get(f"/api/v1/agent/review/proposals/{proposal_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["proposal_id"] == proposal_id

    # 3. POST /api/v1/agent/review/proposals/{proposal_id}/accept
    accept_resp = client.post(f"/api/v1/agent/review/proposals/{proposal_id}/accept")
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == "accepted"
    assert accept_resp.json()["version"] == 2

    # 4. POST /api/v1/reports/{report_id}/quality-metrics
    qm_resp = client.post(f"/api/v1/reports/{rep_id}/quality-metrics")
    assert qm_resp.status_code == 200
    qm_data = qm_resp.json()
    assert qm_data["overall_quality_score"] > 0.0

    # 5. POST /api/v1/reports/{report_id}/invalidate
    inv_payload = {
        "changed_sources": ["ECL_Production_FY24.xlsx"],
    }
    inv_resp = client.post(f"/api/v1/reports/{rep_id}/invalidate", json=inv_payload)
    assert inv_resp.status_code == 200
    inv_data = inv_resp.json()
    assert sec_id in inv_data["affected_section_ids"]
