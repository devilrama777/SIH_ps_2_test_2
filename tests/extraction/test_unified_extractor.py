"""
Tests for UnifiedDocumentExtractor routing.
"""
from pathlib import Path
from core.domain.documents import DocumentType
from core.extraction.unified import extract_document


def test_unified_dispatcher_routing(tmp_path: Path):
    """Verify UnifiedDocumentExtractor routes correctly to various parsers."""
    # Test CSV routing
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,val\n1,100\n")
    doc_csv = extract_document(csv_file)
    assert doc_csv.document_type == DocumentType.CSV

    # Test TXT routing
    txt_file = tmp_path / "memo.txt"
    txt_file.write_text("Important Notice\n\nMeeting at 10 AM.")
    doc_txt = extract_document(txt_file)
    assert doc_txt.document_type == DocumentType.TXT
