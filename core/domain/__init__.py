"""
Domain entities and schemas for Canonical Documents, Evidence, and Reports.
"""
from core.domain.documents import (
    BoundingBox,
    CanonicalDocument,
    DocumentElement,
    DocumentType,
    ElementType,
    Page,
)
from core.domain.evidence import EvidenceReference, ProvenanceRecord, SpreadsheetCoordinate
from core.domain.jobs import JobStage, JobStatus, ProcessingJob
from core.domain.reports import NarrativeBlock, Report, ReportSection, SectionType, ValidationStatus

__all__ = [
    "BoundingBox",
    "CanonicalDocument",
    "DocumentElement",
    "DocumentType",
    "ElementType",
    "EvidenceReference",
    "JobStage",
    "JobStatus",
    "NarrativeBlock",
    "Page",
    "ProcessingJob",
    "ProvenanceRecord",
    "Report",
    "ReportSection",
    "SectionType",
    "SpreadsheetCoordinate",
    "ValidationStatus",
]
