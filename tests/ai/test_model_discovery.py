"""
Tests for Local AI Discovery and Gateway Model Selection.

Verifies:
1. discover_local_models scans loopback ports and returns models if online.
2. get_best_available_backend returns LocalHttpInferenceBackend when server is active,
   or cleanly falls back to RuleBasedLocalBackend.
3. GET /api/v1/ai/models returns discovered models structure.
4. Switching backends via POST /api/v1/ai/backend/select works cleanly.
"""
from fastapi.testclient import TestClient
from apps.processing.server import app, ai_gateway
from core.ai.discovery import discover_local_models, get_best_available_backend
from core.ai.backends.base import LocalInferenceBackend
from core.ai.backends.rule_based import RuleBasedLocalBackend
from core.ai.backends.local_server import LocalHttpInferenceBackend

client = TestClient(app)


def test_discover_local_models_live():
    # If Ollama or llama.cpp is running on host machine, models will be discovered
    models = discover_local_models()
    assert isinstance(models, list)
    # Each discovered entry must adhere to schema
    for m in models:
        assert "model_id" in m
        assert "endpoint_url" in m
        assert "127.0.0.1" in m["endpoint_url"]


def test_get_best_available_backend():
    backend = get_best_available_backend()
    assert isinstance(backend, LocalInferenceBackend)
    assert backend.is_available() is True


def test_ai_models_endpoint():
    res = client.get("/api/v1/ai/models")
    assert res.status_code == 200
    data = res.json()
    assert "active_model" in data
    assert "discovered_models" in data
    assert "available_backends" in data


def test_ai_backend_select_deterministic():
    res = client.post(
        "/api/v1/ai/backend/select",
        json={"backend_type": "deterministic-local"},
    )
    assert res.status_code == 200
    assert res.json()["backend"] == "deterministic-local"
