"""
Report Planner Subsystem — Section 13, 14, 15 of Master Implementation Specification.
"""
from core.reports.planner.reference_analyzer import ReferenceReportAnalyzer, ReferenceReportAnalysis
from core.reports.planner.topic_discovery import TopicDiscoveryEngine, DiscoveredCandidate
from core.reports.planner.evidence_mapper import EvidenceToSectionMapper, SectionEvidencePackage
from core.reports.planner.planner import ReportPlanner, ReportPlan, PlannedSection

__all__ = [
    "ReferenceReportAnalyzer",
    "ReferenceReportAnalysis",
    "TopicDiscoveryEngine",
    "DiscoveredCandidate",
    "EvidenceToSectionMapper",
    "SectionEvidencePackage",
    "ReportPlanner",
    "ReportPlan",
    "PlannedSection",
]
