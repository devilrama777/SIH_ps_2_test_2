"""
Evidence-to-Section Mapper — Section 13 & 15 of Master Implementation Specification.

Associates each planned report section with an explicit, verified evidence package
comprising text blocks, spreadsheet coordinates, tables, and images with provenance IDs.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.domain.evidence import SpreadsheetCoordinate
from core.retrieval.search import HybridSearchEngine, RankedEvidence, SearchQuery


class SectionEvidencePackage(BaseModel):
    """The isolated evidence set allocated to a specific report section."""
    section_id: str
    section_title: str
    ranked_evidence: List[RankedEvidence] = Field(default_factory=list)
    spreadsheet_coordinates: List[SpreadsheetCoordinate] = Field(default_factory=list)
    table_items: List[Dict[str, Any]] = Field(default_factory=list)
    image_items: List[Dict[str, Any]] = Field(default_factory=list)
    sufficiency_score: float = 0.0
    is_sufficient: bool = False
    sufficiency_notes: Optional[str] = None


# Thematic search keywords to seed section evidence queries
SECTION_QUERY_KEYWORDS = {
    "profile": "corporate overview subsidiary mandate vision board directors shareholding",
    "production": "raw coal production overburden removal dragline heavy earth moving machinery shovel dumper",
    "dispatch": "coal dispatch offtake rail siding mgr road supply power plants consumers",
    "financial": "financial performance revenue profit before tax capex ebitda turnover balance sheet",
    "safety": "mine safety rescue station fatal accident rate dgms audit inspection zero harm",
    "environment": "environmental compliance tree plantation mine water discharge solar power reclamation",
    "csr": "corporate social responsibility welfare expenditure education healthcare drinking water rural development",
    "governance": "corporate governance audit committee board meetings vigil mechanism secretarial audit",
    "digital": "digital mine sap erp telemetry automation drone survey fleet management system",
    "fmc": "first mile connectivity rapid loading system conveyor rail evacuation eco-friendly dispatch",
    "solar": "solar power plant ground mounted rooftop renewable energy capacity net zero",
}


class EvidenceToSectionMapper:
    """
    Queries the hybrid retrieval engine and SQLite relational index
    to package evidence for each planned report section.
    """

    def __init__(self, search_engine: Optional[HybridSearchEngine] = None):
        self.search_engine = search_engine or HybridSearchEngine()

    def map_evidence_for_section(
        self,
        section_id: str,
        section_title: str,
        additional_keywords: Optional[List[str]] = None,
        financial_year: Optional[str] = None,
        limit: int = 15,
    ) -> SectionEvidencePackage:
        # Construct focused search query
        query_terms = self._build_query_terms(section_title, additional_keywords)

        search_query = SearchQuery(
            query_text=query_terms,
            financial_year=financial_year,
            limit=limit,
        )

        try:
            results = self.search_engine.search(search_query)
        except Exception:
            results = []

        spreadsheet_coords: List[SpreadsheetCoordinate] = []
        table_items: List[Dict[str, Any]] = []
        image_items: List[Dict[str, Any]] = []

        for item in results:
            if item.spreadsheet_coord:
                spreadsheet_coords.append(item.spreadsheet_coord)
            if item.element_type == "table":
                table_items.append({
                    "element_id": item.element_id,
                    "document_id": item.document_id,
                    "page_number": item.page_number,
                    "content": item.text,
                })
            elif item.element_type == "image":
                image_items.append({
                    "element_id": item.element_id,
                    "document_id": item.document_id,
                    "page_number": item.page_number,
                    "content": item.text,
                })

        # Calculate sufficiency
        # Sections need at least 1-2 relevant evidence items to be writable
        evidence_count = len(results)
        if evidence_count >= 5:
            sufficiency = 1.0
            notes = "Robust evidence package available."
        elif evidence_count >= 1:
            sufficiency = round(evidence_count / 5.0, 2)
            notes = "Moderate evidence available; some topics may require supplementary filing data."
        else:
            sufficiency = 0.0
            notes = "Insufficient evidence found in current corpus. Review data sources."

        return SectionEvidencePackage(
            section_id=section_id,
            section_title=section_title,
            ranked_evidence=results,
            spreadsheet_coordinates=spreadsheet_coords,
            table_items=table_items,
            image_items=image_items,
            sufficiency_score=sufficiency,
            is_sufficient=sufficiency >= 0.2,
            sufficiency_notes=notes,
        )

    def _build_query_terms(self, title: str, additional_keywords: Optional[List[str]] = None) -> str:
        title_lower = title.lower()
        terms = [title]

        for key, query_str in SECTION_QUERY_KEYWORDS.items():
            if key in title_lower:
                terms.append(query_str)

        if additional_keywords:
            terms.extend(additional_keywords)

        return " ".join(terms)[:250]
