"""
Advanced Temporal Query & Timeline Indexing Engine.
Section 5 and Section 11 of Master Implementation Specification.

Parses natural language and structured temporal expressions (e.g., 'March 2025', 'FY 2023-24 Q3',
'2022 to 2024') to filter and rank evidence chronologically from the SQLite FTS5 index.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.ingestion.temporal import extract_temporal_metadata, TemporalMetadata
from core.retrieval.db import ReportDatabase
from core.retrieval.search import HybridSearchEngine, RankedEvidence, SearchQuery


class TemporalQueryFilter(BaseModel):
    """Normalized structured temporal criteria parsed from a user query."""
    raw_query: str
    cleaned_text_query: str
    target_fy: Optional[str] = None
    target_quarter: Optional[str] = None
    target_month: Optional[str] = None
    target_year: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class TimelineCluster(BaseModel):
    """Cluster of evidence grouped by chronological period."""
    period_label: str
    financial_year: Optional[str] = None
    quarter: Optional[str] = None
    month: Optional[str] = None
    evidence_count: int
    items: List[RankedEvidence] = Field(default_factory=list)


class TemporalQueryResult(BaseModel):
    """Results of a temporal query execution."""
    query: str
    filter_criteria: TemporalQueryFilter
    total_matched: int
    chronological_timeline: List[TimelineCluster] = Field(default_factory=list)
    flat_results: List[RankedEvidence] = Field(default_factory=list)


class TemporalQueryEngine:
    """
    Evaluates temporal queries across indexed canonical documents and evidence blocks.
    """

    def __init__(self, search_engine: Optional[HybridSearchEngine] = None, db: Optional[ReportDatabase] = None) -> None:
        self.db = db or ReportDatabase()
        self.search_engine = search_engine or HybridSearchEngine(db=self.db)

    def parse_temporal_query(self, query: str) -> TemporalQueryFilter:
        """
        Parses natural language temporal expressions out of a query.
        Example: 'Find all March 2025 operational performance information'
        -> cleaned: 'operational performance information', month: 'March', year: 2025
        """
        extracted = extract_temporal_metadata(query)
        cleaned = query

        # Extract 4-digit year if present
        target_year: Optional[int] = None
        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", query)
        if year_match:
            target_year = int(year_match.group(1))

        # Strip common query phrases
        cleaned = re.sub(r"(?i)\b(find|show|retrieve|all|evidence|information|data|relevant to|for|in|during)\b", "", cleaned)

        # Strip temporal words if captured
        if extracted.reporting_month:
            cleaned = re.sub(rf"(?i)\b{extracted.reporting_month}\b", "", cleaned)
        if extracted.reporting_quarter:
            cleaned = re.sub(rf"(?i)\b{extracted.reporting_quarter}\b", "", cleaned)
        if extracted.financial_year:
            cleaned = re.sub(rf"(?i)\b{re.escape(extracted.financial_year)}\b", "", cleaned)
            cleaned = re.sub(r"(?i)\bfy\b", "", cleaned)
        if target_year:
            cleaned = re.sub(rf"\b{target_year}\b", "", cleaned)

        cleaned = " ".join(cleaned.split()).strip()

        return TemporalQueryFilter(
            raw_query=query,
            cleaned_text_query=cleaned or query,
            target_fy=extracted.financial_year,
            target_quarter=extracted.reporting_quarter,
            target_month=extracted.reporting_month,
            target_year=target_year,
            date_from=None,
            date_to=None,
        )

    def search_temporal(
        self,
        query: str,
        limit: int = 20,
    ) -> TemporalQueryResult:
        """
        Executes a temporal-first search, clustering results into chronological periods.
        """
        criteria = self.parse_temporal_query(query)

        # 1. Execute lexical search with SearchQuery
        sq = SearchQuery(
            query_text=criteria.cleaned_text_query,
            financial_year=criteria.target_fy,
            reporting_period=criteria.target_month,
            limit=limit * 2,
        )
        base_results = self.search_engine.search(sq)

        matched: List[RankedEvidence] = []

        # 2. Filter / score boost based on temporal alignment
        for res in base_results:
            text_lower = res.text.lower()
            metadata_str = str(res.metadata).lower()

            is_match = True

            # Match FY if specified
            if criteria.target_fy:
                fy_clean = criteria.target_fy.lower().replace(" ", "").replace("-", "")
                if fy_clean not in text_lower.replace(" ", "").replace("-", "") and fy_clean not in metadata_str.replace(" ", "").replace("-", ""):
                    is_match = False

            # Match Month if specified
            if criteria.target_month and is_match:
                if criteria.target_month.lower() not in text_lower and criteria.target_month.lower() not in metadata_str:
                    is_match = False

            # Match Quarter if specified
            if criteria.target_quarter and is_match:
                if criteria.target_quarter.lower() not in text_lower and criteria.target_quarter.lower() not in metadata_str:
                    is_match = False

            if is_match:
                matched.append(res)

        # Fallback to base results if strict filter yields 0 matches
        if not matched and base_results:
            matched = base_results[:limit]

        # 3. Cluster into chronological timeline
        timeline_dict: Dict[str, List[RankedEvidence]] = {}
        for r in matched[:limit]:
            # Derive cluster label
            label = "General Period"
            meta = r.metadata or {}
            if meta.get("financial_year"):
                label = f"{meta['financial_year']}"
                if meta.get("reporting_period"):
                    label += f" ({meta['reporting_period']})"
            elif criteria.target_fy or criteria.target_month:
                parts = [p for p in [criteria.target_month, criteria.target_fy] if p]
                label = " ".join(parts)

            if label not in timeline_dict:
                timeline_dict[label] = []
            timeline_dict[label].append(r)

        clusters = [
            TimelineCluster(
                period_label=lbl,
                evidence_count=len(items),
                items=items,
            )
            for lbl, items in timeline_dict.items()
        ]

        return TemporalQueryResult(
            query=query,
            filter_criteria=criteria,
            total_matched=len(matched[:limit]),
            chronological_timeline=clusters,
            flat_results=matched[:limit],
        )
