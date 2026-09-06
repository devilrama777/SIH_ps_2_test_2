"""
Report Editing Agent — Section 22 of Master Implementation Specification.

Executes source-aware section editing, evidence verification, diff generation,
deterministic validation, and human-in-the-loop approval workflows.
"""
from __future__ import annotations

import difflib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.ai.gateway.base import AIGateway
from core.ai.gateway.local_gateway import LocalAIGateway
from core.ai.prompts.templates import SYSTEM_PROMPT_FACTUAL
from core.domain.reports import NarrativeBlock, Report, ReportSection, ValidationStatus
from core.reports.agent.tools import ControlledAgentTools
from core.validation.engine import ValidationEngine, ValidationReport


class DiffLine(BaseModel):
    operation: str  # '+', '-', ' '
    text: str


class EditProposal(BaseModel):
    """Structured proposal for human review before applying report modifications."""
    proposal_id: str
    report_id: str
    section_id: str
    user_instruction: str
    original_text: str
    proposed_text: str
    diff_lines: List[DiffLine]
    validation_status: ValidationStatus
    validation_issues_count: int
    status: str = "pending_review"  # 'pending_review', 'accepted', 'rejected'
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReportEditingAgent:
    """
    Coordinates source-aware editing, evidence re-grounding, validation,
    and human approval gates.
    """

    def __init__(
        self,
        ai_gateway: Optional[AIGateway] = None,
        agent_tools: Optional[ControlledAgentTools] = None,
        validation_engine: Optional[ValidationEngine] = None,
        reports_dir: str = "data/workspace/reports",
        proposals_dir: str = "data/workspace/proposals",
    ):
        self.ai_gateway = ai_gateway or LocalAIGateway()
        self.tools = agent_tools or ControlledAgentTools()
        self.validation = validation_engine or ValidationEngine()
        self.reports_dir = Path(reports_dir)
        self.proposals_dir = Path(proposals_dir)
        self.proposals_dir.mkdir(parents=True, exist_ok=True)

    def propose_edit(
        self,
        report_id: str,
        section_id: str,
        user_instruction: str,
    ) -> EditProposal:
        # 1. Load active report
        rep_file = self.reports_dir / f"{report_id}.json"
        if not rep_file.exists():
            raise FileNotFoundError(f"Report {report_id} not found")

        with open(rep_file, "r", encoding="utf-8") as f:
            report = Report.model_validate_json(f.read())

        # 2. Locate target section
        sec = self._find_section(report.sections, section_id)
        if not sec:
            raise ValueError(f"Section {section_id} not found in report {report_id}")

        original_text = "\n\n".join(nb.text for nb in sec.narrative_blocks)

        # 3. Search verified source evidence using query keywords
        evidence_results = self.tools.search_documents(
            f"{sec.title} {user_instruction}",
            limit=5,
        )

        evidence_snippets = []
        if evidence_results.success and evidence_results.data:
            for item in evidence_results.data:
                cite = f"[DOC:{item['source_reference']}:P{item.get('page_number') or 1}]"
                evidence_snippets.append(f"- {cite}: {item['text']}")

        evidence_context = "\n".join(evidence_snippets) or "- Verified primary evidence from reporting corpus."

        # 4. Prompt Local AI for grounded revision
        prompt = (
            f"User Editing Instruction: '{user_instruction}'\n\n"
            f"Section Title: '{sec.title}'\n"
            f"Current Section Text:\n{original_text}\n\n"
            f"Verified Evidence Context:\n{evidence_context}\n\n"
            f"Task:\n"
            f"Apply the correction accurately according to the verified evidence.\n"
            f"Preserve or update all bracketed citations [DOC:filename:Pxx] or [COORD:workbook:sheet:cell].\n"
            f"Revised Narrative:"
        )

        ai_res = self.ai_gateway.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT_FACTUAL)
        proposed_text = ai_res.content.strip()

        # 5. Compute Structured Line Diff
        diff_lines = self._compute_diff(original_text, proposed_text)

        # 6. Validate Proposed Section
        val_issues = self.validation.numerical.validate_section(section_id, proposed_text, sec.tables)
        val_status = ValidationStatus.VALID if not val_issues else ValidationStatus.WARNING

        proposal_id = f"prop_{uuid.uuid4().hex[:10]}"
        proposal = EditProposal(
            proposal_id=proposal_id,
            report_id=report_id,
            section_id=section_id,
            user_instruction=user_instruction,
            original_text=original_text,
            proposed_text=proposed_text,
            diff_lines=diff_lines,
            validation_status=val_status,
            validation_issues_count=len(val_issues),
            status="pending_review",
        )

        # 7. Persist proposal to disk
        with open(self.proposals_dir / f"{proposal_id}.json", "w", encoding="utf-8") as f:
            f.write(proposal.model_dump_json(indent=2))

        return proposal

    def accept_proposal(self, proposal_id: str) -> Report:
        """Human approval: Applies the proposed text to the report on disk."""
        prop_file = self.proposals_dir / f"{proposal_id}.json"
        if not prop_file.exists():
            raise FileNotFoundError(f"Proposal {proposal_id} not found")

        with open(prop_file, "r", encoding="utf-8") as f:
            proposal = EditProposal.model_validate_json(f.read())

        rep_file = self.reports_dir / f"{proposal.report_id}.json"
        with open(rep_file, "r", encoding="utf-8") as f:
            report = Report.model_validate_json(f.read())

        # Update target section narrative
        sec = self._find_section(report.sections, proposal.section_id)
        if not sec:
            raise ValueError(f"Section {proposal.section_id} not found")

        paragraphs = [p.strip() for p in proposal.proposed_text.split("\n\n") if p.strip()]
        new_blocks = [
            NarrativeBlock(
                block_id=f"nb_{proposal.section_id}_{idx:02d}",
                text=p,
                confidence=1.0,
            )
            for idx, p in enumerate(paragraphs, 1)
        ]
        sec.narrative_blocks = new_blocks
        sec.validation_status = proposal.validation_status
        report.version += 1
        report.updated_at = datetime.utcnow()

        # Persist updated report
        with open(rep_file, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        # Mark proposal as accepted
        proposal.status = "accepted"
        with open(prop_file, "w", encoding="utf-8") as f:
            f.write(proposal.model_dump_json(indent=2))

        return report

    def reject_proposal(self, proposal_id: str) -> EditProposal:
        """Human rejection: Discards proposal without modifying report."""
        prop_file = self.proposals_dir / f"{proposal_id}.json"
        if not prop_file.exists():
            raise FileNotFoundError(f"Proposal {proposal_id} not found")

        with open(prop_file, "r", encoding="utf-8") as f:
            proposal = EditProposal.model_validate_json(f.read())

        proposal.status = "rejected"
        with open(prop_file, "w", encoding="utf-8") as f:
            f.write(proposal.model_dump_json(indent=2))

        return proposal

    def _find_section(self, sections: List[ReportSection], section_id: str) -> Optional[ReportSection]:
        for s in sections:
            if s.section_id == section_id:
                return s
            sub = self._find_section(s.subsections, section_id)
            if sub:
                return sub
        return None

    def _compute_diff(self, original: str, proposed: str) -> List[DiffLine]:
        orig_lines = original.splitlines()
        prop_lines = proposed.splitlines()
        differ = difflib.Differ()
        diff = list(differ.compare(orig_lines, prop_lines))

        res = []
        for line in diff:
            if not line:
                continue
            op = line[0]
            content = line[2:]
            if op in ("+", "-", " "):
                res.append(DiffLine(operation=op, text=content))
        return res
