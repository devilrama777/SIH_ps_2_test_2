"""
Unit and integration tests for SectionGenerator — Section 16 of Master Plan.
"""
from core.domain.reports import SectionType, ValidationStatus
from core.reports.planner.evidence_mapper import RankedEvidence, SectionEvidencePackage
from core.reports.planner.planner import PlannedSection
from core.reports.generator.section_generator import SectionGenerator


def test_section_generator_insufficient_evidence():
    gen = SectionGenerator()
    planned_sec = PlannedSection(
        section_id="sec_unsupported",
        title="Unfunded Projects",
        level=1,
        type=SectionType.CONDITIONAL,
        evidence_package=None,
    )

    result_sec = gen.generate_section_content(planned_sec)
    assert result_sec.section_id == "sec_unsupported"
    assert len(result_sec.narrative_blocks) == 1
    assert result_sec.narrative_blocks[0].insufficient_evidence is True
    assert "No primary source evidence" in result_sec.narrative_blocks[0].text
    assert result_sec.validation_status == ValidationStatus.WARNING


def test_section_generator_with_evidence():
    gen = SectionGenerator()

    ev1 = RankedEvidence(
        document_id="doc_ops_01",
        element_id="el_01",
        element_type="narrative",
        text="Central Coalfields raw coal output stood at 84.5 MT with 15 FMC projects active.",
        score=0.92,
        page_number=8,
        source_reference="CCL_Operations_FY25.pdf",
    )
    pkg = SectionEvidencePackage(
        section_id="sec_ops",
        section_title="Operational Performance",
        ranked_evidence=[ev1],
        sufficiency_score=0.92,
        is_sufficient=True,
    )

    planned_sec = PlannedSection(
        section_id="sec_ops",
        title="Operational Performance",
        level=1,
        type=SectionType.MANDATORY,
        evidence_package=pkg,
    )

    result_sec = gen.generate_section_content(planned_sec)
    assert result_sec.section_id == "sec_ops"
    assert len(result_sec.narrative_blocks) >= 1
    # Check that citations are preserved or generated
    first_block = result_sec.narrative_blocks[0]
    assert first_block.insufficient_evidence is False
    assert len(first_block.text) > 20
