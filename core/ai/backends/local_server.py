"""
Local HTTP Server Inference Backend (llama.cpp server / Ollama local).

Strictly restricted to localhost (127.0.0.1 / localhost) loopback endpoints.
External and internet network addresses are rejected.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import urllib.request
import urllib.error
import psutil

from core.ai.backends.base import InferenceResult, LocalInferenceBackend
from core.ai.gateway.base import ModelInfo


class LocalHttpInferenceBackend(LocalInferenceBackend):
    """
    Connects to an air-gapped local model server (llama.cpp server or Ollama)
    running exclusively on localhost / 127.0.0.1.
    """

    ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}

    def __init__(
        self,
        endpoint_url: str = "http://127.0.0.1:8080/v1",
        model_name: str = "gemma-2-9b-it",
        context_window: int = 8192,
        timeout_seconds: float = 30.0,
    ):
        self._validate_local_endpoint(endpoint_url)
        self.endpoint_url = endpoint_url.rstrip("/")
        self.model_name = model_name
        self.context_window = context_window
        self.timeout_seconds = timeout_seconds

    @classmethod
    def _validate_local_endpoint(cls, url: str) -> None:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname or hostname.lower() not in cls.ALLOWED_HOSTS:
            raise ValueError(
                f"Air-gapped security violation: AI inference is strictly local. "
                f"Host '{hostname}' is not a permitted loopback address (127.0.0.1, localhost)."
            )

    def is_available(self) -> bool:
        """Check if local server responds to health or model list check."""
        try:
            req = urllib.request.Request(
                f"{self.endpoint_url}/models",
                headers={"User-Agent": "CIL-Local-AI-Gateway"},
            )
            with urllib.request.urlopen(req, timeout=2.0) as response:
                return response.status == 200
        except Exception:
            return False

    def get_model_info(self) -> ModelInfo:
        available = self.is_available()
        process = psutil.Process()
        ram_mb = process.memory_info().rss / (1024 * 1024)

        return ModelInfo(
            model_id=self.model_name,
            display_name=f"{self.model_name} (Local Server)",
            backend="llama.cpp-http",
            context_window=self.context_window,
            is_loaded=available,
            ram_usage_mb=round(ram_mb, 2),
            gpu_accelerated=False,
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> InferenceResult:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stop": stop or [],
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.endpoint_url}/chat/completions",
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "CIL-Local-AI-Gateway"},
            method="POST",
        )

        start_time = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                elapsed = time.perf_counter() - start_time

                choice = res_data.get("choices", [{}])[0]
                message = choice.get("message", {})
                content = message.get("content", "")
                usage = res_data.get("usage", {})

                return InferenceResult(
                    text=content,
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    latency_seconds=round(elapsed, 4),
                    finish_reason=choice.get("finish_reason", "stop"),
                    raw_response=res_data,
                )
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Failed to connect to local AI server at {self.endpoint_url}: {e}"
            ) from e
