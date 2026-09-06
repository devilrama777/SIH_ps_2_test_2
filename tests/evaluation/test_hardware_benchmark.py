"""
Unit and Integration Tests for Phase 28: Hardware Performance Benchmarking & Workload Profiling.
Sections 7, 12, 31, 36, and Section 44 (Step 28) of Master Implementation Specification.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.evaluation.hardware_benchmark import (
    HardwareBenchmarkEngine,
    HardwareBenchmarkReport,
    SystemHardwareProfile,
)

client = TestClient(app)


def test_hardware_profile_collection(tmp_path: Path):
    engine = HardwareBenchmarkEngine(output_dir=str(tmp_path))
    profile: SystemHardwareProfile = engine.collect_hardware_profile()

    assert profile.system_os != ""
    assert profile.cpu_count_logical >= 1
    assert profile.total_ram_gb > 0.0
    assert profile.total_disk_gb > 0.0
    assert profile.disk_write_mb_per_sec > 0.0
    assert profile.disk_read_mb_per_sec > 0.0


def test_ocr_workload_benchmarking_projection(tmp_path: Path):
    engine = HardwareBenchmarkEngine(output_dir=str(tmp_path))
    results = engine.benchmark_ocr_workload(sample_pages_count=2, target_monthly_pages=3000)

    assert len(results) >= 1
    for name, res in results.items():
        assert res.sample_pages_tested == 2
        assert res.pages_per_second > 0.0
        assert res.avg_latency_ms_per_page >= 0.0
        assert res.peak_ram_mb > 0.0
        assert res.projected_monthly_runtime_hours >= 0.0
        assert isinstance(res.is_workload_feasible, bool)


def test_document_scaling_memory_bounds(tmp_path: Path):
    engine = HardwareBenchmarkEngine(output_dir=str(tmp_path))
    scaling_res = engine.benchmark_document_scaling(page_counts=[5, 10, 20])

    assert len(scaling_res.test_page_counts) == 3
    assert scaling_res.is_safe_for_8gb_system is True
    assert scaling_res.is_safe_for_16gb_system is True
    assert scaling_res.max_memory_observed_mb < 2500.0


def test_full_hardware_benchmark_report_generation(tmp_path: Path):
    engine = HardwareBenchmarkEngine(output_dir=str(tmp_path))
    report: HardwareBenchmarkReport = engine.run_full_benchmark(
        quick_mode=True,
        sample_ocr_pages=2,
        target_monthly_pages=3000,
    )

    assert report.benchmark_id.startswith("hw_bench_")
    assert report.pass_target_hardware_specification is True
    assert "A" in report.hardware_suitability_grade or "B" in report.hardware_suitability_grade
    assert len(report.summary_findings) >= 2

    # Check generated files on disk
    json_path = tmp_path / f"{report.benchmark_id}.json"
    md_path = tmp_path / f"{report.benchmark_id}.md"
    assert json_path.exists()
    assert md_path.exists()

    md_content = md_path.read_text(encoding="utf-8")
    assert "Hardware Benchmark & Workload Report" in md_content
    assert "Section 7: OCR Workload Benchmarking" in md_content
    assert "Section 36: Large Document Scaling" in md_content


def test_hardware_benchmark_rest_api_lifecycle():
    # 1. Trigger benchmark via POST endpoint
    post_resp = client.post(
        "/api/v1/benchmarks/hardware",
        json={"quick_mode": True, "sample_ocr_pages": 2, "target_monthly_pages": 3000},
    )
    assert post_resp.status_code == 200
    report_data = post_resp.json()
    assert "benchmark_id" in report_data
    assert "hardware_profile" in report_data
    assert "ocr_workload_benchmarks" in report_data
    assert report_data["pass_target_hardware_specification"] is True

    # 2. Fetch latest benchmark via GET endpoint
    get_resp = client.get("/api/v1/benchmarks/hardware/latest")
    assert get_resp.status_code == 200
    latest_data = get_resp.json()
    assert latest_data["benchmark_id"] == report_data["benchmark_id"]
