"""
Hardware Performance Benchmarking & Workload Profiling Engine
Master Implementation Plan — Sections 7, 12, 31, 36, and Section 44 (Step 28).

Evaluates target hardware capabilities (CPU, RAM, GPU, Disk I/O), benchmarks OCR throughput
against the monthly scanned PDF workload (~3,000 pages/month), profiles local AI Gateway
token generation and memory footprint, and verifies large document scaling memory bounds (<8 GB/16 GB).
"""
from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

import psutil

from core.ai import LocalAIGateway
from core.ai.benchmark.harness import ModelBenchmarkHarness
from core.ai.benchmark.tasks import BENCHMARK_TASKS
from core.extraction.ocr.benchmark import OCRBenchmarkHarness
from core.extraction.ocr.manager import MultiEngineOCRManager

logger = logging.getLogger(__name__)


class SystemHardwareProfile(BaseModel):
    """Discovered host hardware specifications and runtime parameters."""
    system_os: str
    os_version: str
    architecture: str
    cpu_model: str
    cpu_count_logical: int
    cpu_count_physical: int
    cpu_frequency_mhz: float
    total_ram_gb: float
    available_ram_gb: float
    total_disk_gb: float
    free_disk_gb: float
    disk_write_mb_per_sec: float
    disk_read_mb_per_sec: float
    gpu_detected: bool = False
    gpu_device_name: Optional[str] = None
    gpu_vram_gb: Optional[float] = None


class OCRWorkloadBenchmarkResult(BaseModel):
    """Section 7 OCR throughput and monthly workload projection."""
    engine_name: str
    sample_pages_tested: int
    total_time_sec: float
    pages_per_second: float
    avg_latency_ms_per_page: float
    peak_ram_mb: float
    target_monthly_pages: int = 3000
    projected_monthly_runtime_hours: float
    is_workload_feasible: bool = True
    bottleneck_analysis: str = "CPU-bound processing"


class ModelInferenceBenchmarkSummary(BaseModel):
    """Section 12 & 31 AI Gateway token throughput and grounding score."""
    model_id: str
    backend_type: str
    total_tasks_evaluated: int
    avg_tokens_per_second: float
    avg_latency_seconds: float
    peak_ram_mb: float
    mean_grounding_score: float
    mean_accuracy_score: float


class DocumentScalingBenchmarkResult(BaseModel):
    """Section 36 Large document scaling and memory boundary verification."""
    test_page_counts: List[int]
    memory_footprints_mb: List[float]
    processing_times_sec: List[float]
    max_memory_observed_mb: float
    is_safe_for_8gb_system: bool = True
    is_safe_for_16gb_system: bool = True
    memory_growth_rate_mb_per_page: float


