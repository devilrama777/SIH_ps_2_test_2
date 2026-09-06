"""
Master Report Generator — Sections 15, 16, and 17 of Master Implementation Specification.

Orchestrates section-by-section generation from a ReportPlan, applies the deterministic
validation engine, and persists the verified intermediate Report JSON representation.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from core.domain.reports import Report, ReportSection
from core.reports.generator.section_generator import SectionGenerator
from core.reports.planner.planner import ReportPlan
from core.validation.engine import ValidationEngine, ValidationReport


class MasterReportGenerator:
    """
    Executes staged report generation from an approved ReportPlan and validates output.
    """

    def __init__(
        self,
        section_generator: Optional[SectionGenerator] = None,
        validation_engine: Optional[ValidationEngine] = None,
        output_dir: str = "data/workspace/reports",
    ):
        self.section_generator = section_generator or SectionGenerator()
        self.validation_engine = validation_engine or ValidationEngine()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_report(self, plan: ReportPlan) -> Tuple[Report, ValidationReport]:
        # 1. Generate sections node by node
        generated_sections = []
        for planned_sec in plan.sections:
            sec_content = self.section_generator.generate_section_content(planned_sec)
            generated_sections.append(sec_content)

        # 2. Assemble Master Report
        report = Report(
            report_id=plan.plan_id,
            title=plan.report_title,
            reporting_period=plan.reporting_period,
            subsidiary_name=plan.subsidiary_name,
            template_name=plan.template_name,
            sections=generated_sections,
            created_at=plan.created_at,
            updated_at=datetime.utcnow(),
            version=1,
            metadata={"source_plan_id": plan.plan_id},
        )

        # 3. Execute Deterministic Validation Engine
        val_report = self.validation_engine.validate_report(report)

        # 4. Save Report & Validation Findings to Disk
        self._persist_report(report, val_report)

        return report, val_report

    def _persist_report(self, report: Report, val_report: ValidationReport) -> None:
        report_file = Path(self.output_dir) / f"{report.report_id}.json"
        val_file = Path(self.output_dir) / f"{report.report_id}_validation.json"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        with open(val_file, "w", encoding="utf-8") as f:
            f.write(val_report.model_dump_json(indent=2))
