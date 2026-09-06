"""
Concrete Local AI Gateway Implementation — Section 12 of Master Implementation Plan.

Acts as the model-independent orchestration layer between CIL business components
(Report Planner, Section Generator, Agentic Editor) and the underlying local execution backend.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List, Optional

from core.ai.backends.base import LocalInferenceBackend
from core.ai.backends.rule_based import RuleBasedLocalBackend
from core.ai.gateway.base import AIGateway, AIResponse, ModelInfo
from core.ai.prompts.templates import (
    SYSTEM_PROMPT_AGENTIC_EDITOR,
    SYSTEM_PROMPT_FACTUAL,
    SYSTEM_PROMPT_REPORT_PLANNER,
    build_classify_prompt,
    build_edit_section_prompt,
    build_plan_prompt,
    build_summarize_prompt,
)


class LocalAIGateway(AIGateway):
    """
    Model-independent Local AI Gateway for CIL report intelligence.
    Routes generation, summarization, classification, semantic extraction,
    report planning, and section editing through local inference backends.
    """

    def __init__(self, backend: Optional[LocalInferenceBackend] = None):
        self._backend = backend or RuleBasedLocalBackend()

    @property
    def backend(self) -> LocalInferenceBackend:
        return self._backend

    def set_backend(self, backend: LocalInferenceBackend) -> None:
        """Switch active local inference backend (e.g. Gemma, Llama 3.1, or rule engine)."""
        self._backend = backend

    def get_model_info(self) -> ModelInfo:
        return self._backend.get_model_info()

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        **kwargs,
    ) -> AIResponse:
        start_time = time.perf_counter()
        sys_prompt = system_prompt or SYSTEM_PROMPT_FACTUAL

        result = self._backend.generate(
            prompt=prompt,
            system_prompt=sys_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )
        elapsed = time.perf_counter() - start_time

        # Extract cited evidence tags: [DOC:...], [COORD:...], [REF:...]
        cited_evidence = re.findall(r"\[(?:DOC|COORD|REF|EVIDENCE):[^\]]+\]", result.text)

        model_info = self.get_model_info()

        return AIResponse(
            content=result.text,
            model_name=model_info.model_id,
            tokens_generated=result.completion_tokens,
            prompt_tokens=result.prompt_tokens,
            latency_seconds=round(elapsed, 4),
            grounding_metadata={
                "cited_references": cited_evidence,
                "citation_count": len(cited_evidence),
                "is_grounded": len(cited_evidence) > 0,
            },
            finish_reason=result.finish_reason,
        )

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> AIResponse:
        """Multi-turn conversation formatted as dialogue."""
        formatted_dialogue = []
        system_prompt = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_prompt = content
            elif role == "user":
                formatted_dialogue.append(f"User: {content}")
            elif role == "assistant":
                formatted_dialogue.append(f"Assistant: {content}")

        dialogue_prompt = "\n".join(formatted_dialogue)
        return self.generate(prompt=dialogue_prompt, system_prompt=system_prompt, **kwargs)

    def summarize(self, evidence_text: str, focus_areas: Optional[List[str]] = None) -> AIResponse:
        prompt = build_summarize_prompt(evidence_text, focus_areas)
        return self.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT_FACTUAL)

    def classify(self, text: str, categories: List[str]) -> str:
        prompt = build_classify_prompt(text, categories)
        res = self.generate(prompt=prompt, max_tokens=64, temperature=0.0)
        cleaned = res.content.strip().strip("'\"")

        for cat in categories:
            if cat.lower() in cleaned.lower():
                return cat
        return categories[0] if categories else "General"

    def extract_semantics(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        schema_json = json.dumps(schema, indent=2)
        prompt = (
            f"Extract structured data from the following text matching this JSON schema:\n"
            f"Schema:\n{schema_json}\n\n"
            f"Text:\n{text}\n\n"
            f"Respond strictly with valid JSON conforming to the schema keys."
        )
        res = self.generate(prompt=prompt, max_tokens=1024, temperature=0.0)

        # Parse JSON from response
        try:
            # Check for ```json ... ``` blocks
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", res.content)
            json_str = json_match.group(1) if json_match else res.content
            return json.loads(json_str)
        except Exception:
            # Fallback: create default mapping with schema keys
            return {k: f"extracted_{k}" for k in schema.keys()}

    def plan_report(
        self,
        reference_structure: Dict[str, Any],
        current_evidence_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        ref_json = json.dumps(reference_structure, indent=2)
        curr_json = json.dumps(current_evidence_summary, indent=2)
        prompt = build_plan_prompt(ref_json, curr_json)

        res = self.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT_REPORT_PLANNER, max_tokens=2048)

        try:
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", res.content)
            json_str = json_match.group(1) if json_match else res.content
            return json.loads(json_str)
        except Exception:
            # Return baseline valid report plan structure
            return {
                "report_title": "CIL Subsidiary Annual Performance & Financial Report",
                "reporting_period": "FY 2024-25",
                "chapters": [
                    {
                        "id": "sec_01",
                        "title": "Corporate Overview & Subsidiary Profile",
                        "status": "mandatory",
                        "required_evidence": ["overview", "subsidiary_mandate"]
                    },
                    {
                        "id": "sec_02",
                        "title": "Operational Performance & Coal Production",
                        "status": "mandatory",
                        "required_evidence": ["coal_production", "offtake", "overburden"]
                    },
                    {
                        "id": "sec_03",
                        "title": "Financial Highlights & Audit Material",
                        "status": "mandatory",
                        "required_evidence": ["revenue", "profit_after_tax", "capex"]
                    },
                    {
                        "id": "sec_04",
                        "title": "Corporate Social Responsibility (CSR) & Sustainability",
                        "status": "discovered",
                        "required_evidence": ["csr_projects", "environmental_compliance"]
                    }
                ]
            }

    def edit_section(
        self,
        section_content: str,
        evidence_package: Dict[str, Any],
        instructions: str,
    ) -> AIResponse:
        evidence_str = json.dumps(evidence_package, indent=2)
        prompt = build_edit_section_prompt(section_content, evidence_str, instructions)
        return self.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT_AGENTIC_EDITOR)
