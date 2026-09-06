"""
Unit tests for EvidenceToSectionMapper (Section 13 & 15).
"""
from unittest.mock import MagicMock
from core.domain.evidence import SpreadsheetCoordinate
from core.reports.planner.evidence_mapper import EvidenceToSectionMapper
from core.retrieval.search import RankedEvidence


def test_evidence_mapper_packaging_and_sufficiency():
    mock_search = MagicMock()
    mock_search.search.return_value = [
        RankedEvidence(
            element_id="el_101",
            document_id="doc_prod_01",
            source_reference="production.pdf",
            page_number=12,
            element_type="text",
            text="Raw coal production reached 773.60 MT.",
            score=0.85,
        ),
        RankedEvidence(
            element_id="el_102",
            document_id="doc_prod_02",
            source_reference="stats.xlsx",
            page_number=1,
            element_type="table_cell",
            text="773.60",
            score=0.90,
            spreadsheet_coord=SpreadsheetCoordinate(
                workbook_name="stats.xlsx",
                sheet_name="March",
                cell="G27",
                row=27,
                column=7,
            ),
        ),
    ]

    mapper = EvidenceToSectionMapper(search_engine=mock_search)
    pkg = mapper.map_evidence_for_section(
        section_id="sec_01",
        section_title="Operational Performance & Coal Production",
        financial_year="2024-25",
    )

    assert pkg.section_id == "sec_01"
    assert len(pkg.ranked_evidence) == 2
    assert len(pkg.spreadsheet_coordinates) == 1
    assert pkg.spreadsheet_coordinates[0].cell == "G27"
    assert pkg.sufficiency_score > 0.0
    assert pkg.is_sufficient is True
