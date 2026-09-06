"""
Master Validation Engine — Section 17 of Master Implementation Specification.

Executes deterministic multi-dimensional validation across:
- Numerical accuracy & arithmetic
- Temporal consistency
- Provenance & citation integrity
- Structural completeness
- Visual layout bounds
- Hyperlink validity
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.domain.reports import Report, ReportSection, ValidationStatus
from core.validation.numerical import NumericalValidator, ValidationIssue
from core.validation.provenance import ProvenanceValidator
from core.validation.structural import StructuralValidator
from core.validation.temporal import TemporalValidator


class ValidationReport(BaseModel):
    """Consolidated findings from deterministic validation inspection."""
    report_id: str
    overall_status: ValidationStatus
    total_issues: int = 0
    error_count: int = 0
    warning_count: int = 0
    issues: List[ValidationIssue] = Field(default_factory=list)
    passed: bool = True


class ValidationEngine:
    """
    Coordinates all deterministic validation checks across the report before final approval.
    """

    def __init__(
        self,
        numerical_validator: Optional[NumericalValidator] = None,
        temporal_validator: Optional[TemporalValidator] = None,
        provenance_validator: Optional[ProvenanceValidator] = None,
        structural_validator: Optional[StructuralValidator] = None,
    ):
        self.numerical = numerical_validator or NumericalValidator()
        self.temporal = temporal_validator or TemporalValidator()
        self.provenance = provenance_validator or ProvenanceValidator()
        self.structural = structural_validator or StructuralValidator()

    def validate_report(self, report: Report) -> ValidationReport:
        issues: List[ValidationIssue] = []

        # 1. Structural Validation across document hierarchy
        struct_issues = self.structural.validate_report_structure(report)
        issues.extend(struct_issues)

        # 2. Section-level validations (Numerical, Temporal, Provenance, Visual, Links)
        def validate_sections_recursive(sections: List[ReportSection]):
            for sec in sections:
                sec_issues: List[ValidationIssue] = []
                combined_text = " ".join(nb.text for nb in sec.narrative_blocks)

                # Numerical checks
                num_issues = self.numerical.validate_section(sec.section_id, combined_text, sec.tables)
                sec_issues.extend(num_issues)

                # Temporal checks
                temp_issues = self.temporal.validate_section(sec.section_id, combined_text, report.reporting_period)
                sec_issues.extend(temp_issues)

                # Provenance checks for each narrative block
                for block in sec.narrative_blocks:
                    prov_issues = self.provenance.validate_narrative_block(sec.section_id, block)
                    sec_issues.extend(prov_issues)

                # Visual bounds (e.g. table columns > 10)
                for tbl in sec.tables:
                    headers = tbl.get("headers", [])
                    if len(headers) > 10:
                        sec_issues.append(
                            ValidationIssue(
                                category="visual",
                                severity="warning",
                                section_id=sec.section_id,
                                message=f"Table '{tbl.get('table_id')}' has {len(headers)} columns, risk of horizontal overflow.",
                            )
                        )

                # Links validity (must start with http/https)
                for link in sec.links:
                    url = link.get("url", "")
                    if not url.startswith("http://") and not url.startswith("https://"):
                        sec_issues.append(
                            ValidationIssue(
                                category="links",
                                severity="warning",
                                section_id=sec.section_id,
                                message=f"Malformed hyperlink: '{url}' lacks http/https scheme.",
                            )
                        )

                # Update Section validation_status
                has_errors = any(i.severity == "error" for i in sec_issues)
                has_warnings = any(i.severity == "warning" for i in sec_issues)

                if has_errors:
                    sec.validation_status = ValidationStatus.FAILED
                elif has_warnings:
                    sec.validation_status = ValidationStatus.WARNING
                else:
                    sec.validation_status = ValidationStatus.VALID

                issues.extend(sec_issues)
                validate_sections_recursive(sec.subsections)

        validate_sections_recursive(report.sections)

        error_count = sum(1 for i in issues if i.severity == "error")
        warning_count = sum(1 for i in issues if i.severity == "warning")

        if error_count > 0:
            overall_status = ValidationStatus.FAILED
            passed = False
        elif warning_count > 0:
            overall_status = ValidationStatus.WARNING
            passed = True
        else:
            overall_status = ValidationStatus.VALID
            passed = True

        return ValidationReport(
            report_id=report.report_id,
            overall_status=overall_status,
            total_issues=len(issues),
            error_count=error_count,
            warning_count=warning_count,
            issues=issues,
            passed=passed,
        )
