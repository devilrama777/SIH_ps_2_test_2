"""
Tests for canonical document, evidence, job, and report domain models.
"""
from core.domain.documents import (
    BoundingBox,
    CanonicalDocument,
    DocumentElement,
    DocumentType,
    ElementType,
    Page,
)
from core.domain.evidence import (
    EvidenceReference,
    ProvenanceRecord,
    SpreadsheetCoordinate,
)
from core.domain.jobs import JobStage, JobStatus, ProcessingJob
from core.domain.reports import (
    NarrativeBlock,
    Report,
    ReportSection,
    SectionType,
    ValidationStatus,
)
from core.provenance.tracker import (
    create_provenance_record,
    generate_document_id,
    generate_element_id,
)


def test_canonical_document_creation():
    """Verify CanonicalDocument model structure and element containment."""
    bbox = BoundingBox(x0=10.0, y0=20.0, x1=200.0, y1=150.0, page_width=595.0, page_height=842.0)
    assert bbox.to_list() == [10.0, 20.0, 200.0, 150.0]

    el = DocumentElement(
        element_id="el_doc1_p1_00001",
        document_id="doc1",
        type=ElementType.PARAGRAPH,
        page_number=1,
        bbox=bbox,
        text="Coal production during FY25 reached 773.6 MT.",
        confidence=0.98,
    )
    assert el.text is not None

    page = Page(page_number=1, width=595.0, height=842.0, elements=[el])
    assert len(page.elements) == 1

    doc = CanonicalDocument(
        document_id="doc_test123",
        source_reference="C:/data/production.pdf",
        source_hash="abcdef123456",
        document_type=DocumentType.DIGITAL_PDF,
        reporting_year="2024-25",
        reporting_period="Q4",
        pages=[page],
    )
    assert doc.document_type == DocumentType.DIGITAL_PDF
    assert len(doc.pages) == 1
    assert doc.pages[0].elements[0].confidence == 0.98


def test_provenance_and_evidence():
    """Verify provenance record creation and spreadsheet coordinate mapping."""
    sheet_coord = SpreadsheetCoordinate(
        workbook_name="coal_stats.xlsx",
        sheet_name="March2025",
        cell="G27",
        raw_value=1245.70,
        formatted_value="1,245.70",
    )

    prov = create_provenance_record(
        document_id="doc_fin_01",
        source_reference="C:/data/coal_stats.xlsx",
        spreadsheet_coord=sheet_coord,
        extraction_method="xlsx_cell",
        reporting_period="March 2025",
    )
    assert prov.provenance_id.startswith("prov_")
    assert prov.spreadsheet_coord is not None
    assert prov.spreadsheet_coord.cell == "G27"

    ev = EvidenceReference(
        evidence_id="ev_001",
        provenance=prov,
        excerpt_text="Total Production: 1,245.70 MT",
        numeric_value=1245.70,
        unit="MT",
    )
    assert ev.numeric_value == 1245.70


def test_provenance_id_helpers():
    """Verify deterministic document and element ID generation."""
    sample_bytes = b"Sample CIL subsidiary annual report content"
    doc_id = generate_document_id("file:///report.pdf", sample_bytes)
    assert doc_id.startswith("doc_")
    assert len(doc_id) == 16  # "doc_" + 12 chars

    el_id = generate_element_id("doc_test", page_number=5, index=42)
    assert el_id == "el_doc_test_p5_00042"


def test_report_data_model():
    """Verify report data model and section hierarchy."""
    narrative = NarrativeBlock(
        block_id="block_01",
        text="Coal India subsidiaries demonstrated robust operational turnaround.",
    )

    sec = ReportSection(
        section_id="sec_operational_review",
        title="Operational Review",
        level=1,
        type=SectionType.MANDATORY,
        narrative_blocks=[narrative],
        validation_status=ValidationStatus.VALID,
    )

    report = Report(
        report_id="rep_2025_001",
        title="Annual Subsidiary Performance Report",
        reporting_period="FY 2024-25",
        subsidiary_name="Central Coalfields Limited",
        template_name="modern",
        sections=[sec],
    )
    assert len(report.sections) == 1
    assert report.sections[0].title == "Operational Review"
    assert report.template_name == "modern"


def test_processing_job_model():
    """Verify background processing job state transitions."""
    job = ProcessingJob(
        job_id="job_ingest_001",
        job_type="ingest_folder",
        status=JobStatus.RUNNING,
        progress=45.5,
        current_stage=JobStage.EXTRACTION,
        total_items=100,
        processed_items=45,
    )
    assert job.status == JobStatus.RUNNING
    assert job.current_stage == JobStage.EXTRACTION
    assert job.progress == 45.5
