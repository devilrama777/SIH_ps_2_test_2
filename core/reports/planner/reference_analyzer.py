"""
Reference Report Analyzer — Section 14 of Master Implementation Specification.

Extracts structural hierarchy, recurring topics, table patterns, and layout conventions
from previous CIL annual reports to guide generation of new reports without cloning content.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.domain.documents import CanonicalDocument, DocumentElement, ElementType


class ReferenceSectionSummary(BaseModel):
    title: str
    level: int
    element_count: int
    table_count: int
    image_count: int
    topics: List[str] = Field(default_factory=list)


class ReferenceReportAnalysis(BaseModel):
    source_document_id: str
    source_filename: str
    total_pages: int
    total_elements: int
    extracted_outline: List[ReferenceSectionSummary] = Field(default_factory=list)
    recurring_topics: List[str] = Field(default_factory=list)
    table_patterns: Dict[str, Any] = Field(default_factory=dict)
    image_patterns: Dict[str, Any] = Field(default_factory=dict)
    layout_conventions: Dict[str, Any] = Field(default_factory=dict)


# Standard recurring annual report themes in CIL subsidiaries
CIL_STANDARD_THEMES = {
    "Corporate Profile & Mandate": ["profile", "vision", "mission", "about us", "board of directors", "subsidiary profile"],
    "Chairman & Leadership Statement": ["chairman", "cmd's address", "message from chairman", "managing director"],
    "Operational & Production Performance": ["production", "overburden", "off-take", "dispatch", "coal washery", "productivity", "fmc", "first mile", "operational"],
    "Financial Performance & Highlights": ["financial highlights", "financial", "financials", "finance", "revenue", "profit", "capex", "turnover", "balance sheet", "audited accounts"],
    "Mine Safety & Disaster Management": ["safety", "rescue", "accident rate", "dgms", "zero harm", "safety audit"],
    "Environmental Management & Sustainability": ["environment", "plantation", "reclamation", "solar", "mine water", "sustainability", "fly ash"],
    "Corporate Social Responsibility (CSR)": ["csr", "welfare", "community", "education", "healthcare", "sanitation", "rural development"],
    "Corporate Governance": ["governance", "board committees", "compliance", "vigilance", "risk management", "secretarial audit"],
    "Independent Auditors' Report & Financial Statements": ["auditor's report", "c&ag", "standalone balance sheet", "profit and loss", "notes to accounts"],
}


class ReferenceReportAnalyzer:
    """
    Analyzes previous-year reference reports to discover organizational reporting conventions,
    structural hierarchy, and recurring thematic sections.
    """

    def analyze(self, doc: CanonicalDocument) -> ReferenceReportAnalysis:
        outline: List[ReferenceSectionSummary] = []
        identified_topics = set()
        table_count = 0
        image_count = 0
        text_count = 0

        current_section: Optional[ReferenceSectionSummary] = None

        # Extract elements from doc.pages
        all_elements: List[DocumentElement] = []
        if doc.pages:
            for p in doc.pages:
                all_elements.extend(p.elements)
        elif hasattr(doc, "elements"):
            all_elements = getattr(doc, "elements", [])

        # Sort elements by page and reading order
        sorted_elements = sorted(all_elements, key=lambda e: (e.page_number or 1, e.reading_order or 1))

        for elem in sorted_elements:
            elem_text = elem.text or ""
            if elem.type == ElementType.HEADING:
                level = elem.metadata.get("heading_level", 1) if elem.metadata else 1
                title = elem_text.strip()

                if len(title) > 2:
                    matched_topics = self._detect_topics(title)
                    identified_topics.update(matched_topics)

                    sec = ReferenceSectionSummary(
                        title=title,
                        level=level,
                        element_count=1,
                        table_count=0,
                        image_count=0,
                        topics=matched_topics,
                    )
                    outline.append(sec)
                    current_section = sec

            elif elem.type == ElementType.TABLE:
                table_count += 1
                if current_section:
                    current_section.table_count += 1
                    current_section.element_count += 1

            elif elem.type == ElementType.IMAGE:
                image_count += 1
                if current_section:
                    current_section.image_count += 1
                    current_section.element_count += 1

            elif elem.type == ElementType.PARAGRAPH or elem.type == ElementType.OTHER:
                text_count += 1
                matched_topics = self._detect_topics(elem_text)
                identified_topics.update(matched_topics)
                if current_section:
                    current_section.element_count += 1
                    current_section.topics.extend([t for t in matched_topics if t not in current_section.topics])

        # If outline is empty, infer sections from recurring themes
        if not outline:
            outline = self._infer_default_outline(identified_topics)

        total_pages = len(doc.pages) if doc.pages else 1

        return ReferenceReportAnalysis(
            source_document_id=doc.document_id,
            source_filename=doc.source_reference,
            total_pages=total_pages,
            total_elements=len(all_elements),
            extracted_outline=outline,
            recurring_topics=sorted(list(identified_topics)),
            table_patterns={
                "total_tables_extracted": table_count,
                "tables_per_page_avg": round(table_count / max(total_pages, 1), 2),
            },
            image_patterns={
                "total_images_extracted": image_count,
                "images_per_page_avg": round(image_count / max(total_pages, 1), 2),
            },
            layout_conventions={
                "has_structured_headings": any(e.type == ElementType.HEADING for e in all_elements),
                "total_text_blocks": text_count,
                "reporting_period": doc.reporting_period or doc.reporting_year,
            },
        )

    def _detect_topics(self, text: str) -> List[str]:
        text_lower = text.lower()
        matched = []
        for theme_name, keywords in CIL_STANDARD_THEMES.items():
            if any(re.search(rf"\b{re.escape(k)}\b", text_lower) for k in keywords):
                matched.append(theme_name)
        return matched

    def _infer_default_outline(self, identified_topics: set) -> List[ReferenceSectionSummary]:
        themes = identified_topics or set(CIL_STANDARD_THEMES.keys())
        inferred = []
        for idx, theme in enumerate(sorted(list(themes)), 1):
            inferred.append(
                ReferenceSectionSummary(
                    title=theme,
                    level=1,
                    element_count=5,
                    table_count=1,
                    image_count=1,
                    topics=[theme],
                )
            )
        return inferred
