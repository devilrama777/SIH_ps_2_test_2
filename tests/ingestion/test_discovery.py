"""
Tests for Section 6 file discovery, recursion, and filtering.
"""
from pathlib import Path
from core.ingestion.discovery import discover_files
from core.ingestion.formats import DocumentFormat


def test_discover_files_recursion(tmp_path: Path):
    """Verify recursive file discovery across nested directories."""
    sub1 = tmp_path / "2024-25" / "Q4"
    sub1.mkdir(parents=True)
    sub2 = tmp_path / "unorganized"
    sub2.mkdir(parents=True)

    # Valid supported files
    (sub1 / "production_march.csv").write_text("a,b,c")
    (sub1 / "financial_statement.xlsx").write_bytes(b"dummy_excel")
    (sub2 / "site_photo.jpg").write_bytes(b"dummy_jpg")
    (sub2 / "board_minutes.docx").write_bytes(b"dummy_docx")

    # Excluded files
    (sub2 / "backup.zip").write_bytes(b"dummy_zip")
    (sub2 / "slides.pptx").write_bytes(b"dummy_pptx")
    (sub2 / ".hidden_file.pdf").write_bytes(b"dummy_hidden")

    files = discover_files(tmp_path, compute_hashes=True)

    filenames = [f.filename for f in files]
    assert "production_march.csv" in filenames
    assert "financial_statement.xlsx" in filenames
    assert "site_photo.jpg" in filenames
    assert "board_minutes.docx" in filenames

    # Ensure disallowed formats are excluded
    assert "backup.zip" not in filenames
    assert "slides.pptx" not in filenames
    assert ".hidden_file.pdf" not in filenames

    assert len(files) == 4
    for f in files:
        assert f.sha256 is not None
        assert len(f.sha256) == 64


def test_discover_files_empty_dir(tmp_path: Path):
    """Empty directory yields empty list."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    files = discover_files(empty_dir)
    assert len(files) == 0
