"""
CIL Local AI Gateway and Evaluation Framework.
"""
from core.ai.gateway.base import AIGateway, AIResponse, ModelInfo
from core.ai.gateway.local_gateway import LocalAIGateway
from core.ai.backends.base import LocalInferenceBackend, InferenceResult
from core.ai.backends.rule_based import RuleBasedLocalBackend
from core.ai.backends.local_server import LocalHttpInferenceBackend
from core.ai.backends.direct import LlamaCppDirectBackend
from core.ai.benchmark.harness import ModelBenchmarkHarness

__all__ = [
    "AIGateway",
    "AIResponse",
    "ModelInfo",
    "LocalAIGateway",
    "LocalInferenceBackend",
    "InferenceResult",
    "RuleBasedLocalBackend",
    "LocalHttpInferenceBackend",
    "LlamaCppDirectBackend",
    "ModelBenchmarkHarness",
]
