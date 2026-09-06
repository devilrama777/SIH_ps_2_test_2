"""
Tests for SourceTraceabilityService — Section 21 of Master Plan.
"""
from core.reports.traceability.viewer import SourceTraceabilityService


def test_source_traceability_resolution(tmp_path):
    canonical_dir = tmp_path / "canonical"
    canonical_dir.mkdir()

    # Save a mock canonical document
    doc_json = {
        "document_id": "doc_ccl_ops_2025",
        "total_pages": 12,
        "metadata": {
            "source_reference": "CCL_Operations_FY25.pdf",
            "format": "pdf",
        },
        "pages": [
            {
                "page_number": 4,
                "elements": [
                    {"element_id": "el_1", "text": "North Karanpura opencast raw coal production reached 34.2 MT."},
                    {"element_id": "el_2", "text": "Dispatch via rail siding accounted for 82% of offtake."},
                ],
            }
        ],
    }

    import json
    with open(canonical_dir / "doc_ccl_ops_2025.json", "w", encoding="utf-8") as f:
        json.dump(doc_json, f)

    service = SourceTraceabilityService(canonical_dir=str(canonical_dir))

    # Resolve citation [DOC:CCL_Operations_FY25.pdf:P4]
    res = service.resolve_citation("CCL_Operations_FY25.pdf", page_number=4)
    assert res.found is True
    assert res.document_id == "doc_ccl_ops_2025"
    assert res.page_number == 4
    assert "North Karanpura" in res.snippet_text
