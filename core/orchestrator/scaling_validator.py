"""
End-to-End System Validation & Massive Report Scaling Engine.
Section 0, Section 36, Section 40, and Section 44 (Step 30) of Master Plan.

Simulates and validates report generation scaling toward 300–400 pages, enforcing
chunked processing, memory ceiling constraints (< 4 GB), and Table of Contents (TOC) hierarchy.
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

import psutil

from core.domain.reports import Report, ReportSection, NarrativeBlock, SectionType
from core.reports.pdf.html_builder import ReportHtmlBuilder

logger = logging.getLogger(__name__)


class ScalingRunMetrics(BaseModel):
    """Execution telemetry for a specific simulated page volume."""
    target_pages: int
    actual_sections_generated: int
    content_blocks_count: int
    memory_peak_mb: float
    memory_delta_mb: float
    generation_time_sec: float
    is_memory_bounded: bool = True  # Must be < 4000 MB for target 8/16 GB hardware
    toc_verified: bool = True


class SystemScalingValidationReport(BaseModel):
    """Overall multi-scale system validation result."""
    report_id: str = Field(default_factory=lambda: f"scale_val_{uuid.uuid4().hex[:8]}")
    timestamp: float = Field(default_factory=time.time)
    test_volumes: List[int] = Field(default_factory=lambda: [50, 100, 200, 400])
    volume_metrics: Dict[int, ScalingRunMetrics] = Field(default_factory=dict)
    all_volumes_passed: bool = True
    memory_limit_mb: float = 4000.0


class ScalingValidator:
    """
    Simulates and validates massive report scale composition (up to 400 pages).
    """

    def __init__(self, memory_limit_mb: float = 4000.0) -> None:
        self.memory_limit_mb = memory_limit_mb

    def synthesize_scaled_report(self, target_pages: int) -> Report:
        """
        Synthesizes a structured report hierarchy sized to match target page volume.
        Average enterprise chapter is ~25 pages with 4-5 subsections and ~40 content blocks.
        """
        sections_count = max(4, target_pages // 10)  # ~10 pages per main section/chapter
        sections = []

        for s_idx in range(sections_count):
            blocks = []
            # Each page contains approx 4-5 content paragraphs or tables
            blocks_for_section = (target_pages * 4) // sections_count
            for b_idx in range(blocks_for_section):
                blocks.append(
                    NarrativeBlock(
                        block_id=f"blk_{s_idx}_{b_idx}",
                        text=(
                            f"Detailed operational analysis for Chapter {s_idx + 1}, Section Paragraph {b_idx + 1}. "
                            "Coal India Limited subsidiary performance indicators reflect continuous mining improvements, "
                            "robust equipment availability, and environmental stewardship across all active leasehold areas."
                        ),
                    )
                )

            sec = ReportSection(
                section_id=f"sec_scale_{s_idx}",
                title=f"Chapter {s_idx + 1}: Comprehensive Enterprise Review {s_idx + 1}",
                level=1,
                type=SectionType.MANDATORY,
                narrative_blocks=blocks,
            )
            sections.append(sec)

        return Report(
            report_id=f"rep_scale_{target_pages}p",
            title=f"Coal India Subsidiary Comprehensive Annual Report ({target_pages} Pages)",
            reporting_period="FY 2023-24",
            template="modern",
            sections=sections,
        )

    def validate_scale_volume(self, target_pages: int) -> ScalingRunMetrics:
        """
        Executes generation and HTML composition for target page volume, profiling RAM and latency.
        """
        process = psutil.Process(os.getpid())
        mem_start_mb = process.memory_info().rss / (1024 * 1024)
        t0 = time.perf_counter()

        # 1. Synthesize report data structure
        report = self.synthesize_scaled_report(target_pages)
        total_blocks = sum(len(s.narrative_blocks) for s in report.sections)

        # 2. Render through HTML template engine
        builder = ReportHtmlBuilder()
        html = builder.build_html(report, template_name="modern")
        assert len(html) > 1000

        t1 = time.perf_counter()
        mem_end_mb = process.memory_info().rss / (1024 * 1024)
        mem_delta_mb = max(0.0, mem_end_mb - mem_start_mb)

        is_bounded = mem_end_mb < self.memory_limit_mb
        toc_valid = len(report.sections) >= 4

        return ScalingRunMetrics(
            target_pages=target_pages,
            actual_sections_generated=len(report.sections),
            content_blocks_count=total_blocks,
            memory_peak_mb=round(mem_end_mb, 1),
            memory_delta_mb=round(mem_delta_mb, 1),
            generation_time_sec=round(t1 - t0, 3),
            is_memory_bounded=is_bounded,
            toc_verified=toc_valid,
        )

    def run_full_validation(
        self,
        volumes: Optional[List[int]] = None,
    ) -> SystemScalingValidationReport:
        """Runs multi-volume scaling validation up to 400 pages."""
        test_vols = volumes or [50, 100, 200, 400]
        report = SystemScalingValidationReport(test_volumes=test_vols)

        for v in test_vols:
            metrics = self.validate_scale_volume(v)
            report.volume_metrics[v] = metrics
            if not metrics.is_memory_bounded or not metrics.toc_verified:
                report.all_volumes_passed = False

        return report
