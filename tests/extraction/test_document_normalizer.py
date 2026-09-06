"""
Tests for DocumentNormalizer (Section 8 Secondary Markdown Normalization Layer).
"""
import pytest
from pathlib import Path
from core.domain.documents import (
    CanonicalDocument,
    DocumentElement,
    DocumentType,
    ElementType,
    Page,
)
from core.extraction.normalizer import DocumentNormalizer


def test_document_normalizer_with_headings_paragraphs_and_tables(tmp_path: Path):
    doc = CanonicalDocument(
        document_id="doc_test_ccl_01",
        source_reference="testdata/ccl_overview.pdf",
        source_hash="abcdef1234567890abcdef1234567890",
        document_type=DocumentType.DIGITAL_PDF,
        reporting_year="2024",
        reporting_period="FY 2023-24",
        pages=[
            Page(
                page_number=1,
                elements=[
                    DocumentElement(
                        element_id="el_h1",
                        document_id="doc_test_ccl_01",
                        type=ElementType.HEADING,
                        page_number=1,
                        text="Operational Performance Overview",
                        metadata={"level": 1},
                        reading_order=1,
                    ),
                    DocumentElement(
                        element_id="el_p1",
                        document_id="doc_test_ccl_01",
                        type=ElementType.PARAGRAPH,
                        page_number=1,
                        text="Central Coalfields Limited achieved raw coal production of 84.5 MT in FY24.",
                        reading_order=2,
                    ),
                    DocumentElement(
                        element_id="el_tbl1",
                        document_id="doc_test_ccl_01",
                        type=ElementType.TABLE,
                        page_number=1,
                        metadata={
                            "headers": ["Indicator", "FY 2022-23", "FY 2023-24", "Growth (%)"],
                            "rows": [
                                ["Production (MT)", "77.5", "84.5", "+9.03%"],
                                ["Offtake (MT)", "75.3", "82.1", "+9.03%"],
                            ],
                        },
                        reading_order=3,
                    ),
                ],
            )
        ],
    )

    normalizer = DocumentNormalizer(output_dir=tmp_path)
    md_text = normalizer.normalize(doc)

    assert "# Document: ccl_overview.pdf" in md_text
    assert "Operational Performance Overview" in md_text
    assert "84.5 MT in FY24" in md_text
    assert "| Indicator | FY 2022-23 | FY 2023-24 | Growth (%) |" in md_text
    assert "| Production (MT) | 77.5 | 84.5 | +9.03% |" in md_text
    assert "<!-- provenance: doc=doc_test_ccl_01 page=1 el=el_h1" in md_text
    assert "<!-- provenance: doc=doc_test_ccl_01 page=1 el=el_tbl1" in md_text
    assert doc.markdown_content == md_text

    # Test file saving
    saved_path = normalizer.normalize_and_save(doc)
    assert saved_path.exists()
    assert saved_path.read_text(encoding="utf-8") == md_text
