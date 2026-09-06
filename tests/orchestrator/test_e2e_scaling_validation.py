"""
Tests for Phase 30: End-to-End System Validation & 300-400 Page Scaling Simulation.
Section 0, Section 36, Section 40, and Section 44 (Step 30) of Master Implementation Plan.
"""
from __future__ import annotations

import pytest
from core.orchestrator.scaling_validator import ScalingValidator, SystemScalingValidationReport


def test_synthesize_scaled_report():
    validator = ScalingValidator()
    report = validator.synthesize_scaled_report(target_pages=100)

    assert report.report_id == "rep_scale_100p"
    assert len(report.sections) >= 10
    total_blocks = sum(len(s.narrative_blocks) for s in report.sections)
    assert total_blocks >= 350


def test_scaling_volume_execution():
    validator = ScalingValidator(memory_limit_mb=4000.0)
    metrics = validator.validate_scale_volume(target_pages=50)

    assert metrics.target_pages == 50
    assert metrics.actual_sections_generated >= 4
    assert metrics.content_blocks_count >= 150
    assert metrics.is_memory_bounded is True
    assert metrics.toc_verified is True
    assert metrics.generation_time_sec >= 0.0


def test_multi_scale_validation_up_to_400_pages():
    validator = ScalingValidator(memory_limit_mb=4000.0)
    report: SystemScalingValidationReport = validator.run_full_validation(volumes=[50, 100, 200, 400])

    assert len(report.volume_metrics) == 4
    assert 400 in report.volume_metrics
    assert report.all_volumes_passed is True

    metrics_400 = report.volume_metrics[400]
    assert metrics_400.target_pages == 400
    assert metrics_400.content_blocks_count >= 1500
    assert metrics_400.memory_peak_mb < 4000.0  # Safe under 8 GB RAM target