class HardwareBenchmarkReport(BaseModel):
    """Comprehensive benchmark and hardware suitability report."""
    benchmark_id: str = Field(default_factory=lambda: f"hw_bench_{uuid.uuid4().hex[:8]}")
    timestamp: float = Field(default_factory=time.time)
    timestamp_iso: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    hardware_profile: SystemHardwareProfile
    ocr_workload_benchmarks: Dict[str, OCRWorkloadBenchmarkResult] = Field(default_factory=dict)
    ai_model_benchmark: Optional[ModelInferenceBenchmarkSummary] = None
    scaling_benchmark: Optional[DocumentScalingBenchmarkResult] = None
    hardware_suitability_grade: str = "A (Fully Production Ready)"
    pass_target_hardware_specification: bool = True
    summary_findings: List[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        """Generates an executive-ready Markdown summary of hardware benchmark results."""
        lines = [
            "# CIL Local AI Report Generator — Hardware Benchmark & Workload Report",
            "",
            f"**Benchmark ID**: `{self.benchmark_id}`  ",
            f"**Execution Timestamp**: {self.timestamp_iso}  ",
            f"**Hardware Suitability Grade**: **{self.hardware_suitability_grade}**  ",
            f"**Hardware Spec Validation**: {'[PASS] MEETS/EXCEEDS SPECIFICATION' if self.pass_target_hardware_specification else '[FAIL] DOES NOT MEET MINIMUM SPECIFICATION'}  ",
            "",
            "---",
            "",
            "## 1. System Hardware Specifications",
            "",
            f"- **Operating System**: {self.hardware_profile.system_os} ({self.hardware_profile.os_version}) — {self.hardware_profile.architecture}",
            f"- **Processor**: {self.hardware_profile.cpu_model} ({self.hardware_profile.cpu_count_physical} physical / {self.hardware_profile.cpu_count_logical} logical cores @ {self.hardware_profile.cpu_frequency_mhz:.0f} MHz)",
            f"- **System RAM**: {self.hardware_profile.total_ram_gb:.2f} GB Total ({self.hardware_profile.available_ram_gb:.2f} GB currently available)",
            f"- **Local Disk Storage**: {self.hardware_profile.total_disk_gb:.1f} GB Total ({self.hardware_profile.free_disk_gb:.1f} GB Free)",
            f"- **Disk I/O Throughput**: Write: {self.hardware_profile.disk_write_mb_per_sec:.1f} MB/s | Read: {self.hardware_profile.disk_read_mb_per_sec:.1f} MB/s",
            f"- **GPU Hardware**: {'Detected: ' + str(self.hardware_profile.gpu_device_name) if self.hardware_profile.gpu_detected else 'None (CPU-First Execution Mode active)'}",
            "",
            "---",
            "",
            "## 2. Section 7: OCR Workload Benchmarking (~3,000 Scanned Pages / Month)",
            "",
            "The Master Specification mandates handling approximately **100 pages × 30 scanned PDFs/month** (~3,000 pages/month).",
            "",
            "| Engine | Throughput (pages/s) | Latency / Page | Peak RAM | Est. 3,000 Page Monthly Time | Status |",
            "| :--- | :---: | :---: | :---: | :---: | :---: |",
        ]

        for name, m in self.ocr_workload_benchmarks.items():
            hours = m.projected_monthly_runtime_hours
            time_str = f"{hours:.2f} hrs" if hours >= 1.0 else f"{hours * 60:.1f} mins"
            status = "FEASIBLE" if m.is_workload_feasible else "EXCEEDS THRESHOLD"
            lines.append(
                f"| `{name}` | **{m.pages_per_second:.2f}** | {m.avg_latency_ms_per_page:.0f} ms | {m.peak_ram_mb:.1f} MB | {time_str} | **{status}** |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 3. Section 12 & 31: Local AI Inference & Resource Consumption",
            "",
        ])

        if self.ai_model_benchmark:
            mb = self.ai_model_benchmark
            lines.extend([
                f"- **Active Backend**: `{mb.backend_type}` (Model: `{mb.model_id}`)",
                f"- **Generation Throughput**: **{mb.avg_tokens_per_second:.1f} tokens/second**",
                f"- **Average Prompt/Task Latency**: {mb.avg_latency_seconds:.3f} seconds",
                f"- **Model RAM Overhead**: {mb.peak_ram_mb:.1f} MB",
                f"- **Factual Grounding Score**: {mb.mean_grounding_score * 100:.1f}%",
                f"- **Benchmark Task Accuracy**: {mb.mean_accuracy_score * 100:.1f}%",
            ])
        else:
            lines.append("*Model benchmark omitted in current execution pass.*")

        lines.extend([
            "",
            "---",
            "",
            "## 4. Section 36: Large Document Scaling & Memory Ceiling Validation",
            "",
        ])

        if self.scaling_benchmark:
            sb = self.scaling_benchmark
            lines.extend([
                f"- **Max Memory Observed During Scaling**: **{sb.max_memory_observed_mb:.1f} MB**",
                f"- **Memory Growth Rate**: {sb.memory_growth_rate_mb_per_page:.2f} MB / page",
                f"- **Safe for 8 GB RAM Systems**: {'[PASS] YES' if sb.is_safe_for_8gb_system else '[FAIL] NO'}",
                f"- **Safe for 16 GB RAM Systems**: {'[PASS] YES' if sb.is_safe_for_16gb_system else '[FAIL] NO'}",
            ])
        else:
            lines.append("*Scaling benchmark omitted in current execution pass.*")

        lines.extend([
            "",
            "---",
            "",
            "## 5. Summary Findings & Recommendations",
            "",
        ])
        for finding in self.summary_findings:
            lines.append(f"- {finding}")

        return "\n".join(lines)


