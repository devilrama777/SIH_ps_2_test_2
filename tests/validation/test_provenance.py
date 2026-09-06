"""
Tests for ProvenanceValidator — Section 17 coordinate-level evidence validation.
"""
from core.domain.evidence import EvidenceReference, ProvenanceRecord, SpreadsheetCoordinate
from core.domain.reports import NarrativeBlock
from core.validation.provenance import ProvenanceValidator


def test_unsubstantiated_numerical_claim():
    validator = ProvenanceValidator()
    # Narrative block contains numerical claims but zero citations or evidence refs
    block = NarrativeBlock(
        block_id="nb_01",
        text="Total overburden removal achieved a record 125.4 MT during the fiscal year.",
        evidence_refs=[],
        confidence=0.9,
    )
    issues = validator.validate_narrative_block("sec_ops", block)
    errs = [i for i in issues if "Unsubstantiated numerical claim" in i.message]
    assert len(errs) == 1
    assert errs[0].severity == "error"


def test_substantiated_claim_passes():
    validator = ProvenanceValidator()
    # Narrative block contains citation
    ref = EvidenceReference(
        evidence_id="ref_01",
        provenance=ProvenanceRecord(
            provenance_id="prov_01",
            document_id="doc_2024",
            source_reference="Annual_Report_2024.pdf",
            page_number=14,
        ),
        excerpt_text="Total coal production: 125.4 MT",
        confidence_score=0.95,
    )
    block = NarrativeBlock(
        block_id="nb_02",
        text="Total overburden removal achieved a record 125.4 MT [DOC:Annual_Report_2024.pdf:P14].",
        evidence_refs=[ref],
        confidence=0.95,
    )
    issues = validator.validate_narrative_block("sec_ops", block)
    errs = [i for i in issues if "Unsubstantiated numerical claim" in i.message]
    assert len(errs) == 0


def test_insufficient_evidence_warning():
    validator = ProvenanceValidator()
    block = NarrativeBlock(
        block_id="nb_03",
        text="No data found.",
        evidence_refs=[],
        confidence=0.0,
        insufficient_evidence=True,
    )
    issues = validator.validate_narrative_block("sec_test", block)
    warns = [i for i in issues if "insufficient evidence" in i.message]
    assert len(warns) == 1
