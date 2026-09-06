import pytest
from fastapi.testclient import TestClient
from apps.processing.server import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_evaluation_api_lifecycle(client):
    # 1. Run golden evaluation suite
    res = client.post("/api/v1/evaluation/run-golden-suite")
    assert res.status_code == 200
    data = res.json()

    assert data["run_id"].startswith("gold_")
    assert data["total_golden_fixtures"] >= 4
    assert data["ingested_documents"] >= 3
    assert data["generated_sections"] >= 2
    assert data["audit_chain_verified"] is True
    assert data["pdf_generated"] is True
    assert data["metrics"]["source_coverage"] > 0.50

    # 2. Query latest report
    latest_res = client.get("/api/v1/evaluation/latest-report")
    assert latest_res.status_code == 200
    latest_data = latest_res.json()
    assert latest_data["run_id"] == data["run_id"]
