"""
Integration tests for LocalFolderConnector (Section 4).
"""
from pathlib import Path
from core.connectors.local import LocalFolderConnector


def test_local_folder_connector_workflow(tmp_path: Path):
    """Test health check, discovery, metadata, and binary fetch on a local folder."""
    data_dir = tmp_path / "mining_data"
    data_dir.mkdir()

    csv_file = data_dir / "coal_stats.csv"
    csv_content = b"Colliery,Target,Actual\nNorth,100,105\n"
    csv_file.write_bytes(csv_content)

    connector = LocalFolderConnector(data_dir)

    # Health check
    health = connector.health_check()
    assert health.healthy is True
    assert health.connector_type == "local_folder"

    # List sources
    sources = connector.list_sources()
    assert len(sources) == 1
    assert sources[0].filename == "coal_stats.csv"

    source_id = sources[0].source_id
    assert source_id is not None

    # Fetch document bytes
    fetched_bytes = connector.fetch_document(source_id)
    assert fetched_bytes == csv_content

    # Fetch metadata
    meta = connector.fetch_metadata(source_id)
    assert meta["filename"] == "coal_stats.csv"
    assert meta["file_size_bytes"] == len(csv_content)
