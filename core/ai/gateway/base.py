"""
Local AI Gateway Interface — Section 12 of Master Implementation Specification.

Decouples the report generator from specific local LLM weights/backends.
Operations are model-independent. All underlying inference must be local.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AIResponse(BaseModel):
    """Structured response from local AI gateway."""
    content: str
    model_name: str
    tokens_generated: int = 0
    prompt_tokens: int = 0
    latency_seconds: float = 0.0
    grounding_metadata: Dict[str, Any] = Field(default_factory=dict)
    finish_reason: Optional[str] = None


class ModelInfo(BaseModel):
    """Metadata and capability info for an active or configured local model."""
    model_id: str
    display_name: str
    backend: str  # e.g., 'llama.cpp'
    context_window: int
    is_loaded: bool = False
    ram_usage_mb: Optional[float] = None
    gpu_accelerated: bool = False


class AIGateway(ABC):
    """
    Model-independent gateway for local AI reasoning and narrative generation.
    Enforces local execution: third-party cloud AI APIs are strictly disallowed.
    """

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Return information about the currently active local model."""
        pass

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> AIResponse:
        """Raw completion with structured response."""
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> AIResponse:
        """Multi-turn conversation (e.g. for Agentic Review in Phase 9)."""
        pass

    @abstractmethod
    def summarize(self, evidence_text: str, focus_areas: Optional[List[str]] = None) -> AIResponse:
        """Summarize structured evidence strictly preserving facts and numbers."""
        pass

    @abstractmethod
    def classify(self, text: str, categories: List[str]) -> str:
        """Deterministic or constrained classification of document content."""
        pass

    @abstractmethod
    def extract_semantics(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured JSON matching a specified schema from text."""
        pass

    @abstractmethod
    def plan_report(self, reference_structure: Dict[str, Any], current_evidence_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Propose dynamic report hierarchy and section evidence mappings."""
        pass

    @abstractmethod
    def edit_section(self, section_content: str, evidence_package: Dict[str, Any], instructions: str) -> AIResponse:
        """Agentic revision of an affected section strictly grounded in evidence."""
        pass
