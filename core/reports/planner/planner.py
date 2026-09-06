"""
Report Planner Orchestrator — Sections 13, 14, 15 of Master Implementation Specification.

Synthesizes previous-report analysis, dynamic topic discovery from current-year evidence,
and evidence-to-section mapping to formulate a comprehensive, verified Report Plan.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.domain.documents import CanonicalDocument
from core.domain.reports import Report, ReportSection, SectionType, ValidationStatus
from core.reports.planner.evidence_mapper import EvidenceToSectionMapper, SectionEvidencePackage
from core.reports.planner.reference_analyzer import ReferenceReportAnalysis, ReferenceReportAnalyzer
from core.reports.planner.topic_discovery import DiscoveredCandidate, TopicDiscoveryEngine


class PlannedSection(BaseModel):
    """A section node in the structured report plan hierarchy."""
    section_id: str
    title: str
    level: int = 1
    type: SectionType = SectionType.MANDATORY
    discovery_reason: Optional[str] = None
    subsections: List[PlannedSection] = Field(default_factory=list)
    evidence_package: Optional[SectionEvidencePackage] = None


class ReportPlan(BaseModel):
    """The master plan formulating the target report's dynamic hierarchy."""
    plan_id: str
    report_title: str
    reporting_period: str
    subsidiary_name: str = "Coal India Limited Subsidiary"
    template_name: str = "modern"
    reference_analysis: Optional[ReferenceReportAnalysis] = None
    discovered_topics: List[DiscoveredCandidate] = Field(default_factory=list)
    sections: List[PlannedSection] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_planned_sections: int = 0
    sufficient_sections_count: int = 0

    def to_report_skeleton(self) -> Report:
        """Converts the planned hierarchy into a domain Report instance."""
        def convert_section(p_sec: PlannedSection) -> ReportSection:
            sources = []
            if p_sec.evidence_package:
                sources = list({ev.document_id for ev in p_sec.evidence_package.ranked_evidence})

            return ReportSection(
                section_id=p_sec.section_id,
                title=p_sec.title,
                level=p_sec.level,
                type=p_sec.type,
                discovery_reason=p_sec.discovery_reason,
                narrative_blocks=[],
                tables=[],
                charts=[],
                images=[],
                links=[],
                source_refs=sources,
                validation_status=ValidationStatus.UNVALIDATED,
                subsections=[convert_section(sub) for sub in p_sec.subsections],
                metadata={"sufficiency_score": p_sec.evidence_package.sufficiency_score if p_sec.evidence_package else 0.0},
            )

        report_sections = [convert_section(s) for s in self.sections]
        return Report(
            report_id=self.plan_id,
            title=self.report_title,
            reporting_period=self.reporting_period,
            subsidiary_name=self.subsidiary_name,
            template_name=self.template_name,
            sections=report_sections,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
            version=1,
            metadata={"planned_sections_count": self.total_planned_sections},
        )


# Standard mandatory corporate baseline sections for CIL subsidiaries
CIL_MANDATORY_BASELINE = [
    {
        "title": "Corporate Overview & Subsidiary Mandate",
        "level": 1,
        "type": SectionType.MANDATORY,
        "subsections": [
            {"title": "Subsidiary Profile & Vision", "level": 2, "type": SectionType.MANDATORY},
            {"title": "Board of Directors & Leadership Structure", "level": 2, "type": SectionType.MANDATORY},
        ],
    },
    {
        "title": "Chairman's Statement & Executive Review",
        "level": 1,
        "type": SectionType.MANDATORY,
        "subsections": [],
    },
    {
        "title": "Operational Performance & Mining Operations",
        "level": 1,
        "type": SectionType.MANDATORY,
        "subsections": [
            {"title": "Raw Coal Production & Overburden Removal", "level": 2, "type": SectionType.MANDATORY},
            {"title": "Coal Offtake, Evacuation & Dispatch Logistics", "level": 2, "type": SectionType.MANDATORY},
            {"title": "Heavy Earth Moving Machinery (HEMM) Productivity", "level": 2, "type": SectionType.RECURRING},
        ],
    },
    {
        "title": "Financial Highlights & Audited Accounts Review",
        "level": 1,
        "type": SectionType.MANDATORY,
        "subsections": [
            {"title": "Turnover, Profitability & Dividend Declaration", "level": 2, "type": SectionType.MANDATORY},
            {"title": "Capital Expenditure (Capex) Execution", "level": 2, "type": SectionType.MANDATORY},
        ],
    },
    {
        "title": "Safety, Occupational Health & Disaster Management",
        "level": 1,
        "type": SectionType.MANDATORY,
        "subsections": [
            {"title": "Zero Harm Initiatives & DGMS Compliance", "level": 2, "type": SectionType.MANDATORY},
        ],
    },
    {
        "title": "Environmental Management & Sustainable Mining",
        "level": 1,
        "type": SectionType.MANDATORY,
        "subsections": [
            {"title": "Bio-Reclamation & Tree Plantation Metrics", "level": 2, "type": SectionType.MANDATORY},
        ],
    },
    {
        "title": "Corporate Social Responsibility (CSR) & Community Development",
        "level": 1,
        "type": SectionType.MANDATORY,
        "subsections": [
            {"title": "Healthcare, Education & Rural Infrastructure Projects", "level": 2, "type": SectionType.MANDATORY},
        ],
    },
    {
        "title": "Corporate Governance & Statutory Disclosures",
        "level": 1,
        "type": SectionType.MANDATORY,
        "subsections": [
            {"title": "Board Committee Reports & Secretarial Compliance", "level": 2, "type": SectionType.MANDATORY},
        ],
    },
    {
        "title": "Independent Auditors' Report & Financial Statements",
        "level": 1,
        "type": SectionType.MANDATORY,
        "subsections": [
            {"title": "Audited Balance Sheet & Profit and Loss Statement", "level": 2, "type": SectionType.MANDATORY},
            {"title": "Comments of the Comptroller & Auditor General (C&AG) of India", "level": 2, "type": SectionType.MANDATORY},
        ],
    },
]


