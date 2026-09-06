"""
Dynamic Topic Discovery & Section Classification Engine — Section 13 of Master Implementation Plan.

Identifies newly emerging organizational initiatives in current-period evidence,
classifying planned report sections as mandatory, recurring, optional, conditional,
or newly discovered top-level sections.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.domain.reports import SectionType


class DiscoveredCandidate(BaseModel):
    title: str
    section_type: SectionType
    level: int = 1
    discovery_reason: Optional[str] = None
    matched_keywords: List[str] = Field(default_factory=list)
    evidence_item_count: int = 0
    sample_snippets: List[str] = Field(default_factory=list)


# Emergent thematic clusters in CIL current-period evidence
EMERGENT_TOPIC_RULES = [
    {
        "title": "Digital Mine Transformation & Operator Automation",
        "keywords": ["digital mine", "drone survey", "telemetry", "sap erp", "automation", "fleet management", "iot sensors"],
        "level": 1,
        "type": SectionType.NEW_TOP_LEVEL,
        "reason": "Current-period evidence contains substantial technological transformation data absent from standard recurring chapters.",
    },
    {
        "title": "First Mile Connectivity (FMC) & Rapid Loading Infrastructure",
        "keywords": ["first mile connectivity", "fmc", "silo loading", "conveyor", "rail connectivity", "rapid loading"],
        "level": 2,
        "type": SectionType.DISCOVERED,
        "reason": "High-volume capital expenditure and project completion records for eco-friendly coal dispatch discovered in current period.",
    },
    {
        "title": "Renewable Energy Transition & Solar Park Expansion",
        "keywords": ["solar power", "ground mounted solar", "rooftop solar", "renewable energy", "net zero", "carbon footprint"],
        "level": 1,
        "type": SectionType.NEW_TOP_LEVEL,
        "reason": "Dedicated renewable installations and green energy diversification reported across multiple subsidiary sites.",
    },
    {
        "title": "Mission Coking Coal & High-Capacity Washery Modernization",
        "keywords": ["coking coal", "washery modernization", "import substitution", "heavy media cyclone", "beneficiation yield"],
        "level": 2,
        "type": SectionType.DISCOVERED,
        "reason": "Significant capacity expansion and import substitution initiatives discovered in operational evidence.",
    },
    {
        "title": "Mine Water Utilization & Community Potable Water Supply",
        "keywords": ["mine water discharge", "potable water", "irrigation water", "groundwater recharge", "water treatment"],
        "level": 2,
        "type": SectionType.CONDITIONAL,
        "reason": "Triggered when community mine water treatment exceeds environmental compliance reporting thresholds.",
    },
]


class TopicDiscoveryEngine:
    """
    Scans evidence text and metadata from the current reporting period
    to discover novel report sections and classify structural hierarchy.
    """

    def discover_topics(
        self,
        evidence_corpus: List[Dict[str, Any]],
        reference_topics: Optional[List[str]] = None,
    ) -> List[DiscoveredCandidate]:
        candidates: List[DiscoveredCandidate] = []
        ref_topics_lower = [t.lower() for t in (reference_topics or [])]

        for rule in EMERGENT_TOPIC_RULES:
            matched_items: List[Dict[str, Any]] = []
            found_keywords = set()

            for item in evidence_corpus:
                text = item.get("text", "") or item.get("content", "")
                text_lower = text.lower()

                matches = [k for k in rule["keywords"] if re.search(rf"\b{re.escape(k)}\b", text_lower)]
                if matches:
                    matched_items.append(item)
                    found_keywords.update(matches)

            # If evidence matches threshold (at least 1 matching evidence item with keywords)
            if matched_items:
                # Check if this topic was already prominent in the reference report
                rule_title_lower = rule["title"].lower()
                is_in_reference = any(ref in rule_title_lower or rule_title_lower in ref for ref in ref_topics_lower)

                candidate_type = rule["type"]
                # If it was already in reference, it is RECURRING rather than NEW_TOP_LEVEL
                if is_in_reference and candidate_type == SectionType.NEW_TOP_LEVEL:
                    candidate_type = SectionType.RECURRING

                snippets = [it.get("text", "")[:120] for it in matched_items[:3]]

                candidates.append(
                    DiscoveredCandidate(
                        title=rule["title"],
                        section_type=candidate_type,
                        level=rule["level"],
                        discovery_reason=rule["reason"],
                        matched_keywords=sorted(list(found_keywords)),
                        evidence_item_count=len(matched_items),
                        sample_snippets=snippets,
                    )
                )

        return candidates
