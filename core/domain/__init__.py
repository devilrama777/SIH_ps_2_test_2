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
from core.domain.settings import (
    AISettings,
    ApplicationSettings,
    SecuritySettings,
    StorageSettings,
    SubsidiaryProfile,
    TemplateSettings,
)

__all__ = [
    "AISettings",
    "ApplicationSettings",
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
    "SecuritySettings",
    "SpreadsheetCoordinate",
    "StorageSettings",
    "SubsidiaryProfile",
    "TemplateSettings",
    "ValidationStatus",
]

