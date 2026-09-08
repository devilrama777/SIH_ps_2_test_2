"""
Tests for Typed Source Locators and Provenance Discrimination.

Verifies:
1. PdfLocator serialization and bbox preservation.
2. SpreadsheetLocator sheet/cell/range coordinate mapping.
3. DocxLocator paragraph/table/heading path mapping.
4. ImageLocator dimension and region mapping.
5. TextLocator line/char offset mapping.
6. ProvenanceRecord polymorphic deserialization via SourceLocator discriminated union.
7. Backward compatibility with legacy spreadsheet_coord / page_number fields.
"""
import pytest
from core.domain.documents import BoundingBox
from core.domain.evidence import (
    ProvenanceRecord,
    SourceLocator,
    PdfLocator,
    SpreadsheetLocator,
    DocxLocator,
    ImageLocator,
    TextLocator,
)


def test_pdf_locator():
    bbox = BoundingBox(x0=50.0, y0=100.0, x1=500.0, y1=700.0, page_width=595.0, page_height=842.0)
    loc = PdfLocator(page_number=3, bbox=bbox)
    prov = ProvenanceRecord(
        provenance_id="prov_001",
        document_id="doc_pdf_1",
        source_reference="/data/mining_report.pdf",
        locator=loc,
        page_number=loc.page_number,
        bbox=loc.bbox,
    )
    
    dumped = prov.model_dump_json()
    loaded = ProvenanceRecord.model_validate_json(dumped)

    assert loaded.locator is not None
    assert isinstance(loaded.locator, PdfLocator)
    assert loaded.locator.type == "pdf"
    assert loaded.locator.page_number == 3
    assert loaded.locator.bbox.x0 == 50.0


def test_spreadsheet_locator():
    loc = SpreadsheetLocator(
        workbook_name="ECL_Production_FY24.xlsx",
        sheet_name="OB_Removal",
        cell="G27",
        cell_range="G25:G30",
        row=27,
        column=7,
        raw_value=14250000.5,
        formatted_value="14,250,000.50 M.Cu.M",
    )
    prov = ProvenanceRecord(
        provenance_id="prov_002",
        document_id="doc_xlsx_1",
        source_reference="/data/ECL_Production_FY24.xlsx",
        locator=loc,
        spreadsheet_coord=loc,
    )

    dumped = prov.model_dump_json()
    loaded = ProvenanceRecord.model_validate_json(dumped)

    assert loaded.locator is not None
    assert isinstance(loaded.locator, SpreadsheetLocator)
    assert loaded.locator.type == "spreadsheet"
    assert loaded.locator.cell == "G27"
    assert loaded.spreadsheet_coord.row == 27


def test_docx_locator():
    loc = DocxLocator(
        paragraph_index=14,
        table_index=2,
        heading_path=["Executive Summary", "Financial Highlights"],
    )
    prov = ProvenanceRecord(
        provenance_id="prov_003",
        document_id="doc_docx_1",
        source_reference="/data/briefing.docx",
        locator=loc,
    )

    dumped = prov.model_dump_json()
    loaded = ProvenanceRecord.model_validate_json(dumped)

    assert loaded.locator is not None
    assert isinstance(loaded.locator, DocxLocator)
    assert loaded.locator.type == "docx"
    assert loaded.locator.heading_path == ["Executive Summary", "Financial Highlights"]


def test_image_and_text_locators():
    img_loc = ImageLocator(width=1920, height=1080)
    prov_img = ProvenanceRecord(
        provenance_id="prov_004",
        document_id="doc_img_1",
        source_reference="/data/quarry_satellite.png",
        locator=img_loc,
    )
    loaded_img = ProvenanceRecord.model_validate_json(prov_img.model_dump_json())
    assert isinstance(loaded_img.locator, ImageLocator)
    assert loaded_img.locator.width == 1920

    txt_loc = TextLocator(line_start=10, line_end=25, char_offset=450)
    prov_txt = ProvenanceRecord(
        provenance_id="prov_005",
        document_id="doc_txt_1",
        source_reference="/data/logs.txt",
        locator=txt_loc,
    )
    loaded_txt = ProvenanceRecord.model_validate_json(prov_txt.model_dump_json())
    assert isinstance(loaded_txt.locator, TextLocator)
    assert loaded_txt.locator.char_offset == 450
