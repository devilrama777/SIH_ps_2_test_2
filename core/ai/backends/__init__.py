"""
Local AI Inference Backends.
"""
from core.ai.backends.base import LocalInferenceBackend, InferenceResult
from core.ai.backends.rule_based import RuleBasedLocalBackend
from core.ai.backends.local_server import LocalHttpInferenceBackend
from core.ai.backends.direct import LlamaCppDirectBackend

__all__ = [
    "LocalInferenceBackend",
    "InferenceResult",
    "RuleBasedLocalBackend",
    "LocalHttpInferenceBackend",
    "LlamaCppDirectBackend",
]
