"""
Tests for DataConnector base interface contract.
"""
from typing import Any, Dict, List, Optional
from core.connectors.base import ConnectorHealth, DataConnector, SourceItem


class MockMemoryConnector(DataConnector):
    """Test connector operating in memory."""
    def __init__(self):
        self._items = {
            "src_01": b"Sample PDF binary data",
            "src_02": b"Sample CSV text data",
        }

    def discover(self, query: Optional[Dict[str, Any]] = None) -> List[SourceItem]:
        return self.list_sources()

    def list_sources(self) -> List[SourceItem]:
        return [
            SourceItem(
                source_id="src_01",
                source_uri="memory://data/annual_report.pdf",
                filename="annual_report.pdf",
                file_extension=".pdf",
                file_size_bytes=len(self._items["src_01"]),
            ),
            SourceItem(
                source_id="src_02",
                source_uri="memory://data/production.csv",
                filename="production.csv",
                file_extension=".csv",
                file_size_bytes=len(self._items["src_02"]),
            ),
        ]

    def fetch_document(self, source_id: str) -> bytes:
        return self._items[source_id]

    def fetch_metadata(self, source_id: str) -> Dict[str, Any]:
        return {"source_id": source_id, "format": "binary"}

    def health_check(self) -> ConnectorHealth:
        return ConnectorHealth(
            healthy=True,
            connector_type="mock_memory",
            details={"item_count": len(self._items)},
        )


def test_data_connector_contract():
    """Verify DataConnector interface implementation and health check."""
    conn = MockMemoryConnector()
    health = conn.health_check()
    assert health.healthy is True
    assert health.connector_type == "mock_memory"

    sources = conn.list_sources()
    assert len(sources) == 2
    assert sources[0].filename == "annual_report.pdf"

    data = conn.fetch_document("src_01")
    assert data.startswith(b"Sample PDF")
