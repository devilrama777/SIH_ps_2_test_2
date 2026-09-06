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


# ---------------------------------------------------------------------------
# Section 14: Cross-Year Comparative Analysis & YoY Table Synthesis
# ---------------------------------------------------------------------------

class StructuralChangeReport(BaseModel):
    """Structural evolution across reporting cycles."""
    prior_period: str
    current_period: str
    retained_sections: List[str] = Field(default_factory=list)
    added_sections: List[str] = Field(default_factory=list)
    removed_sections: List[str] = Field(default_factory=list)
    renamed_sections: List[Dict[str, str]] = Field(default_factory=list)
    structural_similarity_score: float = 100.0


class YoYMetricRow(BaseModel):
    """A single metric comparison between prior and current periods."""
    indicator: str
    unit: str
    prior_value: float
    current_value: float
    absolute_change: float
    percentage_change: float
    trend: str  # 'positive', 'negative', 'neutral'
    provenance_sources: List[str] = Field(default_factory=list)


class YoYComparativeTable(BaseModel):
    """Standardized Coal India Year-over-Year Comparative Table."""
    table_id: str
    title: str
    category: str  # 'operational', 'financial', 'safety_esg'
    prior_period_label: str
    current_period_label: str
    rows: List[YoYMetricRow] = Field(default_factory=list)

    def to_table_dict(self) -> Dict[str, Any]:
        """Converts to standard ReportSection table dictionary representation."""
        headers = [
            "Performance Indicator",
            "Unit",
            self.prior_period_label,
            self.current_period_label,
            "Variance (Abs)",
            "Growth (%)",
        ]
        table_rows = []
        for r in self.rows:
            growth_str = f"{'+' if r.percentage_change > 0 else ''}{r.percentage_change:.2f}%"
            table_rows.append([
                r.indicator,
                r.unit,
                f"{r.prior_value:,.2f}",
                f"{r.current_value:,.2f}",
                f"{'+' if r.absolute_change > 0 else ''}{r.absolute_change:,.2f}",
                growth_str,
            ])
        return {
            "table_id": self.table_id,
            "title": self.title,
            "headers": headers,
            "rows": table_rows,
            "category": self.category,
            "is_yoy_comparative": True,
        }