class ReportPlanner:
    """
    Constructs a dynamic report hierarchy by fusing reference report analysis,
    current evidence discovery, and section-by-section evidence packaging.
    """

    def __init__(
        self,
        reference_analyzer: Optional[ReferenceReportAnalyzer] = None,
        topic_discovery: Optional[TopicDiscoveryEngine] = None,
        evidence_mapper: Optional[EvidenceToSectionMapper] = None,
    ):
        self.reference_analyzer = reference_analyzer or ReferenceReportAnalyzer()
        self.topic_discovery = topic_discovery or TopicDiscoveryEngine()
        self.evidence_mapper = evidence_mapper or EvidenceToSectionMapper()

    def generate_plan(
        self,
        current_evidence_corpus: List[Dict[str, Any]],
        reference_document: Optional[CanonicalDocument] = None,
        report_title: str = "Annual Performance & Accountability Report",
        reporting_period: str = "FY 2024-25",
        subsidiary_name: str = "Coal India Limited Subsidiary",
        template_name: str = "modern",
        attach_evidence: bool = True,
    ) -> ReportPlan:
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"

        # 1. Analyze previous report reference if provided
        ref_analysis: Optional[ReferenceReportAnalysis] = None
        ref_topics: List[str] = []
        if reference_document:
            ref_analysis = self.reference_analyzer.analyze(reference_document)
            ref_topics = ref_analysis.recurring_topics

        # 2. Discover emerging topics in current-period evidence
        discovered = self.topic_discovery.discover_topics(
            evidence_corpus=current_evidence_corpus,
            reference_topics=ref_topics,
        )

        # 3. Build section hierarchy starting from corporate baseline
        sections: List[PlannedSection] = []
        sec_idx = 1

        for base in CIL_MANDATORY_BASELINE:
            sec_id = f"sec_{sec_idx:02d}"
            subsections: List[PlannedSection] = []

            for sub_idx, sub in enumerate(base["subsections"], 1):
                sub_id = f"{sec_id}_{sub_idx:02d}"
                sub_pkg = (
                    self.evidence_mapper.map_evidence_for_section(
                        section_id=sub_id,
                        section_title=sub["title"],
                        financial_year=reporting_period,
                    )
                    if attach_evidence
                    else None
                )

                subsections.append(
                    PlannedSection(
                        section_id=sub_id,
                        title=sub["title"],
                        level=sub["level"],
                        type=sub["type"],
                        evidence_package=sub_pkg,
                    )
                )

            pkg = (
                self.evidence_mapper.map_evidence_for_section(
                    section_id=sec_id,
                    section_title=base["title"],
                    financial_year=reporting_period,
                )
                if attach_evidence
                else None
            )

            sections.append(
                PlannedSection(
                    section_id=sec_id,
                    title=base["title"],
                    level=base["level"],
                    type=base["type"],
                    subsections=subsections,
                    evidence_package=pkg,
                )
            )
            sec_idx += 1

        # 4. Integrate dynamically discovered sections & new top-level sections
        for cand in discovered:
            sec_id = f"sec_disc_{sec_idx:02d}"
            disc_pkg = (
                self.evidence_mapper.map_evidence_for_section(
                    section_id=sec_id,
                    section_title=cand.title,
                    additional_keywords=cand.matched_keywords,
                    financial_year=reporting_period,
                )
                if attach_evidence
                else None
            )

            if cand.level == 1 or cand.section_type == SectionType.NEW_TOP_LEVEL:
                # Insert as top-level chapter before governance/statutory accounts
                insert_pos = max(len(sections) - 2, 1)
                sections.insert(
                    insert_pos,
                    PlannedSection(
                        section_id=sec_id,
                        title=cand.title,
                        level=1,
                        type=cand.section_type,
                        discovery_reason=cand.discovery_reason,
                        subsections=[],
                        evidence_package=disc_pkg,
                    ),
                )
            else:
                # Add as subsection to Operations or Sustainability
                target_sec = sections[2] if len(sections) > 2 else sections[0]
                target_sec.subsections.append(
                    PlannedSection(
                        section_id=sec_id,
                        title=cand.title,
                        level=2,
                        type=cand.section_type,
                        discovery_reason=cand.discovery_reason,
                        evidence_package=disc_pkg,
                    )
                )
            sec_idx += 1

        # Count total and sufficient sections
        total_count = 0
        sufficient_count = 0

        def count_nodes(nodes: List[PlannedSection]):
            nonlocal total_count, sufficient_count
            for n in nodes:
                total_count += 1
                if n.evidence_package and n.evidence_package.is_sufficient:
                    sufficient_count += 1
                count_nodes(n.subsections)

        count_nodes(sections)

        return ReportPlan(
            plan_id=plan_id,
            report_title=report_title,
            reporting_period=reporting_period,
            subsidiary_name=subsidiary_name,
            template_name=template_name,
            reference_analysis=ref_analysis,
            discovered_topics=discovered,
            sections=sections,
            total_planned_sections=total_count,
            sufficient_sections_count=sufficient_count,
        )
