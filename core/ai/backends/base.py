"""
Inference backend base classes and data transfer models.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.ai.gateway.base import ModelInfo


class InferenceResult(BaseModel):
    """Raw result returned by a local inference backend."""
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_seconds: float = 0.0
    finish_reason: Optional[str] = "stop"
    raw_response: Dict[str, Any] = Field(default_factory=dict)


class LocalInferenceBackend(ABC):
    """
    Abstract interface for offline, local model inference backends.
    All underlying executions must run locally without external cloud API calls.
    """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is installed, configured, and operational."""
        pass

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Retrieve model metadata, context window size, and resource status."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> InferenceResult:
        """Execute text generation locally."""
        pass

    def unload(self) -> None:
        """Release allocated CPU/GPU memory."""
        pass
