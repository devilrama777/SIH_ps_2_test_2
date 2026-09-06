"""
Unit tests for TopicDiscoveryEngine (Section 13).
"""
from core.domain.reports import SectionType
from core.reports.planner.topic_discovery import TopicDiscoveryEngine


def test_topic_discovery_emergent_topics():
    engine = TopicDiscoveryEngine()

    evidence_corpus = [
        {
            "id": "item_1",
            "text": "The subsidiary completed SAP ERP rollout and deployed drone survey fleet for digital mine telemetry.",
        },
        {
            "id": "item_2",
            "text": "Commissioned 50 MW ground mounted solar power plant advancing towards net zero carbon footprint.",
        },
        {
            "id": "item_3",
            "text": "Rapid loading system and first mile connectivity (FMC) conveyor commissioned at Piparwar.",
        },
    ]

    candidates = engine.discover_topics(evidence_corpus=evidence_corpus, reference_topics=["Operations", "Finance"])

    assert len(candidates) >= 3

    titles = [c.title for c in candidates]
    assert any("Digital Mine Transformation" in t for t in titles)
    assert any("Renewable Energy Transition" in t for t in titles)
    assert any("First Mile Connectivity" in t for t in titles)

    digital_candidate = next(c for c in candidates if "Digital Mine" in c.title)
    assert digital_candidate.section_type == SectionType.NEW_TOP_LEVEL
    assert digital_candidate.discovery_reason is not None
    assert len(digital_candidate.matched_keywords) >= 2


def test_topic_discovery_recurring_override():
    engine = TopicDiscoveryEngine()

    evidence_corpus = [
        {
            "id": "item_1",
            "text": "50 MW solar power plant installed on reclaimed land.",
        }
    ]

    # If reference report already featured Renewable Energy, candidate marks as recurring
    candidates = engine.discover_topics(
        evidence_corpus=evidence_corpus,
        reference_topics=["Renewable Energy Transition & Solar Park Expansion"],
    )

    solar_cand = next(c for c in candidates if "Solar" in c.title)
    assert solar_cand.section_type == SectionType.RECURRING
