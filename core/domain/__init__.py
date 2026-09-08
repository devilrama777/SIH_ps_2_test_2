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
from core.domain.evidence import (
    ProvenanceRecord,
    EvidenceReference,
    SpreadsheetCoordinate,
    SpreadsheetLocator,
    PdfLocator,
    DocxLocator,
    ImageLocator,
    TextLocator,
    SourceLocator,
)
from core.domain.jobs import JobStage, JobStatus, JobError, ProcessingJob
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
    "DocxLocator",
    "DocumentElement",
    "DocumentType",
    "ElementType",
    "EvidenceReference",
    "ImageLocator",
    "JobError",
    "JobStage",
    "JobStatus",
    "NarrativeBlock",
    "Page",
    "PdfLocator",
    "ProcessingJob",
    "ProvenanceRecord",
    "Report",
    "ReportSection",
    "SectionType",
    "SecuritySettings",
    "SourceLocator",
    "SpreadsheetCoordinate",
    "SpreadsheetLocator",
    "StorageSettings",
    "SubsidiaryProfile",
    "TemplateSettings",
    "TextLocator",
    "ValidationStatus",
]

