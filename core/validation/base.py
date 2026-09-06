"""
Deterministic Validation Engine Base — Section 17 of Master Implementation Specification.

Executes deterministic mathematical, temporal, provenance, structural, visual,
and hyperlink consistency checks prior to final report composition.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from core.domain.reports import Report, ReportSection


class ValidationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(str, Enum):
    NUMERICAL = "numerical"
    TEMPORAL = "temporal"
    PROVENANCE = "provenance"
    STRUCTURAL = "structural"
    VISUAL = "visual"
    HYPERLINK = "hyperlink"


class ValidationIssue(BaseModel):
    """An individual inconsistency or rule violation flagged by the validation engine."""
    issue_id: str
    category: ValidationCategory
    severity: ValidationSeverity
    section_id: Optional[str] = None
    field_or_element: Optional[str] = None
    message: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    suggested_fix: Optional[str] = None


class ValidationResult(BaseModel):
    """Summary of all validation checks executed against a report or section."""
    is_valid: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    total_checks: int = 0
    passed_checks: int = 0
    warning_count: int = 0
    error_count: int = 0


class ValidationEngine(ABC):
    """
    Deterministic validator ensuring report fidelity and preventing LLM hallucination.
    """

    @abstractmethod
    def validate_report(self, report: Report) -> ValidationResult:
        """Execute full multi-dimensional validation suite across an entire report."""
        pass

    @abstractmethod
    def validate_section(self, section: ReportSection, report_context: Optional[Report] = None) -> ValidationResult:
        """Validate an individual section (e.g. after incremental agentic editing)."""
        pass