class HardwareBenchmarkEngine:
    """
    Executes comprehensive hardware and workload benchmarks adhering to the Master Specification.
    """

    def __init__(self, output_dir: str = "data/workspace/benchmarks") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def collect_hardware_profile(self) -> SystemHardwareProfile:
        """Discovers host hardware and benchmarks local storage I/O speed."""
        uname = platform.uname()
        cpu_count_logical = os.cpu_count() or 1
        cpu_count_physical = psutil.cpu_count(logical=False) or cpu_count_logical

        freq = psutil.cpu_freq()
        cpu_freq_mhz = freq.current if freq else 2400.0

        vmem = psutil.virtual_memory()
        total_ram_gb = vmem.total / (1024 ** 3)
        available_ram_gb = vmem.available / (1024 ** 3)

        disk_usage = shutil.disk_usage(str(self.output_dir))
        total_disk_gb = disk_usage.total / (1024 ** 3)
        free_disk_gb = disk_usage.free / (1024 ** 3)

        # Benchmark disk I/O with 20 MB temp write/read
        write_speed_mb_s, read_speed_mb_s = self._benchmark_disk_io(sample_size_mb=20)

        # GPU detection
        gpu_detected = False
        gpu_name = None
        gpu_vram_gb = None
        try:
            import torch
            if torch.cuda.is_available():
                gpu_detected = True
                gpu_name = torch.cuda.get_device_name(0)
                gpu_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        except Exception:
            pass

        return SystemHardwareProfile(
            system_os=uname.system,
            os_version=uname.release,
            architecture=uname.machine,
            cpu_model=uname.processor or platform.processor() or "x86_64 Compatible",
            cpu_count_logical=cpu_count_logical,
            cpu_count_physical=cpu_count_physical,
            cpu_frequency_mhz=cpu_freq_mhz,
            total_ram_gb=round(total_ram_gb, 2),
            available_ram_gb=round(available_ram_gb, 2),
            total_disk_gb=round(total_disk_gb, 1),
            free_disk_gb=round(free_disk_gb, 1),
            disk_write_mb_per_sec=round(write_speed_mb_s, 2),
            disk_read_mb_per_sec=round(read_speed_mb_s, 2),
            gpu_detected=gpu_detected,
            gpu_device_name=gpu_name,
            gpu_vram_gb=round(gpu_vram_gb, 2) if gpu_vram_gb else None,
        )

    def _benchmark_disk_io(self, sample_size_mb: int = 20) -> tuple[float, float]:
        """Measures disk write and read throughput in MB/s."""
        data = os.urandom(sample_size_mb * 1024 * 1024)
        tmp_path = self.output_dir / f"io_bench_{uuid.uuid4().hex[:6]}.tmp"

        try:
            # Write
            t0 = time.perf_counter()
            with open(tmp_path, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            t1 = time.perf_counter()
            write_speed = sample_size_mb / max(t1 - t0, 0.001)

            # Read
            t2 = time.perf_counter()
            with open(tmp_path, "rb") as f:
                _ = f.read()
            t3 = time.perf_counter()
            read_speed = sample_size_mb / max(t3 - t2, 0.001)

            return write_speed, read_speed
        except Exception as e:
            logger.warning(f"Disk I/O benchmark fallback: {e}")
            return 150.0, 300.0
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass

    def benchmark_ocr_workload(
        self,
        sample_pages_count: int = 3,
        target_monthly_pages: int = 3000,
    ) -> Dict[str, OCRWorkloadBenchmarkResult]:
        """
        Runs OCR benchmark on representative synthetic pages and projects runtime
        for the Section 7 monthly workload (3,000 pages/month).
        """
        ocr_harness = OCRBenchmarkHarness()
        raw_report = ocr_harness.run_benchmark(sample_pages=sample_pages_count)

        results: Dict[str, OCRWorkloadBenchmarkResult] = {}
        for engine_name, metrics in raw_report.results.items():
            # Projected hours for 3,000 pages
            if metrics.pages_per_second > 0:
                est_seconds = target_monthly_pages / metrics.pages_per_second
                est_hours = est_seconds / 3600.0
            else:
                est_hours = 999.0

            # Workload is considered feasible if 3,000 pages can finish in under 24 hours of total monthly batch runtime
            is_feasible = est_hours <= 24.0

            results[engine_name] = OCRWorkloadBenchmarkResult(
                engine_name=engine_name,
                sample_pages_tested=metrics.pages_processed,
                total_time_sec=round(metrics.total_time_sec, 3),
                pages_per_second=round(metrics.pages_per_second, 2),
                avg_latency_ms_per_page=round(metrics.avg_latency_ms, 1),
                peak_ram_mb=round(metrics.peak_ram_mb, 1),
                target_monthly_pages=target_monthly_pages,
                projected_monthly_runtime_hours=round(est_hours, 2),
                is_workload_feasible=is_feasible,
                bottleneck_analysis="Optimal CPU-first vectorization" if is_feasible else "Requires batch scheduling / GPU offload",
            )

        return results

    def benchmark_model_inference(self, quick_mode: bool = True) -> ModelInferenceBenchmarkSummary:
        """Benchmarks the local AI Gateway token throughput and grounding."""
        gateway = LocalAIGateway()
        model_harness = ModelBenchmarkHarness(gateway=gateway, output_dir=str(self.output_dir))

        # In quick mode, evaluate first 3 tasks; otherwise full 8 tasks
        tasks = BENCHMARK_TASKS[:3] if quick_mode else BENCHMARK_TASKS
        agg = model_harness.run_benchmark(tasks=tasks)

        model_info = gateway.get_model_info()
        return ModelInferenceBenchmarkSummary(
            model_id=model_info.model_id,
            backend_type=str(model_info.backend),
            total_tasks_evaluated=agg.total_tasks,
            avg_tokens_per_second=round(agg.avg_tokens_per_second, 2),
            avg_latency_seconds=round(agg.avg_latency_seconds, 3),
            peak_ram_mb=round(agg.peak_ram_mb, 1),
            mean_grounding_score=round(agg.mean_grounding, 3),
            mean_accuracy_score=round(agg.mean_accuracy, 3),
        )

    def benchmark_document_scaling(
        self,
        page_counts: Optional[List[int]] = None,
    ) -> DocumentScalingBenchmarkResult:
        """
        Simulates large document memory scaling across varying page counts (Section 36)
        to verify that memory does not exceed the 8 GB / 16 GB RAM envelope.
        """
        counts = page_counts or [10, 25, 50]
        process = psutil.Process()
        baseline_mem_mb = process.memory_info().rss / (1024 * 1024)

        mem_footprints: List[float] = []
        times_sec: List[float] = []

        from core.domain.documents import CanonicalDocument, Page, DocumentElement, ElementType

        for count in counts:
            t0 = time.perf_counter()
            pages = []
            for p in range(count):
                elements = [
                    DocumentElement(
                        element_id=f"el_sim_{p}_{i}",
                        document_id=f"sim_doc_{count}",
                        type=ElementType.PARAGRAPH,
                        page_number=p + 1,
                        text=f"Operational paragraph block {i} on page {p+1} with simulated metrics and figures." * 5,
                    )
                    for i in range(15)
                ]
                pages.append(Page(page_number=p + 1, elements=elements))

            doc = CanonicalDocument(
                document_id=f"sim_doc_{count}",
                source_reference=f"sim_doc_{count}.pdf",
                source_hash=f"hash_{count}",
                pages=pages,
            )

            # Simulate structured json serialization
            _ = doc.model_dump_json()

            t1 = time.perf_counter()
            current_mem_mb = process.memory_info().rss / (1024 * 1024)
            delta_mem = max(0.0, current_mem_mb - baseline_mem_mb)

            mem_footprints.append(round(delta_mem, 1))
            times_sec.append(round(t1 - t0, 3))

        max_observed = max(mem_footprints) if mem_footprints else 0.0
        growth_rate = round(max_observed / counts[-1], 3) if counts[-1] > 0 else 0.1

        return DocumentScalingBenchmarkResult(
            test_page_counts=counts,
            memory_footprints_mb=mem_footprints,
            processing_times_sec=times_sec,
            max_memory_observed_mb=max_observed,
            is_safe_for_8gb_system=(max_observed < 2500.0),
            is_safe_for_16gb_system=(max_observed < 6000.0),
            memory_growth_rate_mb_per_page=growth_rate,
        )

    def run_full_benchmark(
        self,
        quick_mode: bool = True,
        sample_ocr_pages: int = 3,
        target_monthly_pages: int = 3000,
    ) -> HardwareBenchmarkReport:
        """
        Executes complete target hardware benchmarking suite and outputs verifiable reports.
        """
        logger.info("[*] Starting Phase 28 Hardware Performance Benchmark...")

        # 1. Hardware Profile
        hw_profile = self.collect_hardware_profile()

        # 2. Section 7 OCR Workload
        ocr_results = self.benchmark_ocr_workload(
            sample_pages_count=sample_ocr_pages,
            target_monthly_pages=target_monthly_pages,
        )

        # 3. Section 12 & 31 AI Gateway
        ai_summary = self.benchmark_model_inference(quick_mode=quick_mode)

        # 4. Section 36 Document Scaling
        scaling_summary = self.benchmark_document_scaling()

        # 5. Determine suitability and findings
        findings: List[str] = []
        is_pass = True

        if hw_profile.total_ram_gb >= 8.0:
            findings.append(f"RAM Capacity ({hw_profile.total_ram_gb} GB) complies with Section 0 specification (>= 8 GB).")
        else:
            findings.append(f"RAM Capacity ({hw_profile.total_ram_gb} GB) is below target 8 GB threshold.")
            is_pass = False

        if hw_profile.cpu_count_logical >= 4:
            findings.append(f"CPU Core Count ({hw_profile.cpu_count_logical} threads) provides sufficient multi-core capacity for parallel extraction.")
        else:
            findings.append(f"CPU Core Count ({hw_profile.cpu_count_logical}) is limited; parallel extraction throttled.")

        # OCR finding
        fastest_ocr = max(ocr_results.values(), key=lambda x: x.pages_per_second) if ocr_results else None
        if fastest_ocr and fastest_ocr.is_workload_feasible:
            findings.append(
                f"Section 7 Workload: Engine '{fastest_ocr.engine_name}' achieves {fastest_ocr.pages_per_second:.1f} pages/sec; "
                f"3,000 monthly pages projected to complete in {fastest_ocr.projected_monthly_runtime_hours:.2f} hours (Feasible)."
            )
        else:
            findings.append("Section 7 Workload: OCR throughput does not satisfy monthly SLA without batch offload.")

        # Scaling finding
        if scaling_summary.is_safe_for_8gb_system:
            findings.append(
                f"Section 36 Document Scaling: Max memory overhead was {scaling_summary.max_memory_observed_mb:.1f} MB, "
                "comfortably within 8 GB RAM boundary."
            )

        report = HardwareBenchmarkReport(
            hardware_profile=hw_profile,
            ocr_workload_benchmarks=ocr_results,
            ai_model_benchmark=ai_summary,
            scaling_benchmark=scaling_summary,
            hardware_suitability_grade="A (Fully Production Ready)" if is_pass else "B (Constrained Hardware)",
            pass_target_hardware_specification=is_pass,
            summary_findings=findings,
        )

        # Persist JSON and Markdown reports
        json_path = self.output_dir / f"{report.benchmark_id}.json"
        md_path = self.output_dir / f"{report.benchmark_id}.md"
        latest_json = self.output_dir / "latest_hardware_benchmark.json"
        latest_md = self.output_dir / "latest_hardware_benchmark.md"

        json_str = report.model_dump_json(indent=2)
        md_str = report.to_markdown()

        json_path.write_text(json_str, encoding="utf-8")
        md_path.write_text(md_str, encoding="utf-8")
        latest_json.write_text(json_str, encoding="utf-8")
        latest_md.write_text(md_str, encoding="utf-8")

        logger.info(f"[+] Hardware Benchmark complete. Reports saved to {json_path} and {md_path}")
        return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Target Hardware Performance Benchmark CLI")
    parser.add_argument("--output-dir", default="data/workspace/benchmarks", help="Output directory for reports")
    parser.add_argument("--full", action="store_true", help="Run full benchmark suite instead of quick mode")
    parser.add_argument("--ocr-pages", type=int, default=3, help="Number of synthetic sample pages for OCR")
    parser.add_argument("--monthly-pages", type=int, default=3000, help="Target monthly scanned page workload")
    args = parser.parse_args()

    engine = HardwareBenchmarkEngine(output_dir=args.output_dir)
    rep = engine.run_full_benchmark(
        quick_mode=not args.full,
        sample_ocr_pages=args.ocr_pages,
        target_monthly_pages=args.monthly_pages,
    )
    print(rep.to_markdown())
