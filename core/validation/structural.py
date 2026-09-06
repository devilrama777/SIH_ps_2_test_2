"""
Structural Validation Engine — Section 17 of Master Implementation Specification.

Ensures that statutory mandatory corporate sections exist, heading nesting is valid,
and the document hierarchy is consistent.
"""
from __future__ import annotations

from typing import List
from core.domain.reports import Report, ReportSection, SectionType
from core.validation.numerical import ValidationIssue


REQUIRED_MANDATORY_TOPICS = [
    "Corporate Overview",
    "Operational Performance",
    "Financial Highlights",
    "Safety",
    "Auditors' Report",
]


class StructuralValidator:
    """
    Verifies that the document hierarchy conforms to statutory reporting requirements.
    """

    def validate_report_structure(self, report: Report) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        all_titles = self._collect_all_titles(report.sections)

        # 1. Verify Mandatory Sections Exist
        for req in REQUIRED_MANDATORY_TOPICS:
            found = any(req.lower() in t.lower() for t in all_titles)
            if not found:
                issues.append(
                    ValidationIssue(
                        category="structural",
                        severity="error",
                        section_id=report.report_id,
                        message=f"Missing mandatory statutory section: '{req}' was not found in planned report structure.",
                        context={"required_topic": req},
                    )
                )

        # 2. Check Heading Hierarchy Nesting (no jumps e.g. 1 -> 3)
        def check_hierarchy(sections: List[ReportSection], parent_level: int = 0):
            for sec in sections:
                if sec.level > parent_level + 1:
                    issues.append(
                        ValidationIssue(
                            category="structural",
                            severity="warning",
                            section_id=sec.section_id,
                            message=f"Invalid heading hierarchy: section '{sec.title}' at level {sec.level} "
                                    f"directly follows parent at level {parent_level}.",
                            context={"section_id": sec.section_id, "level": sec.level, "parent_level": parent_level},
                        )
                    )
                check_hierarchy(sec.subsections, sec.level)

        check_hierarchy(report.sections, 0)
        return issues

    def _collect_all_titles(self, sections: List[ReportSection]) -> List[str]:
        titles = []
        for s in sections:
            titles.append(s.title)
            titles.extend(self._collect_all_titles(s.subsections))
        return titles
