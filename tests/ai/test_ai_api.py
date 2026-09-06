"""
FastAPI integration tests for Local AI Gateway & Benchmark endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from apps.processing.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_ai_models(client):
    res = client.get("/api/v1/ai/models")
    assert res.status_code == 200
    data = res.json()
    assert "active_model" in data
    assert "available_backends" in data
    assert len(data["available_backends"]) >= 3
    assert data["active_model"]["is_loaded"] is True


def test_ai_generate_endpoint(client):
    payload = {
        "prompt": "Summarize production from [DOC:Test_Doc.pdf:P01] achieving 500 MT.",
        "max_tokens": 128,
        "temperature": 0.0,
    }
    res = client.post("/api/v1/ai/generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "content" in data
    assert "model_name" in data
    assert data["grounding_metadata"]["is_grounded"] is True
    assert "[DOC:Test_Doc.pdf:P01]" in data["grounding_metadata"]["cited_references"]


def test_ai_summarize_endpoint(client):
    payload = {
        "evidence_text": "Audited coal offtake reached 700 MT as per [DOC:offtake.pdf:P03].",
        "focus_areas": ["offtake"],
    }
    res = client.post("/api/v1/ai/summarize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "[DOC:offtake.pdf:P03]" in data["content"]


def test_select_backend_air_gap_validation(client):
    # Attempting to set an external non-loopback server should fail with 400
    payload = {
        "backend_type": "llama.cpp-http",
        "endpoint_url": "https://api.openai.com/v1",
    }
    res = client.post("/api/v1/ai/backend/select", json=payload)
    assert res.status_code == 400
    assert "Air-gapped security violation" in res.json()["detail"]


def test_run_benchmark_endpoint(client):
    res = client.post("/api/v1/ai/benchmark")
    assert res.status_code == 200
    data = res.json()
    assert data["total_tasks"] == 8
    assert data["mean_accuracy"] > 0
    assert data["mean_grounding"] > 0
    assert data["passed"] is True

    # Check benchmark list endpoint
    list_res = client.get("/api/v1/ai/benchmarks")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
