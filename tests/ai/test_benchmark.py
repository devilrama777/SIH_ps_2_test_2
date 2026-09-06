"""
Unit and integration tests for ModelBenchmarkHarness and 8 evaluation tasks.
"""
import os
import pytest
from core.ai.benchmark.harness import ModelBenchmarkHarness
from core.ai.benchmark.tasks import BENCHMARK_TASKS
from core.ai.gateway.local_gateway import LocalAIGateway
from core.ai.backends.rule_based import RuleBasedLocalBackend


def test_benchmark_tasks_definition():
    assert len(BENCHMARK_TASKS) == 8
    task_ids = [t.task_id for t in BENCHMARK_TASKS]
    assert "task_1_summarize_evidence" in task_ids
    assert "task_4_interpret_tables" in task_ids
    assert "task_7_follow_provenance" in task_ids
    assert "task_8_generate_report_plan" in task_ids


def test_model_benchmark_harness_execution(tmp_path):
    gateway = LocalAIGateway(RuleBasedLocalBackend())
    harness = ModelBenchmarkHarness(gateway=gateway, output_dir=str(tmp_path))

    aggregate = harness.run_benchmark()

    assert aggregate.total_tasks == 8
    assert aggregate.mean_grounding > 0.0
    assert aggregate.mean_accuracy > 0.0
    assert aggregate.peak_ram_mb > 0.0
    assert aggregate.avg_latency_seconds >= 0.0

    # Verify JSON and Markdown reports are generated
    files = os.listdir(str(tmp_path))
    json_reports = [f for f in files if f.endswith(".json")]
    md_reports = [f for f in files if f.endswith(".md")]

    assert len(json_reports) == 1
    assert len(md_reports) == 1

    with open(os.path.join(str(tmp_path), md_reports[0]), encoding="utf-8") as f:
        md_content = f.read()
        assert "Local AI Model Benchmark Report" in md_content
        assert "Task Breakdown" in md_content