class ComparativeReportAnalyzer:
    """
    Evaluates prior-year reporting structures against current plans to detect
    organizational shifts, identify recurring reporting patterns, and generate YoY tables.
    """

    METRIC_CATALOG: Dict[str, Dict[str, Any]] = {
        "raw_coal_production": {
            "label": "Raw Coal Production",
            "unit": "Million Tonnes (MT)",
            "higher_is_better": True,
        },
        "coking_coal_production": {
            "label": "Coking Coal Production",
            "unit": "Million Tonnes (MT)",
            "higher_is_better": True,
        },
        "coal_offtake": {
            "label": "Total Coal Off-take / Dispatch",
            "unit": "Million Tonnes (MT)",
            "higher_is_better": True,
        },
        "overburden_removal": {
            "label": "Composite Overburden Removal (OBR)",
            "unit": "M.Cu.M",
            "higher_is_better": True,
        },
        "gross_revenue": {
            "label": "Gross Sales / Revenue from Operations",
            "unit": "INR Crores",
            "higher_is_better": True,
        },
        "net_profit": {
            "label": "Profit After Tax (PAT)",
            "unit": "INR Crores",
            "higher_is_better": True,
        },
        "capex": {
            "label": "Capital Expenditure (Capex)",
            "unit": "INR Crores",
            "higher_is_better": True,
        },
        "csr_expenditure": {
            "label": "Corporate Social Responsibility (CSR) Spend",
            "unit": "INR Crores",
            "higher_is_better": True,
        },
        "fatal_accidents": {
            "label": "Fatal Accidents (Zero Harm Target)",
            "unit": "Incidents",
            "higher_is_better": False,
        },
        "plantation_area": {
            "label": "Afforestation & Mine Reclamation",
            "unit": "Hectares",
            "higher_is_better": True,
        },
    }

    @staticmethod
    def _normalize_title(title: str) -> str:
        t = re.sub(r"^\d+[\.\d]*\s*", "", title).strip().lower()
        return re.sub(r"[^a-z0-9]", "", t)

    @staticmethod
    def _tokens(title: str) -> Set[str]:
        t = re.sub(r"^\d+[\.\d]*\s*", "", title).strip().lower()
        t = t.replace("'s", "")
        return {w for w in re.findall(r"[a-z0-9]{3,}", t)}

    def compare_structures(
        self,
        prior_sections: List[str],
        current_sections: List[str],
        prior_period: str = "Prior Period",
        current_period: str = "Current Period",
    ) -> StructuralChangeReport:
        """Compares section titles across two annual reporting cycles."""
        prior_norm = {self._normalize_title(s): s for s in prior_sections if s.strip()}
        current_norm = {self._normalize_title(s): s for s in current_sections if s.strip()}

        retained: List[str] = []
        renamed: List[Dict[str, str]] = []
        added: List[str] = []
        removed: List[str] = []

        matched_current = set()

        for p_norm, p_orig in prior_norm.items():
            if p_norm in current_norm:
                retained.append(current_norm[p_norm])
                matched_current.add(p_norm)
            else:
                # Check for token overlap / similarity
                p_tokens = self._tokens(p_orig)
                found_match = False
                for c_norm, c_orig in current_norm.items():
                    if c_norm not in matched_current and c_norm not in prior_norm:
                        c_tokens = self._tokens(c_orig)
                        intersection = p_tokens & c_tokens
                        if len(intersection) >= 2 or (len(p_tokens) == 1 and len(intersection) == 1):
                            renamed.append({"prior": p_orig, "current": c_orig})
                            matched_current.add(c_norm)
                            found_match = True
                            break
                        elif p_norm in c_norm or c_norm in p_norm:
                            renamed.append({"prior": p_orig, "current": c_orig})
                            matched_current.add(c_norm)
                            found_match = True
                            break
                if not found_match:
                    removed.append(p_orig)

        for c_norm, c_orig in current_norm.items():
            if c_norm not in matched_current and not any(r["current"] == c_orig for r in renamed):
                added.append(c_orig)

        total_sections = max(1, len(prior_sections) + len(current_sections))
        matched_count = (len(retained) * 2) + (len(renamed) * 2)
        similarity = min(100.0, round((matched_count / total_sections) * 100.0, 1))

        return StructuralChangeReport(
            prior_period=prior_period,
            current_period=current_period,
            retained_sections=retained,
            added_sections=added,
            removed_sections=removed,
            renamed_sections=renamed,
            structural_similarity_score=similarity,
        )


    def generate_yoy_comparative_table(
        self,
        category: str,
        prior_metrics: Dict[str, float],
        current_metrics: Dict[str, float],
        prior_period: str = "FY 2022-23",
        current_period: str = "FY 2023-24",
        source_ref: str = "",
    ) -> YoYComparativeTable:
        """Synthesizes a standardized Year-over-Year comparative table with delta calculations."""
        rows: List[YoYMetricRow] = []
        all_keys = list(prior_metrics.keys()) + [k for k in current_metrics.keys() if k not in prior_metrics]

        table_id = f"yoy_{category.lower().replace(' ', '_')}_{int(re.sub(r'[^0-9]', '', current_period) or 0)}"
        title = f"Year-over-Year Comparative Performance ({prior_period} vs {current_period})"

        for key in all_keys:
            meta = self.METRIC_CATALOG.get(key, {
                "label": key.replace("_", " ").title(),
                "unit": "Units",
                "higher_is_better": True,
            })

            p_val = float(prior_metrics.get(key, 0.0))
            c_val = float(current_metrics.get(key, 0.0))
            abs_change = round(c_val - p_val, 2)

            if p_val > 0:
                pct_change = round((abs_change / p_val) * 100.0, 2)
            else:
                pct_change = 100.0 if c_val > 0 else 0.0

            if abs_change == 0:
                trend = "neutral"
            elif (abs_change > 0 and meta["higher_is_better"]) or (abs_change < 0 and not meta["higher_is_better"]):
                trend = "positive"
            else:
                trend = "negative"

            rows.append(
                YoYMetricRow(
                    indicator=meta["label"],
                    unit=meta["unit"],
                    prior_value=p_val,
                    current_value=c_val,
                    absolute_change=abs_change,
                    percentage_change=pct_change,
                    trend=trend,
                    provenance_sources=[source_ref] if source_ref else [],
                )
            )

        return YoYComparativeTable(
            table_id=table_id,
            title=title,
            category=category,
            prior_period_label=prior_period,
            current_period_label=current_period,
            rows=rows,
        )

