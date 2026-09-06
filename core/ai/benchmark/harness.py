"""
Model Benchmark Harness — Section 31 of Master Implementation Plan.

Executes standardized evaluation tasks across local models and logs factual grounding,
accuracy, hallucination rate, throughput, and hardware resource utilization.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import List, Optional
import psutil

from core.ai.benchmark.metrics import (
    AggregateMetrics,
    TaskMetrics,
    calculate_accuracy,
    calculate_grounding_score,
    calculate_hallucination_rate,
)
from core.ai.benchmark.tasks import BENCHMARK_TASKS, BenchmarkTask
from core.ai.gateway.base import AIGateway


class ModelBenchmarkHarness:
    """
    Executes benchmark evaluations against an active AIGateway.
    Enforces identical evaluation criteria across all candidate local models.
    """

    def __init__(self, gateway: AIGateway, output_dir: str = "data/workspace/benchmarks"):
        self.gateway = gateway
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def run_benchmark(
        self,
        tasks: Optional[List[BenchmarkTask]] = None,
    ) -> AggregateMetrics:
        eval_tasks = tasks or BENCHMARK_TASKS
        task_results: List[TaskMetrics] = []
        process = psutil.Process()

        # Prime CPU percent measurement
        process.cpu_percent(interval=None)

        model_info = self.gateway.get_model_info()

        for task in eval_tasks:
            # Build task prompt with context data
            context_str = json.dumps(task.context_data, indent=2)
            combined_prompt = f"{task.prompt}\n\nContext Data:\n{context_str}"

            # Measure resource usage and latency
            ram_start_mb = process.memory_info().rss / (1024 * 1024)
            start_time = time.perf_counter()

            response = self.gateway.generate(combined_prompt, max_tokens=512)

            elapsed = max(time.perf_counter() - start_time, 0.001)
            cpu_usage = process.cpu_percent(interval=None)
            ram_end_mb = process.memory_info().rss / (1024 * 1024)

            # Evaluate quality and citations
            grounding = calculate_grounding_score(response.content, task.expected_citations)
            accuracy = calculate_accuracy(response.content, task.ground_truth_facts)
            hallucination = calculate_hallucination_rate(accuracy, grounding)

            tokens_generated = response.tokens_generated or max(len(response.content.split()), 1)
            tps = round(tokens_generated / elapsed, 2)

            task_metric = TaskMetrics(
                task_id=task.task_id,
                task_name=task.task_name,
                accuracy=accuracy,
                grounding_score=grounding,
                hallucination_rate=hallucination,
                latency_seconds=round(elapsed, 4),
                tokens_per_second=tps,
                ram_mb=round(ram_end_mb, 2),
                cpu_percent=round(cpu_usage, 2),
                response_preview=response.content[:160].replace("\n", " "),
            )
            task_results.append(task_metric)

        # Compute aggregate metrics
        mean_acc = round(sum(t.accuracy for t in task_results) / len(task_results), 3)
        mean_ground = round(sum(t.grounding_score for t in task_results) / len(task_results), 3)
        mean_halluc = round(sum(t.hallucination_rate for t in task_results) / len(task_results), 3)
        avg_lat = round(sum(t.latency_seconds for t in task_results) / len(task_results), 4)
        avg_tps = round(sum(t.tokens_per_second for t in task_results) / len(task_results), 2)
        peak_ram = max(t.ram_mb for t in task_results)
        avg_cpu = round(sum(t.cpu_percent for t in task_results) / len(task_results), 2)

        passed = mean_ground >= 0.5 and mean_halluc <= 0.5

        aggregate = AggregateMetrics(
            model_name=model_info.model_id,
            backend=model_info.backend,
            total_tasks=len(task_results),
            mean_accuracy=mean_acc,
            mean_grounding=mean_ground,
            mean_hallucination_rate=mean_halluc,
            avg_latency_seconds=avg_lat,
            avg_tokens_per_second=avg_tps,
            peak_ram_mb=peak_ram,
            avg_cpu_percent=avg_cpu,
            passed=passed,
        )

        # Save benchmark log
        self._save_benchmark_artifacts(model_info.model_id, aggregate, task_results)

        return aggregate

    def _save_benchmark_artifacts(
        self,
        model_id: str,
        aggregate: AggregateMetrics,
        tasks: List[TaskMetrics],
    ) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_model = model_id.replace("/", "_").replace("\\", "_")
        json_filename = f"{timestamp}_{safe_model}_benchmark.json"
        json_path = os.path.join(self.output_dir, json_filename)

        data = {
            "timestamp": timestamp,
            "aggregate": aggregate.model_dump(),
            "tasks": [t.model_dump() for t in tasks],
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # Generate markdown summary
        md_filename = f"{timestamp}_{safe_model}_report.md"
        md_path = os.path.join(self.output_dir, md_filename)

        lines = [
            f"# Local AI Model Benchmark Report — {model_id}",
            f"\n**Execution Timestamp**: {timestamp}",
            f"**Backend**: {aggregate.backend}",
            f"**Evaluation Status**: {'PASSED' if aggregate.passed else 'FAILED'}\n",
            "## Summary Metrics",
            "| Metric | Value | Threshold Requirement |",
            "|---|---|---|",
            f"| Mean Accuracy | {aggregate.mean_accuracy * 100:.1f}% | >= 50.0% |",
            f"| Mean Grounding (Citations) | {aggregate.mean_grounding * 100:.1f}% | >= 50.0% |",
            f"| Hallucination Rate | {aggregate.mean_hallucination_rate * 100:.1f}% | <= 50.0% |",
            f"| Avg Latency | {aggregate.avg_latency_seconds:.3f} s | — |",
            f"| Throughput | {aggregate.avg_tokens_per_second:.1f} tokens/s | — |",
            f"| Peak RAM Usage | {aggregate.peak_ram_mb:.1f} MB | <= 8192 MB |",
            f"| Avg CPU Usage | {aggregate.avg_cpu_percent:.1f}% | — |\n",
            "## Task Breakdown",
            "| Task | Grounding | Accuracy | Latency | Tokens/s | RAM (MB) |",
            "|---|---|---|---|---|---|",
        ]

        for t in tasks:
            lines.append(
                f"| {t.task_name} | {t.grounding_score*100:.0f}% | {t.accuracy*100:.0f}% | "
                f"{t.latency_seconds:.3f}s | {t.tokens_per_second:.1f} | {t.ram_mb:.1f} |"
            )

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return json_path
