"""
Local AI Model Discovery and Auto-Selection.

Scans standard air-gapped local model ports (e.g., Ollama at 11434, llama.cpp at 8080)
via loopback HTTP to discover installed GGUF/local models without manual configuration.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

from core.ai.backends.base import LocalInferenceBackend
from core.ai.backends.local_server import LocalHttpInferenceBackend
from core.ai.backends.rule_based import RuleBasedLocalBackend

logger = logging.getLogger(__name__)

STANDARD_LOCAL_PORTS = [11434, 8080, 5000]


def discover_local_models(
    ports: Optional[List[int]] = None,
    timeout: float = 1.5,
) -> List[Dict[str, Any]]:
    """
    Query local loopback servers for OpenAI-compatible or Ollama-native model lists.
    Returns a list of discovered model descriptor dictionaries.
    """
    ports = ports or STANDARD_LOCAL_PORTS
    discovered: List[Dict[str, Any]] = []

    for port in ports:
        base_v1 = f"http://127.0.0.1:{port}/v1"
        try:
            req = urllib.request.Request(
                f"{base_v1}/models",
                headers={"User-Agent": "MineIntel-Discovery/1.0"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = data.get("data", [])
                    for m in models:
                        m_id = m.get("id")
                        if m_id:
                            discovered.append({
                                "model_id": m_id,
                                "name": m_id,
                                "backend_type": "llama.cpp-http",
                                "endpoint_url": base_v1,
                                "port": port,
                                "server": "ollama" if port == 11434 else "llama.cpp",
                                "status": "available",
                            })
        except Exception:
            # Try native Ollama endpoint if /v1/models fails
            if port == 11434:
                try:
                    req_native = urllib.request.Request(
                        "http://127.0.0.1:11434/api/tags",
                        headers={"User-Agent": "MineIntel-Discovery/1.0"},
                    )
                    with urllib.request.urlopen(req_native, timeout=timeout) as resp_native:
                        if resp_native.status == 200:
                            data_native = json.loads(resp_native.read().decode("utf-8"))
                            for m in data_native.get("models", []):
                                m_name = m.get("name")
                                if m_name:
                                    discovered.append({
                                        "model_id": m_name,
                                        "name": m_name,
                                        "backend_type": "llama.cpp-http",
                                        "endpoint_url": base_v1,
                                        "port": port,
                                        "server": "ollama",
                                        "status": "available",
                                    })
                except Exception:
                    pass

    return discovered


def get_best_available_backend(
    preferred_models: Optional[List[str]] = None,
) -> LocalInferenceBackend:
    """
    Select the highest capability local model backend available on loopback.
    Prefers llama3.1, gemma2/gemma4, or any detected local model before falling back to rule-based.
    """
    preferred_models = preferred_models or ["llama3.1:latest", "llama3.1", "gemma4:latest", "gemma2", "gemma-2-9b-it"]
    discovered = discover_local_models()

    if discovered:
        # Match preferred model first
        for pref in preferred_models:
            for item in discovered:
                if pref.lower() in item["model_id"].lower():
                    logger.info("Auto-selected preferred local model: %s on %s", item["model_id"], item["endpoint_url"])
                    return LocalHttpInferenceBackend(
                        endpoint_url=item["endpoint_url"],
                        model_name=item["model_id"],
                    )

        # Otherwise pick first available discovered model
        first = discovered[0]
        logger.info("Auto-selected first available local model: %s on %s", first["model_id"], first["endpoint_url"])
        return LocalHttpInferenceBackend(
            endpoint_url=first["endpoint_url"],
            model_name=first["model_id"],
        )

    # Fallback to deterministic rule-based engine when no servers are online
    logger.info("No local AI servers detected on loopback. Initializing deterministic verification engine.")
    return RuleBasedLocalBackend()
