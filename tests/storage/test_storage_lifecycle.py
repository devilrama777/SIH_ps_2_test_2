import pytest
from pathlib import Path
from core.storage.lifecycle import StorageManager, ArtifactCategory


def test_storage_breakdown_and_accounting(tmp_path):
    sm = StorageManager(workspace_dir=str(tmp_path))

    # Add mock files to sources and temp
    source_file = tmp_path / "sources" / "test_raw_doc.pdf"
    source_file.write_text("dummy raw pdf source content", encoding="utf-8")

    temp_file = tmp_path / "temp" / "render_scratch_buffer.html"
    temp_file.write_text("<html>temp scratch buffer</html>", encoding="utf-8")

    breakdown = sm.get_storage_breakdown()

    assert ArtifactCategory.ORIGINAL_SOURCE.value in breakdown
    assert ArtifactCategory.RENDER_TEMP.value in breakdown

    assert breakdown[ArtifactCategory.ORIGINAL_SOURCE.value].file_count == 1
    assert breakdown[ArtifactCategory.RENDER_TEMP.value].file_count == 1
    assert breakdown[ArtifactCategory.ORIGINAL_SOURCE.value].total_bytes > 0


def test_temporary_cleanup_protects_original_sources(tmp_path):
    sm = StorageManager(workspace_dir=str(tmp_path))

    # Create raw source file
    source_file = tmp_path / "sources" / "critical_ccl_report.pdf"
    source_file.write_text("IMPORTANT ORIGINAL CIL DATA", encoding="utf-8")

    # Create ephemeral temp files
    temp_file_1 = tmp_path / "temp" / "scratch_page_1.html"
    temp_file_1.write_text("temp html", encoding="utf-8")

    temp_file_2 = tmp_path / "temp" / "browser_buffer.tmp"
    temp_file_2.write_text("browser buffer", encoding="utf-8")

    # Execute cleanup
    cleanup_res = sm.cleanup_temporary_artifacts(max_age_seconds=0.0, dry_run=False)

    assert cleanup_res["deleted_file_count"] == 2
    assert cleanup_res["freed_bytes"] > 0
    assert not temp_file_1.exists()
    assert not temp_file_2.exists()

    # Section 37 Invariant: Original source MUST NOT be deleted
    assert source_file.exists()
    assert source_file.read_text(encoding="utf-8") == "IMPORTANT ORIGINAL CIL DATA"


def test_safe_purge_category_rejection(tmp_path):
    sm = StorageManager(workspace_dir=str(tmp_path))

    # Attempting to purge ORIGINAL_SOURCE must unconditionally raise PermissionError
    with pytest.raises(PermissionError) as exc_info:
        sm.safe_purge_category(ArtifactCategory.ORIGINAL_SOURCE, confirmation="PURGE_ORIGINAL_SOURCE")
    assert "Section 37 Invariant" in str(exc_info.value)

    # Invalid confirmation token raises ValueError
    with pytest.raises(ValueError):
        sm.safe_purge_category(ArtifactCategory.RENDER_TEMP, confirmation="WRONG_TOKEN")
