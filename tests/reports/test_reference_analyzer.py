"""
Unit tests for ReferenceReportAnalyzer (Section 14).
"""
from core.domain.documents import CanonicalDocument, DocumentElement, DocumentType, ElementType, Page
from core.reports.planner.reference_analyzer import ReferenceReportAnalyzer


def test_reference_report_analyzer_outline_and_themes():
    analyzer = ReferenceReportAnalyzer()

    page1_elements = [
        DocumentElement(
            element_id="el_01",
            document_id="ref_doc_001",
            type=ElementType.HEADING,
            text="Corporate Profile & Vision",
            page_number=1,
            reading_order=1,
            metadata={"heading_level": 1},
        ),
        DocumentElement(
            element_id="el_02",
            document_id="ref_doc_001",
            type=ElementType.PARAGRAPH,
            text="The subsidiary operates opencast and underground mines in Eastern India.",
            page_number=1,
            reading_order=2,
        ),
    ]

    page2_elements = [
        DocumentElement(
            element_id="el_03",
            document_id="ref_doc_001",
            type=ElementType.HEADING,
            text="Operational Performance & Coal Production",
            page_number=2,
            reading_order=1,
            metadata={"heading_level": 1},
        ),
        DocumentElement(
            element_id="el_04",
            document_id="ref_doc_001",
            type=ElementType.TABLE,
            text="Production (MT) | Offtake (MT)\n773.6 | 750.2",
            page_number=2,
            reading_order=2,
        ),
    ]

    page3_elements = [
        DocumentElement(
            element_id="el_05",
            document_id="ref_doc_001",
            type=ElementType.HEADING,
            text="Financial Performance & Highlights",
            page_number=3,
            reading_order=1,
            metadata={"heading_level": 1},
        ),
    ]

    doc = CanonicalDocument(
        document_id="ref_doc_001",
        source_reference="CIL_Annual_Report_2023_24.pdf",
        source_hash="abc123hash",
        document_type=DocumentType.DIGITAL_PDF,
        reporting_year="2023-24",
        pages=[
            Page(page_number=1, elements=page1_elements),
            Page(page_number=2, elements=page2_elements),
            Page(page_number=3, elements=page3_elements),
        ],
    )

    analysis = analyzer.analyze(doc)

    assert analysis.total_pages == 3
    assert len(analysis.extracted_outline) >= 3
    assert "Operational & Production Performance" in analysis.recurring_topics
    assert "Financial Performance & Highlights" in analysis.recurring_topics
    assert analysis.table_patterns["total_tables_extracted"] == 1
