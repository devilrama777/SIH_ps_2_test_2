"""
Tests for ValidationEngine — Section 17 full multi-dimensional report validation.
"""
from datetime import datetime
from core.domain.reports import NarrativeBlock, Report, ReportSection, SectionType, ValidationStatus
from core.domain.evidence import EvidenceReference, ProvenanceRecord
from core.validation.engine import ValidationEngine


def test_validation_engine_full_flow():
    engine = ValidationEngine()

    ref = EvidenceReference(
        evidence_id="ref_01",
        provenance=ProvenanceRecord(
            provenance_id="prov_01",
            document_id="doc_2025",
            source_reference="Annual_Report_2025.pdf",
            page_number=5,
        ),
        excerpt_text="Corporate Overview",
        confidence_score=1.0,
    )

    sec_corp = ReportSection(
        section_id="sec_01",
        title="Corporate Overview",
        level=1,
        type=SectionType.MANDATORY,
        narrative_blocks=[
            NarrativeBlock(
                block_id="nb_01",
                text="Established in 1975, the company operates across India [DOC:Annual_Report_2025.pdf:P5].",
                evidence_refs=[ref],
                confidence=1.0,
            )
        ],
    )

    sec_ops = ReportSection(
        section_id="sec_02",
        title="Operational Performance",
        level=1,
        type=SectionType.MANDATORY,
        narrative_blocks=[
            NarrativeBlock(
                block_id="nb_02",
                text="Total raw coal production reached 65.4 MT [DOC:Annual_Report_2025.pdf:P12].",
                evidence_refs=[ref],
                confidence=1.0,
            )
        ],
    )

    sec_fin = ReportSection(
        section_id="sec_03",
        title="Financial Highlights",
        level=1,
        type=SectionType.MANDATORY,
        narrative_blocks=[
            NarrativeBlock(
                block_id="nb_03",
                text="Revenue from operations was ₹12,500 crores [DOC:Annual_Report_2025.pdf:P20].",
                evidence_refs=[ref],
                confidence=1.0,
            )
        ],
    )

    sec_safety = ReportSection(
        section_id="sec_04",
        title="Safety & Sustainable Mining",
        level=1,
        type=SectionType.MANDATORY,
        narrative_blocks=[
            NarrativeBlock(
                block_id="nb_04",
                text="Zero fatalities were recorded in underground operations [DOC:Annual_Report_2025.pdf:P32].",
                evidence_refs=[ref],
                confidence=1.0,
            )
        ],
    )

    sec_audit = ReportSection(
        section_id="sec_05",
        title="Auditors' Report & Financial Statements",
        level=1,
        type=SectionType.MANDATORY,
        narrative_blocks=[
            NarrativeBlock(
                block_id="nb_05",
                text="The financial statements give a true and fair view [DOC:Annual_Report_2025.pdf:P45].",
                evidence_refs=[ref],
                confidence=1.0,
            )
        ],
    )

    report = Report(
        report_id="rep_test_01",
        title="Annual Report 2024-25",
        reporting_period="FY 2024-25",
        subsidiary_name="Central Coalfields Limited",
        template_name="classic",
        sections=[sec_corp, sec_ops, sec_fin, sec_safety, sec_audit],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        version=1,
    )

    val_result = engine.validate_report(report)
    assert val_result.report_id == "rep_test_01"
    assert val_result.error_count == 0
    assert val_result.passed is True
    assert val_result.overall_status in (ValidationStatus.VALID, ValidationStatus.WARNING)
