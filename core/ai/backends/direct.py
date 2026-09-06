"""
Direct In-Process GGUF Backend via llama-cpp-python.

Supports CPU-first execution with configurable n_threads, and GPU acceleration
via n_gpu_layers where CUDA/ROCm/Metal hardware acceleration is present.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional
import psutil

from core.ai.backends.base import InferenceResult, LocalInferenceBackend
from core.ai.gateway.base import ModelInfo


class LlamaCppDirectBackend(LocalInferenceBackend):
    """
    Direct in-process GGUF model loader using llama-cpp-python bindings.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        context_window: int = 8192,
        n_gpu_layers: int = 0,
        n_threads: Optional[int] = None,
    ):
        self.model_path = model_path
        self.context_window = context_window
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads or max(os.cpu_count() or 4 - 1, 1)
        self._llm = None
        self._has_llama_cpp = False

        try:
            import llama_cpp
            self._has_llama_cpp = True
        except ImportError:
            self._has_llama_cpp = False

    def is_available(self) -> bool:
        if not self._has_llama_cpp:
            return False
        if not self.model_path or not os.path.exists(self.model_path):
            return False
        return True

    def _ensure_loaded(self) -> None:
        if not self._has_llama_cpp:
            raise RuntimeError(
                "llama-cpp-python is not installed. Direct GGUF loading requires llama-cpp-python."
            )
        if not self.model_path or not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model GGUF file not found: {self.model_path}")

        if self._llm is None:
            import llama_cpp
            self._llm = llama_cpp.Llama(
                model_path=self.model_path,
                n_ctx=self.context_window,
                n_gpu_layers=self.n_gpu_layers,
                n_threads=self.n_threads,
                verbose=False,
            )

    def get_model_info(self) -> ModelInfo:
        loaded = self._llm is not None
        model_name = os.path.basename(self.model_path) if self.model_path else "Unconfigured"

        process = psutil.Process()
        ram_mb = process.memory_info().rss / (1024 * 1024)

        return ModelInfo(
            model_id=model_name,
            display_name=f"{model_name} (llama.cpp direct)",
            backend="llama.cpp-direct",
            context_window=self.context_window,
            is_loaded=loaded,
            ram_usage_mb=round(ram_mb, 2) if loaded else 0.0,
            gpu_accelerated=self.n_gpu_layers > 0,
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
        self._ensure_loaded()
        assert self._llm is not None

        formatted_prompt = prompt
        if system_prompt:
            formatted_prompt = f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant:"

        start_time = time.perf_counter()
        output = self._llm(
            formatted_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop or [],
        )
        elapsed = time.perf_counter() - start_time

        choice = output.get("choices", [{}])[0]
        text = choice.get("text", "")
        usage = output.get("usage", {})

        return InferenceResult(
            text=text,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            latency_seconds=round(elapsed, 4),
            finish_reason=choice.get("finish_reason", "stop"),
            raw_response=output,
        )

    def unload(self) -> None:
        if self._llm is not None:
            del self._llm
            self._llm = None
