"""
Report Data Model — Section 15 of Master Implementation Specification.

Represents an intermediate, renderer-independent report structure that can be:
- dynamically constructed by the Report Planner,
- verified by the Validation Engine,
- reviewed & edited by the Human/Agent Review System,
- rendered into either Classic or Modern PDF templates.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from core.domain.evidence import EvidenceReference


class SectionType(str, Enum):
    MANDATORY = "mandatory"
    OPTIONAL = "optional"
    CONDITIONAL = "conditional"
    RECURRING = "recurring"
    DISCOVERED = "discovered"
    NEW_TOP_LEVEL = "new_top_level"
    NEW_SUBSECTION = "new_subsection"


class ValidationStatus(str, Enum):
    UNVALIDATED = "unvalidated"
    VALID = "valid"
    WARNING = "warning"
    FAILED = "failed"


class NarrativeBlock(BaseModel):
    """A paragraph or narrative unit within a section with explicit provenance links."""
    block_id: str
    text: str
    evidence_refs: List[EvidenceReference] = Field(default_factory=list)
    confidence: Optional[float] = None
    insufficient_evidence: bool = False


class ReportSection(BaseModel):
    """Structured report section independent of final layout."""
    section_id: str
    title: str
    level: int = Field(default=1, ge=1, le=5, description="Heading level (1 = Top level chapter, 2 = Subsection)")
    type: SectionType = SectionType.MANDATORY
    discovery_reason: Optional[str] = None
    narrative_blocks: List[NarrativeBlock] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    charts: List[Dict[str, Any]] = Field(default_factory=list)
    images: List[Dict[str, Any]] = Field(default_factory=list)
    links: List[Dict[str, Any]] = Field(default_factory=list)
    source_refs: List[str] = Field(default_factory=list, description="IDs of source documents supporting this section")
    validation_status: ValidationStatus = ValidationStatus.UNVALIDATED
    subsections: List[ReportSection] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Report(BaseModel):
    """The complete structured report instance."""
    report_id: str
    title: str
    reporting_period: str
    subsidiary_name: str = "Coal India Limited Subsidiary"
    template_name: str = Field(default="modern", description="'classic' or 'modern'")
    sections: List[ReportSection] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)
