"""
Master 30-Step Immediate Implementation Order & Dependency Progression Engine.
Section 44 of Master Implementation Specification.

Audits, validates, and certifies the 30-step foundation-first execution DAG:
1. Validates that every preceding step's artifacts and contracts are satisfied before downstream steps proceed.
2. Formally constructs the DAG and proves topological sort compliance and acyclicity.
3. Certifies 100% completion (30/30 steps) of the platform's foundational delivery order.
"""

from __future__ import annotations

import logging
import os
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class StepDefinition:
    """Specification metadata for one of the 30 foundational implementation steps."""
    step_number: int
    title: str
    category: str
    primary_artifact: str
    prerequisites: List[int]
    associated_test: str
    contract_import: Optional[str] = None
    description: str = ""


@dataclass
class StepAuditResult:
    """Evaluation result for an individual implementation step."""
    step_number: int
    title: str
    category: str
    primary_artifact: str
    prerequisites: List[int]
    prerequisites_satisfied: bool
    artifact_exists: bool
    test_exists: bool
    contract_verified: bool
    completed: bool
    latency_ms: float
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ImplementationOrderReport:
    """Master audit report certifying the 30-step implementation order (Section 44)."""
    timestamp: str
    total_steps: int
    completed_steps: int
    completion_pct: float
    topological_order_valid: bool
    all_completed: bool
    specification_section: str
    steps: List[StepAuditResult] = field(default_factory=list)
    topological_sequence: List[int] = field(default_factory=list)
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Authoritative 30-Step DAG definition mandated by Section 44
SECTION_44_STEPS: List[StepDefinition] = [
    StepDefinition(
        step_number=1,
        title="Create repository and architecture docs",
        category="FOUNDATION",
        primary_artifact="docs/architecture/00_overview.md",
        prerequisites=[],
        associated_test="tests/conftest.py",
        description="Bootstrap repository layout and baseline architecture documentation.",
    ),
    StepDefinition(
        step_number=2,
        title="Create Tauri + React desktop shell",
        category="FRONTEND_SHELL",
        primary_artifact="apps/desktop/src/App.tsx",
        prerequisites=[1],
        associated_test="apps/desktop/package.json",
        description="Initialize desktop frontend with React and Tauri configuration.",
    ),
    StepDefinition(
        step_number=3,
        title="Create Python processing service",
        category="BACKEND_SERVICE",
        primary_artifact="apps/processing/server.py",
        prerequisites=[1],
        associated_test="tests/test_health.py",
        description="FastAPI service serving endpoints on localhost:8765.",
    ),
    StepDefinition(
        step_number=4,
        title="Implement LocalFolderConnector",
        category="DATA_INGESTION",
        primary_artifact="core/connectors/local.py",
        prerequisites=[1, 3],
        associated_test="tests/test_connectors.py",
        contract_import="core.connectors.local.LocalFolderConnector",
        description="Air-gapped filesystem connector for raw CIL subsidiary documents.",
    ),
    StepDefinition(
        step_number=5,
        title="Implement ingestion/job system",
        category="DATA_INGESTION",
        primary_artifact="core/ingestion/jobs.py",
        prerequisites=[4],
        associated_test="tests/test_sources_jobs_api.py",
        contract_import="core.ingestion.jobs.IngestionJobManager",
        description="Batch job manager with non-blocking stage execution and progress reporting.",
    ),
    StepDefinition(
        step_number=6,
        title="Implement canonical document model",
        category="EVIDENCE_MODEL",
        primary_artifact="core/domain/documents.py",
        prerequisites=[5],
        associated_test="tests/test_domain_models.py",
        contract_import="core.domain.documents.CanonicalDocument",
        description="Normalized Document/Page/Block/Table hierarchy with bounding boxes.",
    ),
    StepDefinition(
        step_number=7,
        title="Implement PDF/document extraction",
        category="DOCUMENT_EXTRACTION",
        primary_artifact="core/extraction/unified.py",
        prerequisites=[6],
        associated_test="tests/extraction/test_unified_extractor.py",
        contract_import="core.extraction.unified.UnifiedDocumentExtractor",
        description="Multi-format document parsing (DOCX, XLSX, PDF, TXT) via MarkItDown/PyMuPDF.",
    ),
    StepDefinition(
        step_number=8,
        title="Implement OCR/layout/table extraction",
        category="DOCUMENT_EXTRACTION",
        primary_artifact="core/extraction/ocr/manager.py",
        prerequisites=[7],
        associated_test="tests/extraction/test_ocr_engines.py",
        contract_import="core.extraction.ocr.manager.OCRManager",
        description="Multi-engine OCR fallback (Tesseract/Surya/PaddleOCR) for scanned PDFs and tables.",
    ),
    StepDefinition(
        step_number=9,
        title="Implement provenance",
        category="PROVENANCE",
        primary_artifact="core/provenance/tracker.py",
        prerequisites=[6, 7],
        associated_test="tests/validation/test_provenance.py",
        contract_import="core.provenance.tracker.generate_document_id",
        description="Cryptographic SHA-256 snippet hashing and persistent spatial coordinate bindings.",
    ),
    StepDefinition(
        step_number=10,
        title="Implement SQLite + FTS5",
        category="RETRIEVAL_PERSISTENCE",
        primary_artifact="core/retrieval/db.py",
        prerequisites=[6, 9],
        associated_test="tests/retrieval/test_sqlite_fts5.py",
        contract_import="core.retrieval.db.ReportDatabase",
        description="Relational tables and FTS5 full-text search index for air-gapped evidence queries.",
    ),
    StepDefinition(
        step_number=11,
        title="Implement temporal metadata/search",
        category="RETRIEVAL_PERSISTENCE",
        primary_artifact="core/retrieval/temporal_query_engine.py",
        prerequisites=[10],
        associated_test="tests/retrieval/test_temporal_query_engine.py",
        contract_import="core.retrieval.temporal_query_engine.TemporalQueryEngine",
        description="Timeline indexing, fiscal-year bounding, and historical temporal query resolution.",
    ),
    StepDefinition(
        step_number=12,
        title="Implement retrieval",
        category="RETRIEVAL_PERSISTENCE",
        primary_artifact="core/retrieval/search.py",
        prerequisites=[10, 11],
        associated_test="tests/retrieval/test_fts5_temporal_search.py",
        contract_import="core.retrieval.search.HybridSearchEngine",
        description="FTS5 BM25 lexical + temporal query search with spatial provenance filtering.",
    ),
    StepDefinition(
        step_number=13,
        title="Implement AI Gateway",
        category="AI_RUNTIME",
        primary_artifact="core/ai/gateway/base.py",
        prerequisites=[3],
        associated_test="tests/ai/test_gateway.py",
        contract_import="core.ai.gateway.base.AIGateway",
        description="Pluggable provider-neutral gateway for local model inference.",
    ),
    StepDefinition(
        step_number=14,
        title="Integrate local model runtime",
        category="AI_RUNTIME",
        primary_artifact="core/ai/backends/local_server.py",
        prerequisites=[13],
        associated_test="tests/ai/test_backends.py",
        contract_import="core.ai.backends.local_server.LocalInferenceBackend",
        description="Local Ollama/llama.cpp/vLLM runtime integration with CPU/GPU offloading.",
    ),
    StepDefinition(
        step_number=15,
        title="Build model benchmark harness",
        category="AI_RUNTIME",
        primary_artifact="core/ai/benchmark/harness.py",
        prerequisites=[13, 14],
        associated_test="tests/ai/test_benchmark.py",
        contract_import="core.ai.benchmark.harness.ModelBenchmarkHarness",
        description="8-task evaluation benchmark scoring latency, citation accuracy, and hallucination rate.",
    ),
    StepDefinition(
        step_number=16,
        title="Build Report Planner",
        category="REPORT_GENERATION",
        primary_artifact="core/reports/planner/planner.py",
        prerequisites=[12, 13],
        associated_test="tests/reports/test_planner.py",
        contract_import="core.reports.planner.planner.ReportPlanner",
        description="Dynamic topic discovery, reference report structure analysis, and section layout planning.",
    ),
    StepDefinition(
        step_number=17,
        title="Build section generator",
        category="REPORT_GENERATION",
        primary_artifact="core/reports/generator/section_generator.py",
        prerequisites=[13, 16],
        associated_test="tests/reports/test_section_generator.py",
        contract_import="core.reports.generator.section_generator.SectionGenerator",
        description="Evidence-grounded narrative drafting with mandatory inline coordinate citations.",
    ),
    StepDefinition(
        step_number=18,
        title="Build validation engine",
        category="VALIDATION_INTELLIGENCE",
        primary_artifact="core/validation/engine.py",
        prerequisites=[9, 17],
        associated_test="tests/validation/test_engine.py",
        contract_import="core.validation.engine.ValidationEngine",
        description="Multi-dimensional verification checking arithmetic, temporal consistency, and provenance.",
    ),
    StepDefinition(
        step_number=19,
        title="Build image asset pipeline",
        category="IMAGE_INTELLIGENCE",
        primary_artifact="core/reports/image_intelligence.py",
        prerequisites=[8, 17],
        associated_test="tests/reports/test_image_intelligence.py",
        contract_import="core.reports.image_intelligence.ImageAssetAnalyzer",
        description="Visual asset extraction, DPI enhancement, deduplication, and layout placement selection.",
    ),
    StepDefinition(
        step_number=20,
        title="Build Report JSON model",
        category="REPORT_MODEL",
        primary_artifact="core/domain/reports.py",
        prerequisites=[6, 16],
        associated_test="tests/test_domain_models.py",
        contract_import="core.domain.reports.Report",
        description="Renderer-independent intermediate JSON representation for reports and narrative blocks.",
    ),
    StepDefinition(
        step_number=21,
        title="Build HTML/CSS renderer",
        category="RENDERING",
        primary_artifact="core/reports/pdf/html_builder.py",
        prerequisites=[20],
        associated_test="tests/reports/test_pdf_renderer.py",
        contract_import="core.reports.pdf.html_builder.ReportHtmlBuilder",
        description="CSS Paged Media HTML builder with dynamic headers, footers, and page numbers.",
    ),
    StepDefinition(
        step_number=22,
        title="Build classic template",
        category="RENDERING",
        primary_artifact="core/reports/pdf/templates/classic.py",
        prerequisites=[21],
        associated_test="tests/reports/test_pdf_renderer.py",
        description="Formal CIL board-grade template styled with serif typography and traditional layouts.",
    ),
    StepDefinition(
        step_number=23,
        title="Build modern template",
        category="RENDERING",
        primary_artifact="core/reports/pdf/templates/modern.py",
        prerequisites=[21],
        associated_test="tests/reports/test_pdf_renderer.py",
        description="Modern corporate visual mode styled with full-bleed covers and callout cards.",
    ),
    StepDefinition(
        step_number=24,
        title="Build source viewer",
        category="USER_INTERFACE",
        primary_artifact="apps/desktop/src/components/SourceTraceabilityView.tsx",
        prerequisites=[2, 9],
        associated_test="tests/reports/test_traceability.py",
        description="Interactive side-by-side coordinate preview highlighting exact source evidence bounding boxes.",
    ),
    StepDefinition(
        step_number=25,
        title="Build agentic correction system",
        category="AGENTIC_REVIEW",
        primary_artifact="core/reports/agent/editing_agent.py",
        prerequisites=[17, 18],
        associated_test="tests/reports/test_agentic_editing.py",
        contract_import="core.reports.agent.editing_agent.ReportEditingAgent",
        description="Semi-autonomous human+agent conversational review for regenerating deficient sections.",
    ),
    StepDefinition(
        step_number=26,
        title="Add security/audit hardening",
        category="SECURITY",
        primary_artifact="core/security/network_guard.py",
        prerequisites=[3],
        associated_test="tests/security/test_tamper_evident_audit.py",
        contract_import="core.security.network_guard.NetworkSecurityGuard",
        description="Deterministic socket blocker, HMAC-SHA256 audit chaining, and air-gap enforcement.",
    ),
    StepDefinition(
        step_number=27,
        title="Build regression suite",
        category="TESTING",
        primary_artifact="tests/regression/test_golden_dataset_pipeline.py",
        prerequisites=[18, 20, 21],
        associated_test="tests/regression/test_golden_dataset_pipeline.py",
        description="Automated golden dataset pipeline verifying report quality metrics across revisions.",
    ),
    StepDefinition(
        step_number=28,
        title="Benchmark on target hardware",
        category="EVALUATION",
        primary_artifact="core/evaluation/hardware_benchmark.py",
        prerequisites=[15, 27],
        associated_test="tests/evaluation/test_hardware_benchmark.py",
        contract_import="core.evaluation.hardware_benchmark.HardwareBenchmarkEngine",
        description="System profiling verifying memory ceiling (< 4 GB) and CPU throughput on i5-class hardware.",
    ),
    StepDefinition(
        step_number=29,
        title="Build installers",
        category="PACKAGING",
        primary_artifact="installer/build_installers.py",
        prerequisites=[2, 3],
        associated_test="tests/packaging/test_native_installers.py",
        description="Multi-platform bundler generating Windows MSI/NSIS, Linux AppImage/DEB, and macOS DMG packages.",
    ),
    StepDefinition(
        step_number=30,
        title="Run complete end-to-end test",
        category="END_TO_END",
        primary_artifact="core/orchestrator/final_product_vision.py",
        prerequisites=[27, 28, 29],
        associated_test="tests/orchestrator/test_final_product_vision_pipeline.py",
        contract_import="core.orchestrator.final_product_vision.FinalProductVisionPipeline",
        description="12-stage unified turnkey operational demonstration yielding certified publication reports.",
    ),
]


