"""
Local AI Gateway interfaces and implementations.
"""
from core.ai.gateway.base import AIGateway, AIResponse, ModelInfo
from core.ai.gateway.local_gateway import LocalAIGateway

__all__ = [
    "AIGateway",
    "AIResponse",
    "ModelInfo",
    "LocalAIGateway",
]
