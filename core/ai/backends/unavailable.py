"""
Unavailable / Offline local AI backend.
Explicitly returns MODEL_UNAVAILABLE state rather than silently fabricating content.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from core.ai.backends.base import LocalInferenceBackend, InferenceResult
from core.ai.gateway.base import ModelInfo


class ModelUnavailableBackend(LocalInferenceBackend):
    """
    Explicit backend representing when no real local AI model (Ollama, llama.cpp, etc.)
    is available or running on the system.
    """

    def __init__(self, message: str = "No local AI model service (Ollama / llama.cpp) detected on loopback."):
        self.message = message

    def is_available(self) -> bool:
        return False

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            model_name="NONE (Model Unavailable)",
            backend="unavailable",
            context_window=0,
            quantization="none",
            device="none",
            is_local=True,
            status="MODEL_UNAVAILABLE",
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
        raise RuntimeError(f"MODEL_UNAVAILABLE: {self.message}")

    def unload(self) -> None:
        pass