class ImplementationOrderEngine:
    """
    Automated sequential dependency verifier and progression auditor
    for the Section 44 30-step immediate implementation order.
    """

    def __init__(self, workspace_root: Optional[Path | str] = None) -> None:
        if workspace_root is None:
            self.workspace_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.workspace_root = Path(workspace_root).resolve()

        self.step_map: Dict[int, StepDefinition] = {s.step_number: s for s in SECTION_44_STEPS}

    def validate_dependency_dag(self) -> bool:
        """
        Validates that the 30-step dependency graph is a valid Directed Acyclic Graph (DAG)
        with no circular dependencies and strictly forward-moving or valid prerequisite references.
        """
        in_degree: Dict[int, int] = {i: 0 for i in range(1, 31)}
        adjacency: Dict[int, List[int]] = {i: [] for i in range(1, 31)}

        for step in SECTION_44_STEPS:
            for prereq in step.prerequisites:
                if prereq not in self.step_map:
                    return False
                adjacency[prereq].append(step.step_number)
                in_degree[step.step_number] += 1

        queue = deque([node for node, deg in in_degree.items() if deg == 0])
        visited_count = 0

        while queue:
            curr = queue.popleft()
            visited_count += 1
            for neighbor in adjacency[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return visited_count == 30

    def compute_topological_sequence(self) -> List[int]:
        """Returns the canonical topological execution sequence of the 30 steps."""
        in_degree: Dict[int, int] = {i: 0 for i in range(1, 31)}
        adjacency: Dict[int, List[int]] = {i: [] for i in range(1, 31)}

        for step in SECTION_44_STEPS:
            for prereq in step.prerequisites:
                adjacency[prereq].append(step.step_number)
                in_degree[step.step_number] += 1

        queue = deque(sorted([node for node, deg in in_degree.items() if deg == 0]))
        sequence: List[int] = []

        while queue:
            curr = queue.popleft()
            sequence.append(curr)
            for neighbor in adjacency[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return sequence

    def verify_step(self, step_number: int, completed_prior_steps: Optional[Set[int]] = None) -> StepAuditResult:
        """
        Evaluates an individual step's artifact, test file, contract import, and prerequisite compliance.
        """
        t0 = time.perf_counter()
        if step_number not in self.step_map:
            return StepAuditResult(
                step_number=step_number,
                title="Unknown Step",
                category="UNKNOWN",
                primary_artifact="",
                prerequisites=[],
                prerequisites_satisfied=False,
                artifact_exists=False,
                test_exists=False,
                contract_verified=False,
                completed=False,
                latency_ms=0.0,
                details=f"Step #{step_number} is outside the 1..30 specification range.",
            )

        step_def = self.step_map[step_number]
        artifact_path = self.workspace_root / step_def.primary_artifact
        artifact_exists = artifact_path.exists()

        test_path = self.workspace_root / step_def.associated_test
        test_exists = test_path.exists()

        # Prerequisites check
        if completed_prior_steps is not None:
            prereqs_satisfied = all(p in completed_prior_steps for p in step_def.prerequisites)
        else:
            prereqs_satisfied = True

        # Optional contract import verification
        contract_verified = True
        contract_details = ""
        if step_def.contract_import:
            try:
                module_name, class_name = step_def.contract_import.rsplit(".", 1)
                mod = __import__(module_name, fromlist=[class_name])
                cls = getattr(mod, class_name)
                contract_verified = cls is not None
                contract_details = f"Contract '{class_name}' imported successfully."
            except Exception as exc:
                contract_verified = False
                contract_details = f"Contract check error: {exc}"

        completed = artifact_exists and test_exists and contract_verified and prereqs_satisfied
        dt_ms = (time.perf_counter() - t0) * 1000.0

        details = (
            f"Artifact: {step_def.primary_artifact} ({'EXISTS' if artifact_exists else 'MISSING'}); "
            f"Test: {step_def.associated_test} ({'EXISTS' if test_exists else 'MISSING'}). "
            f"{contract_details}"
        )

        return StepAuditResult(
            step_number=step_number,
            title=step_def.title,
            category=step_def.category,
            primary_artifact=step_def.primary_artifact,
            prerequisites=step_def.prerequisites,
            prerequisites_satisfied=prereqs_satisfied,
            artifact_exists=artifact_exists,
            test_exists=test_exists,
            contract_verified=contract_verified,
            completed=completed,
            latency_ms=round(dt_ms, 2),
            details=details,
        )

    def audit_all_steps(self) -> ImplementationOrderReport:
        """
        Audits all 30 steps in topological order, tracking sequential progression
        and verifying that no dependent step executes with unfulfilled prerequisites.
        """
        t_start = time.perf_counter()
        dag_valid = self.validate_dependency_dag()
        topological_seq = self.compute_topological_sequence()

        completed_set: Set[int] = set()
        step_results: List[StepAuditResult] = []

        # Audit following the canonical sequential order (1 through 30)
        for step_num in range(1, 31):
            res = self.verify_step(step_num, completed_prior_steps=completed_set)
            if res.completed:
                completed_set.add(step_num)
            step_results.append(res)

        completed_count = len(completed_set)
        completion_pct = round((completed_count / len(SECTION_44_STEPS)) * 100.0, 1)
        all_completed = (completed_count == len(SECTION_44_STEPS))
        total_time_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

        return ImplementationOrderReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_steps=len(SECTION_44_STEPS),
            completed_steps=completed_count,
            completion_pct=completion_pct,
            topological_order_valid=dag_valid,
            all_completed=all_completed,
            specification_section="Section 44 (Immediate Implementation Order)",
            steps=step_results,
            topological_sequence=topological_seq,
            execution_time_ms=total_time_ms,
        )
