"""
Unit tests for Local AI Backends and Air-Gapped Security Validation.
"""
import pytest
from core.ai.backends.rule_based import RuleBasedLocalBackend
from core.ai.backends.local_server import LocalHttpInferenceBackend
from core.ai.backends.direct import LlamaCppDirectBackend


def test_rule_based_backend():
    backend = RuleBasedLocalBackend()
    assert backend.is_available() is True

    info = backend.get_model_info()
    assert info.model_id == "local-rule-engine-v1"
    assert info.is_loaded is True
    assert info.ram_usage_mb is not None

    res = backend.generate("Please summarize [DOC:prod.pdf:P01] raw coal production 500 MT.")
    assert res.completion_tokens > 0
    assert "[DOC:prod.pdf:P01]" in res.text


def test_local_server_backend_air_gap_validation():
    # Valid loopback addresses
    valid_backend = LocalHttpInferenceBackend(endpoint_url="http://127.0.0.1:8000/v1")
    assert valid_backend.endpoint_url == "http://127.0.0.1:8000/v1"

    valid_localhost = LocalHttpInferenceBackend(endpoint_url="http://localhost:11434/v1")
    assert valid_localhost.endpoint_url == "http://localhost:11434/v1"

    # External cloud URLs MUST be strictly rejected with ValueError
    with pytest.raises(ValueError, match="Air-gapped security violation"):
        LocalHttpInferenceBackend(endpoint_url="https://api.openai.com/v1")

    with pytest.raises(ValueError, match="Air-gapped security violation"):
        LocalHttpInferenceBackend(endpoint_url="http://192.168.1.50:8080/v1")


def test_llama_cpp_direct_backend_availability():
    # Without model file, should report available=False gracefully without crashing
    backend = LlamaCppDirectBackend(model_path="non_existent_model.gguf")
    assert backend.is_available() is False

    info = backend.get_model_info()
    assert info.is_loaded is False
