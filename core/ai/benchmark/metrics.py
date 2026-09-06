"""
Evaluation Metrics for Local Model Benchmarking — Section 31 of Master Implementation Plan.

Calculates grounding accuracy, citation presence, hallucination rate, latency,
throughput (tokens/sec), RAM, and CPU metrics.
"""
from typing import List, Optional
from pydantic import BaseModel


class TaskMetrics(BaseModel):
    task_id: str
    task_name: str
    accuracy: float
    grounding_score: float
    hallucination_rate: float
    latency_seconds: float
    tokens_per_second: float
    ram_mb: float
    cpu_percent: float
    gpu_memory_mb: Optional[float] = None
    response_preview: str


class AggregateMetrics(BaseModel):
    model_name: str
    backend: str
    total_tasks: int
    mean_accuracy: float
    mean_grounding: float
    mean_hallucination_rate: float
    avg_latency_seconds: float
    avg_tokens_per_second: float
    peak_ram_mb: float
    avg_cpu_percent: float
    passed: bool


def calculate_grounding_score(response_text: str, expected_citations: List[str]) -> float:
    """Proportion of required provenance citations present in the generated output."""
    if not expected_citations:
        return 1.0
    matched = sum(1 for cite in expected_citations if cite in response_text)
    return round(matched / len(expected_citations), 3)


def calculate_accuracy(response_text: str, ground_truth_facts: List[str]) -> float:
    """Proportion of required factual elements correctly reflected in output."""
    if not ground_truth_facts:
        return 1.0
    text_lower = response_text.lower()
    matched = sum(1 for fact in ground_truth_facts if fact.lower() in text_lower)
    return round(matched / len(ground_truth_facts), 3)


def calculate_hallucination_rate(accuracy: float, grounding: float) -> float:
    """
    Inverse grounding score representing unsupported claims or missing ground truth.
    0.0 represents zero hallucination.
    """
    error = 1.0 - ((accuracy * 0.5) + (grounding * 0.5))
    return round(max(0.0, min(1.0, error)), 3)
