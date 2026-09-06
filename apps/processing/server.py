"""
FastAPI Local Processing Server — Section 25 & Section 39 (Phase 0).

Provides local HTTP/REST endpoints for health checks, system diagnostics,
and orchestrating document intelligence tasks for the desktop shell.
"""
from __future__ import annotations

import base64
import json
import platform
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uuid

import psutil
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from apps.processing.config import settings
from apps.processing.logging_config import setup_logging
from core.domain.jobs import ProcessingJob
from core.ingestion.discovery import DiscoveredFile, discover_files
from core.ingestion.jobs import IngestionJobManager

logger = setup_logging(settings.log_level)
START_TIME = time.time()
job_manager = IngestionJobManager()

from core.security.models import AuditEventType, AuditLogEntry
from core.security.audit_logger import AuditLogger
from core.security.credentials import SecureCredentialVault
from core.security.network_guard import NetworkSecurityGuard

audit_logger = AuditLogger(db_path="data/workspace/audit_log.db")
credential_vault = SecureCredentialVault(vault_path="data/workspace/vault.bin")

from core.settings import SettingsManager
from core.domain.settings import ApplicationSettings, SubsidiaryProfile
from core.orchestrator.vertical_slice import VerticalSliceConfig, VerticalSliceResult, VerticalSliceRunner
from core.extraction.normalizer import DocumentNormalizer
from core.extraction.ocr.manager import MultiEngineOCRManager
from core.extraction.ocr.benchmark import OCRBenchmarkHarness, OCRBenchmarkReport
from core.extraction.ocr.base import OCRPageResult, OCRHealth
from core.orchestrator.report_job import ReportJobManager, ReportJobConfig, ReportJobState, ReportJobStatus
from core.reports.image_intelligence import (
    ImageAsset,
    ImageAssetAnalyzer,
    ImageAssetCatalog,
    DeterministicLayoutEngine,
    LayoutType,
    ImageTopic,
    SectionImagePresentation,
)
from core.reports.agent.editing_agent import ReportEditingAgent, EditProposal
from core.evaluation.metrics import ReportQualityEvaluator, ReportQualityMetrics
from core.reports.incremental_engine import SectionDependencyGraph
from core.reports.planner.reference_analyzer import (
    ComparativeReportAnalyzer,
    StructuralChangeReport,
    YoYComparativeTable,
)

settings_manager = SettingsManager(config_path="data/workspace/app_settings.json")
vertical_slice_runner = VerticalSliceRunner(workspace_dir="data/workspace")
document_normalizer = DocumentNormalizer(output_dir="data/workspace/normalized")
ocr_manager = MultiEngineOCRManager()
ocr_benchmark = OCRBenchmarkHarness(ocr_manager=ocr_manager)
report_job_manager = ReportJobManager(workspace_dir="data/workspace")
image_catalog = ImageAssetCatalog(db_path="data/workspace/image_assets.db")
editing_agent = ReportEditingAgent(
    reports_dir="data/workspace/reports",
    proposals_dir="data/workspace/proposals",
)
quality_evaluator = ReportQualityEvaluator()
comparative_analyzer = ComparativeReportAnalyzer()

from core.storage.lifecycle import StorageManager, ArtifactCategory, format_bytes
from core.reports.incremental_engine import SectionDependencyGraph

storage_manager = StorageManager(workspace_dir=str(settings.workspace_root))



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for service startup and shutdown."""
    settings.ensure_directories()
    logger.info("CIL Local AI Processing Service started on %s:%d", settings.host, settings.port)
    logger.info("Operating in strictly local mode (allow_external_network=%s)", settings.allow_external_network)
    yield
    logger.info("CIL Local AI Processing Service shutting down")


app = FastAPI(
    title="CIL Local AI Processing Service",
    description="Local-first document intelligence and report generation processing service.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS restricted to local desktop application
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    uptime_seconds: float
    timestamp: str
    environment: str


class DiagnosticsResponse(BaseModel):
    platform: str
    python_version: str
    cpu_count_logical: int
    cpu_count_physical: int
    cpu_usage_percent: float
    memory_total_gb: float
    memory_available_gb: float
    memory_used_percent: float
    disk_total_gb: float
    disk_free_gb: float
    disk_used_percent: float


class ScanFolderRequest(BaseModel):
    folder_path: str


class ScanFolderResponse(BaseModel):
    folder_path: str
    total_files: int
    total_size_mb: float
    format_distribution: Dict[str, int]
    financial_years: List[str]
    files: List[DiscoveredFile]


class IngestJobRequest(BaseModel):
    folder_path: str


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Service liveness and health check."""
    return HealthResponse(
        status="ok",
        service="cil-report-ai-processing",
        version="0.1.0",
        uptime_seconds=round(time.time() - START_TIME, 2),
        timestamp=datetime.utcnow().isoformat() + "Z",
        environment=settings.environment,
    )


@app.get("/api/v1/diagnostics", response_model=DiagnosticsResponse)
async def system_diagnostics() -> DiagnosticsResponse:
    """Hardware capability and resource consumption diagnostics."""
    try:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(str(settings.workspace_root.resolve()))
        return DiagnosticsResponse(
            platform=f"{platform.system()} {platform.release()} ({platform.machine()})",
            python_version=sys.version.split()[0],
            cpu_count_logical=psutil.cpu_count(logical=True) or 0,
            cpu_count_physical=psutil.cpu_count(logical=False) or 0,
            cpu_usage_percent=psutil.cpu_percent(interval=0.1),
            memory_total_gb=round(mem.total / (1024**3), 2),
            memory_available_gb=round(mem.available / (1024**3), 2),
            memory_used_percent=mem.percent,
            disk_total_gb=round(disk.total / (1024**3), 2),
            disk_free_gb=round(disk.free / (1024**3), 2),
            disk_used_percent=disk.percent,
        )
    except Exception as exc:
        logger.error("Failed to retrieve diagnostics: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error collecting system diagnostics",
        )


@app.get("/api/v1/system/info")
async def system_info() -> Dict[str, Any]:
    """System configuration status."""
    return {
        "service": "cil-report-ai-processing",
        "version": "0.1.0",
        "local_only": not settings.allow_external_network,
        "workspace_root": str(settings.workspace_root.resolve()),
        "cache_dir": str(settings.cache_dir.resolve()),
        "index_dir": str(settings.index_dir.resolve()),
        "allowed_origins": settings.allowed_origins,
    }


@app.post("/api/v1/sources/scan", response_model=ScanFolderResponse)
async def scan_folder(req: ScanFolderRequest) -> ScanFolderResponse:
    """Scan a local directory, enforcing path validity and returning format & temporal distribution."""
    target_path = Path(req.folder_path).resolve()
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target directory does not exist or is not a directory: {req.folder_path}",
        )

    try:
        discovered = discover_files(target_path, compute_hashes=False)
        format_dist: Dict[str, int] = {}
        fy_set = set()
        total_bytes = 0

        for f in discovered:
            fmt_str = f.format.value
            format_dist[fmt_str] = format_dist.get(fmt_str, 0) + 1
            total_bytes += f.file_size_bytes
            if f.temporal.financial_year:
                fy_set.add(f.temporal.financial_year)

        return ScanFolderResponse(
            folder_path=str(target_path),
            total_files=len(discovered),
            total_size_mb=round(total_bytes / (1024 * 1024), 2),
            format_distribution=format_dist,
            financial_years=sorted(list(fy_set)),
            files=discovered[:100],  # Return up to first 100 files for fast preview
        )
    except Exception as exc:
        logger.error("Error during folder scan: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scanning folder: {str(exc)}",
        )


@app.post("/api/v1/jobs/ingest", response_model=ProcessingJob)
async def start_ingest_job(req: IngestJobRequest) -> ProcessingJob:
    """Start an observable and resumable ingestion job on a local folder."""
    target_path = Path(req.folder_path).resolve()
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target directory does not exist: {req.folder_path}",
        )

    job = job_manager.create_job(source_path=str(target_path), job_type="ingest_folder")

    # In Phase 1 local prototype, run pipeline (synchronously or background thread)
    # The pipeline is fully resumable and observable
    import threading
    thread = threading.Thread(target=job_manager.run_ingestion_pipeline, args=(job.job_id,), daemon=True)
    thread.start()

    return job


@app.get("/api/v1/jobs/{job_id}", response_model=ProcessingJob)
async def get_job_status(job_id: str) -> ProcessingJob:
    """Poll the status, progress, stage, and errors of a processing job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found")
    return job


@app.get("/api/v1/jobs", response_model=List[ProcessingJob])
async def list_recent_jobs() -> List[ProcessingJob]:
    """List recent background processing jobs."""
    return job_manager.list_jobs(limit=20)


@app.post("/api/v1/jobs/{job_id}/cancel")
async def cancel_job(job_id: str) -> Dict[str, str]:
    """Cancel an active processing job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found")
    job_manager.cancel_job(job_id)
    return {"status": "cancelled", "job_id": job_id}


class StartReportJobRequest(BaseModel):
    source_folder: Optional[str] = None
    subsidiary_code: str = "CCL"
    reporting_period: str = "FY 2023-24"
    template_style: str = "modern"
    reference_report_path: Optional[str] = None
    run_sync: bool = False


@app.post("/api/v1/report-jobs/start", response_model=ReportJobState)
async def start_report_generation_job(
    req: StartReportJobRequest,
    background_tasks: BackgroundTasks,
) -> ReportJobState:
    """Launch a unified 12-stage resumable report generation job (Section 27)."""
    cfg = ReportJobConfig(
        source_folder=req.source_folder,
        subsidiary_code=req.subsidiary_code,
        reporting_period=req.reporting_period,
        template_style=req.template_style,
        reference_report_path=req.reference_report_path,
    )
    state = report_job_manager.create_job(cfg)
    if req.run_sync:
        state = report_job_manager.execute_job_stages(state)
        return state
    else:
        background_tasks.add_task(report_job_manager.execute_job_stages, state)
        return state


@app.get("/api/v1/report-jobs", response_model=List[ReportJobState])
async def list_report_generation_jobs() -> List[ReportJobState]:
    """List all 12-stage report generation jobs."""
    return report_job_manager.list_jobs()


@app.get("/api/v1/report-jobs/{job_id}", response_model=ReportJobState)
async def get_report_generation_job_status(job_id: str) -> ReportJobState:
    """Retrieve live 12-stage progress, timings, and checkpoints for a report job."""
    job = report_job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report job {job_id} not found")
    return job


@app.post("/api/v1/report-jobs/{job_id}/pause", response_model=ReportJobState)
async def pause_report_generation_job(job_id: str) -> ReportJobState:
    """Pause an active report generation job safely after its active stage."""
    job = report_job_manager.pause_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report job {job_id} not found")
    return job


@app.post("/api/v1/report-jobs/{job_id}/resume", response_model=ReportJobState)
async def resume_report_generation_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    run_sync: bool = False,
) -> ReportJobState:
    """Resume a paused report generation job from its latest stage checkpoint."""
    job = report_job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report job {job_id} not found")
    if run_sync:
        return report_job_manager.resume_job(job_id) or job
    else:
        background_tasks.add_task(report_job_manager.resume_job, job_id)
        job.status = ReportJobStatus.RUNNING
        return job


@app.post("/api/v1/report-jobs/{job_id}/cancel", response_model=ReportJobState)
async def cancel_report_generation_job(job_id: str) -> ReportJobState:
    """Cancel an active report generation job."""
    job = report_job_manager.cancel_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report job {job_id} not found")
    return job


from core.retrieval.search import HybridSearchEngine, RankedEvidence, SearchQuery
search_engine = HybridSearchEngine()


@app.post("/api/v1/evidence/search", response_model=List[RankedEvidence])
async def search_evidence(query: SearchQuery) -> List[RankedEvidence]:
    """Execute hybrid FTS5 BM25 search with temporal and document filters."""
    try:
        return search_engine.search(query)
    except Exception as exc:
        logger.error("Error executing evidence search: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing search: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# Phase 4: Local AI Gateway & Benchmark Endpoints (Section 12 & 31)
# ---------------------------------------------------------------------------
from core.ai.gateway.base import AIResponse, ModelInfo
from core.ai.gateway.local_gateway import LocalAIGateway
from core.ai.backends.base import LocalInferenceBackend
from core.ai.backends.rule_based import RuleBasedLocalBackend
from core.ai.backends.local_server import LocalHttpInferenceBackend
from core.ai.backends.direct import LlamaCppDirectBackend
from core.ai.benchmark.harness import ModelBenchmarkHarness
from core.ai.benchmark.metrics import AggregateMetrics

ai_gateway = LocalAIGateway(RuleBasedLocalBackend())


class AIGenerateRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: int = 1024
    temperature: float = 0.2


class AISummarizeRequest(BaseModel):
    evidence_text: str
    focus_areas: Optional[List[str]] = None


class AISelectBackendRequest(BaseModel):
    backend_type: str  # 'deterministic-local', 'llama.cpp-http', 'llama.cpp-direct'
    endpoint_url: Optional[str] = None
    model_name: Optional[str] = None
    model_path: Optional[str] = None


AIGenerateRequest.model_rebuild()
AISummarizeRequest.model_rebuild()
AISelectBackendRequest.model_rebuild()


@app.get("/api/v1/ai/models", response_model=Dict[str, Any])
async def get_ai_models() -> Dict[str, Any]:
    """Retrieve active local model status and available backends."""
    active_info = ai_gateway.get_model_info()
    return {
        "active_model": active_info.model_dump(),
        "available_backends": [
            {
                "type": "deterministic-local",
                "name": "Local Rule-Based & Factual Verification Engine",
                "status": "active" if active_info.backend == "deterministic-local" else "available",
                "description": "Zero-dependency air-gapped deterministic reasoning, citation provenance, and fact checks.",
            },
            {
                "type": "llama.cpp-http",
                "name": "Local llama.cpp Server / Ollama",
                "status": "active" if active_info.backend == "llama.cpp-http" else "available",
                "description": "Connects to air-gapped local port (127.0.0.1:8080 or 127.0.0.1:11434).",
            },
            {
                "type": "llama.cpp-direct",
                "name": "Direct In-Process GGUF Loader",
                "status": "active" if active_info.backend == "llama.cpp-direct" else "available",
                "description": "In-process CPU/GPU GGUF execution via llama-cpp-python.",
            },
        ],
    }


@app.post("/api/v1/ai/backend/select", response_model=ModelInfo)
async def select_ai_backend(req: AISelectBackendRequest) -> ModelInfo:
    """Switch active local inference backend (strictly air-gapped)."""
    try:
        if req.backend_type == "deterministic-local":
            backend = RuleBasedLocalBackend()
        elif req.backend_type == "llama.cpp-http":
            url = req.endpoint_url or "http://127.0.0.1:8080/v1"
            name = req.model_name or "gemma-2-9b-it"
            backend = LocalHttpInferenceBackend(endpoint_url=url, model_name=name)
        elif req.backend_type == "llama.cpp-direct":
            backend = LlamaCppDirectBackend(model_path=req.model_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown backend type: {req.backend_type}",
            )

        ai_gateway.set_backend(backend)
        return ai_gateway.get_model_info()
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to switch AI backend: {str(exc)}",
        )


@app.post("/api/v1/ai/generate", response_model=AIResponse)
async def ai_generate(req: AIGenerateRequest) -> AIResponse:
    """Execute raw text completion with provenance citation extraction."""
    try:
        return ai_gateway.generate(
            prompt=req.prompt,
            system_prompt=req.system_prompt,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        )
    except Exception as exc:
        logger.error("AI generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(exc)}",
        )


@app.post("/api/v1/ai/summarize", response_model=AIResponse)
async def ai_summarize(req: AISummarizeRequest) -> AIResponse:
    """Summarize structured evidence strictly preserving facts, figures, and citations."""
    try:
        return ai_gateway.summarize(
            evidence_text=req.evidence_text,
            focus_areas=req.focus_areas,
        )
    except Exception as exc:
        logger.error("AI summarization failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(exc)}",
        )


@app.post("/api/v1/ai/benchmark", response_model=AggregateMetrics)
async def run_ai_benchmark() -> AggregateMetrics:
    """Run standardized 8-task benchmark harness on the active local AI model."""
    try:
        harness = ModelBenchmarkHarness(gateway=ai_gateway)
        return harness.run_benchmark()
    except Exception as exc:
        logger.error("Benchmark run failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Benchmark execution failed: {str(exc)}",
        )


@app.get("/api/v1/ai/benchmarks", response_model=List[Dict[str, Any]])
async def list_ai_benchmarks() -> List[Dict[str, Any]]:
    """List historical benchmark evaluation runs."""
    benchmark_dir = Path("data/workspace/benchmarks")
    if not benchmark_dir.exists():
        return []

    results = []
    for p in sorted(benchmark_dir.glob("*_benchmark.json"), reverse=True)[:20]:
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                results.append({
                    "filename": p.name,
                    "timestamp": data.get("timestamp"),
                    "aggregate": data.get("aggregate"),
                })
        except Exception:
            continue
    return results


# ---------------------------------------------------------------------------
# Phase 5: Report Planner Endpoints (Sections 13, 14, 15)
# ---------------------------------------------------------------------------
from core.reports.planner import ReportPlanner, ReportPlan, EvidenceToSectionMapper
from core.domain.documents import CanonicalDocument

report_planner = ReportPlanner(evidence_mapper=EvidenceToSectionMapper(search_engine=search_engine))


class PlanReportRequest(BaseModel):
    report_title: str = "Annual Performance & Accountability Report"
    reporting_period: str = "FY 2024-25"
    subsidiary_name: str = "Coal India Limited Subsidiary"
    template_name: str = "modern"
    reference_document_id: Optional[str] = None
    attach_evidence: bool = True


PlanReportRequest.model_rebuild()


@app.post("/api/v1/reports/plan", response_model=ReportPlan)
async def create_report_plan(req: PlanReportRequest) -> ReportPlan:
    """Generate a structured, dynamic report plan based on evidence and reference analysis."""
    try:
        # Load evidence corpus from indexed canonical documents
        corpus: List[Dict[str, Any]] = []
        canonical_dir = Path("data/workspace/canonical_documents")
        if canonical_dir.exists():
            for p in canonical_dir.glob("*.json"):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        cdoc = json.load(f)
                        for page in cdoc.get("pages", []):
                            for elem in page.get("elements", []):
                                if elem.get("text"):
                                    corpus.append({
                                        "id": elem.get("element_id"),
                                        "text": elem.get("text"),
                                        "document_id": cdoc.get("document_id"),
                                    })
                except Exception:
                    continue

        # If corpus is empty, provide default operational baseline items
        if not corpus:
            corpus = [
                {"id": "base_1", "text": "Raw coal production reached 773.60 MT with rapid loading and first mile connectivity (FMC)."},
                {"id": "base_2", "text": "Commissioned 50 MW solar power plant for renewable energy transition."},
                {"id": "base_3", "text": "Completed SAP ERP digital mine telemetry and drone survey fleet deployment."},
            ]

        # Check for reference document if specified
        ref_doc: Optional[CanonicalDocument] = None
        if req.reference_document_id and canonical_dir.exists():
            ref_path = canonical_dir / f"{req.reference_document_id}.json"
            if ref_path.exists():
                try:
                    with open(ref_path, "r", encoding="utf-8") as f:
                        ref_doc = CanonicalDocument.model_validate_json(f.read())
                except Exception as exc:
                    logger.warning("Could not parse reference document: %s", exc)

        plan = report_planner.generate_plan(
            current_evidence_corpus=corpus,
            reference_document=ref_doc,
            report_title=req.report_title,
            reporting_period=req.reporting_period,
            subsidiary_name=req.subsidiary_name,
            template_name=req.template_name,
            attach_evidence=req.attach_evidence,
        )

        # Persist plan to disk
        plans_dir = Path("data/workspace/report_plans")
        plans_dir.mkdir(parents=True, exist_ok=True)
        with open(plans_dir / f"{plan.plan_id}.json", "w", encoding="utf-8") as f:
            f.write(plan.model_dump_json(indent=2))

        return plan
    except Exception as exc:
        logger.error("Failed to generate report plan: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report planning failed: {str(exc)}",
        )


@app.get("/api/v1/reports/plans", response_model=List[Dict[str, Any]])
async def list_report_plans() -> List[Dict[str, Any]]:
    """List historical report plans."""
    plans_dir = Path("data/workspace/report_plans")
    if not plans_dir.exists():
        return []

    plans = []
    for p in sorted(plans_dir.glob("*.json"), reverse=True):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                plans.append({
                    "plan_id": data.get("plan_id"),
                    "report_title": data.get("report_title"),
                    "reporting_period": data.get("reporting_period"),
                    "subsidiary_name": data.get("subsidiary_name"),
                    "template_name": data.get("template_name"),
                    "total_planned_sections": data.get("total_planned_sections"),
                    "created_at": data.get("created_at"),
                })
        except Exception:
            continue
    return plans


@app.get("/api/v1/reports/plans/{plan_id}", response_model=ReportPlan)
async def get_report_plan(plan_id: str) -> ReportPlan:
    """Retrieve full details of a specific report plan."""
    plan_path = Path("data/workspace/report_plans") / f"{plan_id}.json"
    if not plan_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan {plan_id} not found")

    with open(plan_path, "r", encoding="utf-8") as f:
        return ReportPlan.model_validate_json(f.read())


# ---------------------------------------------------------------------------
# Phase 6: Content Generation & Validation Engine Endpoints (Sections 16, 17)
# ---------------------------------------------------------------------------
from core.reports.generator.report_generator import MasterReportGenerator
from core.reports.generator.section_generator import SectionGenerator
from core.validation.engine import ValidationEngine, ValidationReport
from core.domain.reports import Report

validation_engine = ValidationEngine()
report_generator = MasterReportGenerator(
    section_generator=SectionGenerator(ai_gateway=ai_gateway),
    validation_engine=validation_engine,
    output_dir="data/workspace/reports",
)


class GenerateReportRequest(BaseModel):
    plan_id: str


GenerateReportRequest.model_rebuild()


@app.post("/api/v1/reports/generate", response_model=Dict[str, Any])
async def generate_report(req: GenerateReportRequest) -> Dict[str, Any]:
    """Generate a complete verified report from an approved ReportPlan."""
    plan_path = Path("data/workspace/report_plans") / f"{req.plan_id}.json"
    if not plan_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan {req.plan_id} not found")

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = ReportPlan.model_validate_json(f.read())

    try:
        report, val_report = report_generator.generate_report(plan)
        audit_logger.log_event(
            event_type=AuditEventType.REPORT_CREATED,
            action="generate_report",
            resource_id=report.report_id,
            details={
                "title": report.title,
                "sections": len(report.sections),
                "validation": val_report.overall_status.value,
            },
        )
        return {
            "report_id": report.report_id,
            "title": report.title,
            "reporting_period": report.reporting_period,
            "total_sections": len(report.sections),
            "validation": {
                "overall_status": val_report.overall_status.value,
                "passed": val_report.passed,
                "total_issues": val_report.total_issues,
                "error_count": val_report.error_count,
                "warning_count": val_report.warning_count,
            },
        }
    except Exception as exc:
        logger.error("Report generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(exc)}",
        )


@app.get("/api/v1/reports", response_model=List[Dict[str, Any]])
async def list_reports() -> List[Dict[str, Any]]:
    """List all generated corporate reports."""
    reports_dir = Path("data/workspace/reports")
    if not reports_dir.exists():
        return []

    reports = []
    for p in sorted(reports_dir.glob("*.json")):
        if p.name.endswith("_validation.json"):
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                reports.append({
                    "report_id": data.get("report_id"),
                    "title": data.get("title"),
                    "reporting_period": data.get("reporting_period"),
                    "subsidiary_name": data.get("subsidiary_name"),
                    "template_name": data.get("template_name"),
                    "total_sections": len(data.get("sections", [])),
                    "created_at": data.get("created_at"),
                })
        except Exception:
            continue
    return reports


@app.get("/api/v1/reports/{report_id}", response_model=Report)
async def get_report(report_id: str) -> Report:
    """Retrieve full generated report document structure."""
    rep_path = Path("data/workspace/reports") / f"{report_id}.json"
    if not rep_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found")

    with open(rep_path, "r", encoding="utf-8") as f:
        return Report.model_validate_json(f.read())


@app.get("/api/v1/reports/{report_id}/validation", response_model=ValidationReport)
async def get_report_validation(report_id: str) -> ValidationReport:
    """Retrieve validation findings and audit issues for a report."""
    val_path = Path("data/workspace/reports") / f"{report_id}_validation.json"
    if not val_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Validation report for {report_id} not found")

    with open(val_path, "r", encoding="utf-8") as f:
        return ValidationReport.model_validate_json(f.read())


@app.post("/api/v1/reports/{report_id}/validate", response_model=ValidationReport)
async def revalidate_report(report_id: str) -> ValidationReport:
    """Re-run deterministic validation checks on an existing report."""
    rep_path = Path("data/workspace/reports") / f"{report_id}.json"
    if not rep_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found")

    with open(rep_path, "r", encoding="utf-8") as f:
        report = Report.model_validate_json(f.read())

    val_report = validation_engine.validate_report(report)

    # Save updated validation findings
    val_path = Path("data/workspace/reports") / f"{report_id}_validation.json"
    with open(val_path, "w", encoding="utf-8") as f:
        f.write(val_report.model_dump_json(indent=2))

    return val_report


# ---------------------------------------------------------------------------
# Phase 7: Image Intelligence Endpoints (Section 18)
# ---------------------------------------------------------------------------
from core.assets.catalog import ImageAssetCatalog
from core.assets.models import ImageAsset, ImageAssetAssignment, ImageLayoutType

asset_catalog = ImageAssetCatalog(db_path="data/workspace/assets.db")


class RegisterImageRequest(BaseModel):
    file_path: str
    source_document_id: Optional[str] = None
    page_number: Optional[int] = None
    provenance_id: Optional[str] = None


class AssignImageRequest(BaseModel):
    section_id: str
    asset_id: str
    layout_type: Optional[ImageLayoutType] = None
    caption: Optional[str] = None
    display_order: int = 1
    width_percentage: int = 100


RegisterImageRequest.model_rebuild()
AssignImageRequest.model_rebuild()


@app.get("/api/v1/assets", response_model=List[ImageAsset])
async def list_assets(
    tag: Optional[str] = None,
    include_duplicates: bool = False,
) -> List[ImageAsset]:
    """List cataloged image assets with optional tag and deduplication filters."""
    return asset_catalog.list_assets(tag=tag, include_duplicates=include_duplicates)


@app.post("/api/v1/assets/register", response_model=ImageAsset)
async def register_asset(req: RegisterImageRequest) -> ImageAsset:
    """Register and analyze an image file into the image intelligence catalog."""
    try:
        return asset_catalog.register_image(
            file_path=req.file_path,
            source_document_id=req.source_document_id,
            page_number=req.page_number,
            provenance_id=req.provenance_id,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to register image asset: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.get("/api/v1/assets/{asset_id}", response_model=ImageAsset)
async def get_asset(asset_id: str) -> ImageAsset:
    """Retrieve full technical and provenance metadata for an image asset."""
    asset = asset_catalog.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset {asset_id} not found")
    return asset


@app.post("/api/v1/assets/assign", response_model=ImageAssetAssignment)
async def assign_asset_to_section(req: AssignImageRequest) -> ImageAssetAssignment:
    """Assign an image asset to a report section with layout and caption metadata."""
    try:
        return asset_catalog.assign_to_section(
            section_id=req.section_id,
            asset_id=req.asset_id,
            layout_type=req.layout_type,
            caption=req.caption,
            display_order=req.display_order,
            width_percentage=req.width_percentage,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to assign asset: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.get("/api/v1/assets/sections/{section_id}", response_model=List[ImageAssetAssignment])
async def get_section_image_assignments(section_id: str) -> List[ImageAssetAssignment]:
    """Retrieve all image layout assignments for a specific report section."""
    return asset_catalog.get_section_assignments(section_id)


# ---------------------------------------------------------------------------
# Phase 8: PDF Generation & Rendering Endpoints (Sections 19, 20)
# ---------------------------------------------------------------------------
from fastapi.responses import FileResponse
from core.reports.pdf.renderer import PdfRenderer, PdfRenderResult

pdf_renderer = PdfRenderer(asset_catalog=asset_catalog, output_dir="data/workspace/reports")


@app.post("/api/v1/reports/{report_id}/export/pdf", response_model=PdfRenderResult)
async def export_report_to_pdf(
    report_id: str,
    template: str = "modern",
) -> PdfRenderResult:
    """Render intermediate Report JSON to print PDF (template: 'classic' | 'modern')."""
    rep_path = Path("data/workspace/reports") / f"{report_id}.json"
    if not rep_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found")

    with open(rep_path, "r", encoding="utf-8") as f:
        report = Report.model_validate_json(f.read())

    try:
        res = pdf_renderer.render_report(report, template_name=template)
        audit_logger.log_event(
            event_type=AuditEventType.EXPORT_PDF,
            action="export_pdf",
            resource_id=report_id,
            details={"template": template, "pdf_path": res.pdf_path, "pages": res.page_count},
        )
        return res
    except Exception as exc:
        logger.error("PDF generation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF rendering failed: {str(exc)}")


@app.get("/api/v1/reports/{report_id}/export/pdf")
@app.get("/api/v1/reports/{report_id}/pdf")
async def download_report_pdf(
    report_id: str,
    template: str = "modern",
):

    """Download generated PDF binary."""
    pdf_path = Path("data/workspace/reports") / f"{report_id}_{template}.pdf"
    if not pdf_path.exists():
        rep_path = Path("data/workspace/reports") / f"{report_id}.json"
        if not rep_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found")
        with open(rep_path, "r", encoding="utf-8") as f:
            report = Report.model_validate_json(f.read())
        res = pdf_renderer.render_report(report, template_name=template)
        pdf_path = Path(res.pdf_path)

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{report_id}_{template}.pdf",
    )


@app.get("/api/v1/reports/{report_id}/export/html")
async def download_report_html(
    report_id: str,
    template: str = "modern",
):
    """Download compiled HTML report."""
    html_path = Path("data/workspace/reports") / f"{report_id}_{template}.html"
    if not html_path.exists():
        rep_path = Path("data/workspace/reports") / f"{report_id}.json"
        if not rep_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found")
        with open(rep_path, "r", encoding="utf-8") as f:
            report = Report.model_validate_json(f.read())
        pdf_renderer.render_report(report, template_name=template)

    return FileResponse(
        path=str(html_path),
        media_type="text/html",
        filename=f"{report_id}_{template}.html",
    )


@app.get("/api/v1/reports/{report_id}/preview-html")
async def preview_report_html(
    report_id: str,
    template: str = "classic",
):
    """Return live compiled HTML for in-browser or desktop iframe preview."""
    rep_path = Path("data/workspace/reports") / f"{report_id}.json"
    if not rep_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found")
    with open(rep_path, "r", encoding="utf-8") as f:
        report = Report.model_validate_json(f.read())
    res = pdf_renderer.render_report(report, template_name=template)
    html_path = Path(res.html_path)
    if not html_path.exists():
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="HTML preview file not found")
    content = html_path.read_text(encoding="utf-8")
    return Response(content=content, media_type="text/html")


# ---------------------------------------------------------------------------
# Phase 9: Source Traceability & Agentic Editing Endpoints (Sections 21, 22, 23)
# ---------------------------------------------------------------------------
from core.reports.traceability.viewer import (
    SourceTraceabilityService,
    SourceEvidenceResolution,
)
from core.reports.agent.editing_agent import ReportEditingAgent, EditProposal
from core.reports.agent.tools import ControlledAgentTools

traceability_service = SourceTraceabilityService(canonical_dir="data/workspace/canonical_documents")
agent_tools = ControlledAgentTools(
    search_engine=search_engine,
    asset_catalog=asset_catalog,
    validation_engine=validation_engine,
    audit_logger=audit_logger,
    workspace_dir="data/workspace",
)
editing_agent = ReportEditingAgent(
    ai_gateway=ai_gateway,
    agent_tools=agent_tools,
    validation_engine=validation_engine,
    reports_dir="data/workspace/reports",
    proposals_dir="data/workspace/proposals",
)


class ExecuteAgentToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    authorization_token: Optional[str] = None


@app.get("/api/v1/agent/tools")
async def list_agent_tools_endpoint():
    """List all registered agent tools with their risk postures (Section 23)."""
    return [t.model_dump() for t in agent_tools.list_tools()]


@app.post("/api/v1/agent/tools/execute")
async def execute_agent_tool_endpoint(req: ExecuteAgentToolRequest):
    """Execute a sandboxed agent tool under Section 23 security controls."""
    res = agent_tools.execute_tool(
        tool_name=req.tool_name,
        args=req.arguments,
        authorization_token=req.authorization_token,
    )
    if not res.success and res.requires_approval:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=res.error or "High-risk tool requires human authorization token.",
        )
    return res.model_dump()


class AgentEditRequest(BaseModel):
    section_id: str
    instruction: str


AgentEditRequest.model_rebuild()


@app.get("/api/v1/traceability/resolve", response_model=SourceEvidenceResolution)
async def resolve_source_traceability(
    source_ref: str,
    page: Optional[int] = None,
    cell: Optional[str] = None,
) -> SourceEvidenceResolution:
    """Resolve a citation coordinate [DOC:...:Pxx] or [COORD:...] to primary source elements."""
    return traceability_service.resolve_citation(
        source_reference=source_ref,
        page_number=page,
        cell_address=cell,
    )


@app.get("/api/v1/sources/page-preview")
async def get_source_page_preview(
    document_id: Optional[str] = None,
    source_reference: Optional[str] = None,
    page_number: int = 1,
    element_id: Optional[str] = None,
    bbox: Optional[str] = None,
):
    """
    Renders a requested document page to PNG and highlights the target element or bounding box.
    Preserves exact coordinates under local air-gapped CPU operation (Section 21).
    """
    import io
    import fitz
    from PIL import Image, ImageDraw

    doc_obj: Optional[CanonicalDocument] = None
    file_path: Optional[Path] = None

    if document_id:
        doc_path = Path("data/workspace/canonical_documents") / f"{document_id}.json"
        if not doc_path.exists():
            doc_path = Path("data/cache") / f"{document_id}.json"
        if doc_path.exists():
            try:
                doc_obj = CanonicalDocument.model_validate_json(doc_path.read_text(encoding="utf-8"))
                file_path = Path(doc_obj.source_reference)
            except Exception:
                pass

    if not file_path and source_reference:
        cand = Path(source_reference)
        if cand.exists():
            file_path = cand
        else:
            for base in [Path("data/raw"), Path("data/workspace"), Path(".")]:
                matches = list(base.glob(f"**/{cand.name}"))
                if matches:
                    file_path = matches[0]
                    break

    target_box = None
    if bbox:
        try:
            parts = [float(p.strip()) for p in bbox.split(",")]
            if len(parts) == 4:
                target_box = parts
        except ValueError:
            pass

    if not target_box and doc_obj and element_id:
        for pg in doc_obj.pages:
            if pg.page_number == page_number:
                for el in pg.elements:
                    if el.element_id == element_id and el.bbox:
                        target_box = [el.bbox.x0, el.bbox.y0, el.bbox.x1, el.bbox.y1]
                        break

    img: Optional[Image.Image] = None

    if file_path and file_path.exists() and file_path.suffix.lower() == ".pdf":
        try:
            pdf_doc = fitz.open(str(file_path))
            if 1 <= page_number <= len(pdf_doc):
                fitz_page = pdf_doc[page_number - 1]
                pix = fitz_page.get_pixmap(dpi=150)
                img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGBA")
            pdf_doc.close()
        except Exception as exc:
            logger.warning("Could not render page via fitz: %s", exc)

    elif file_path and file_path.exists() and file_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
        try:
            img = Image.open(str(file_path)).convert("RGBA")
        except Exception:
            pass

    if img is None:
        img = Image.new("RGBA", (700, 950), (255, 255, 255, 255))
        draw_synth = ImageDraw.Draw(img)
        draw_synth.rectangle([(40, 30), (660, 70)], fill=(240, 245, 250, 255), outline=(180, 200, 220, 255))
        title_text = f"SOURCE PAGE PREVIEW — {source_reference or document_id or 'DOCUMENT'} (Page {page_number})"
        draw_synth.text((50, 42), title_text, fill=(20, 40, 70, 255))

        y_cursor = 100
        if doc_obj:
            for pg in doc_obj.pages:
                if pg.page_number == page_number:
                    for el in pg.elements:
                        if el.text:
                            draw_synth.text((50, y_cursor), el.text[:90], fill=(40, 40, 40, 255))
                            y_cursor += 30
                            if y_cursor > 850:
                                break
        if y_cursor == 100:
            draw_synth.text((50, 100), f"Evidence verification preview for page {page_number}.", fill=(50, 50, 50, 255))
            draw_synth.text((50, 140), f"Coordinates: {target_box or 'Entire Page'}", fill=(80, 80, 80, 255))

    if target_box:
        overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw_overlay = ImageDraw.Draw(overlay)

        bx0, by0, bx1, by1 = target_box
        bx0 = max(0.0, min(float(img.width), bx0))
        by0 = max(0.0, min(float(img.height), by0))
        bx1 = max(0.0, min(float(img.width), bx1))
        by1 = max(0.0, min(float(img.height), by1))
        if bx1 <= bx0:
            bx1 = min(float(img.width), bx0 + 200.0)
        if by1 <= by0:
            by1 = min(float(img.height), by0 + 40.0)

        draw_overlay.rectangle([(bx0, by0), (bx1, by1)], fill=(255, 215, 0, 85), outline=(220, 38, 38, 255), width=3)
        tag_text = f" SOURCE: {element_id or 'EVIDENCE'} "
        draw_overlay.rectangle([(bx0, max(0.0, by0 - 20)), (bx0 + len(tag_text) * 7.5, by0)], fill=(220, 38, 38, 230))
        draw_overlay.text((bx0 + 2, max(2.0, by0 - 18)), tag_text, fill=(255, 255, 255, 255))

        img = Image.alpha_composite(img, overlay)

    out_buf = io.BytesIO()
    img.convert("RGB").save(out_buf, format="PNG")
    return Response(content=out_buf.getvalue(), media_type="image/png")


@app.post("/api/v1/reports/{report_id}/edit-agent", response_model=EditProposal)
async def run_agentic_edit(
    report_id: str,
    req: AgentEditRequest,
) -> EditProposal:
    """Agentic editing: Verifies sources, proposes grounded narrative changes, and runs validation."""
    try:
        return editing_agent.propose_edit(
            report_id=report_id,
            section_id=req.section_id,
            user_instruction=req.instruction,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Agentic editing failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.post("/api/v1/reports/proposals/{proposal_id}/accept", response_model=Report)
async def accept_edit_proposal(proposal_id: str) -> Report:
    """Human approval gate: Accepts proposed edit and updates the report."""
    try:
        return editing_agent.accept_proposal(proposal_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Accepting proposal failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.post("/api/v1/reports/proposals/{proposal_id}/reject", response_model=EditProposal)
async def reject_edit_proposal(proposal_id: str) -> EditProposal:
    """Human rejection gate: Discards proposal without modifying the report."""
    try:
        return editing_agent.reject_proposal(proposal_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Rejecting proposal failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ---------------------------------------------------------------------------
# Phase 10: Security Architecture & Audit Logging (Section 24)
# ---------------------------------------------------------------------------

class StoreSecretRequest(BaseModel):
    key: str
    value: str


StoreSecretRequest.model_rebuild()


@app.get("/api/v1/security/status", response_model=Dict[str, Any])
async def get_security_status() -> Dict[str, Any]:
    """Retrieve full air-gap compliance and cryptographic audit ledger verification."""
    is_chain_valid = audit_logger.verify_chain_integrity()
    airgap_posture = NetworkSecurityGuard.verify_air_gap_posture()
    total_logs = audit_logger.count_logs()
    vault_keys = credential_vault.list_keys()

    return {
        "air_gap_enforced": airgap_posture["air_gap_enforced"],
        "no_cloud_ai_calls": True,
        "fully_isolated": airgap_posture["fully_isolated"],
        "cloud_keys_detected": airgap_posture["cloud_keys_detected"],
        "audit_chain_valid": is_chain_valid,
        "total_audit_logs": total_logs,
        "vault_status": "active_encrypted",
        "vault_keys_count": len(vault_keys),
        "vault_keys": vault_keys,
        "active_controls": [
            "Local Loopback Enforcement (127.0.0.1)",
            "Deterministic Numeric & Citation Validation Gates",
            "Zero Cloud AI API Transmissions",
            "SHA-256 Tamper-Evident Chained Audit Trail",
            "OS-Level DPAPI / Machine-Salted Vault Encryption",
            "Strict Human Approval Gates for Agentic Revisions",
        ],
    }


@app.get("/api/v1/security/audit-logs", response_model=List[AuditLogEntry])
async def get_audit_logs(
    event_type: Optional[AuditEventType] = None,
    limit: int = 50,
) -> List[AuditLogEntry]:
    """Retrieve recent cryptographically chained audit events."""
    return audit_logger.list_logs(event_type=event_type, limit=limit)


@app.post("/api/v1/security/vault")
async def store_secret(req: StoreSecretRequest) -> Dict[str, Any]:
    """Store a secret securely in the DPAPI/machine-encrypted vault."""
    credential_vault.store_secret(req.key, req.value)
    audit_logger.log_event(
        event_type=AuditEventType.CONFIG_CHANGE,
        action="store_vault_secret",
        resource_id=req.key,
        details={"key": req.key},
    )
    return {"status": "stored", "key": req.key}


@app.get("/api/v1/security/vault/keys")
async def list_vault_keys() -> List[str]:
    """List stored secret keys (values remain securely hidden)."""
    return credential_vault.list_keys()


# ---------------------------------------------------------------------------
# Phase 11: Golden Dataset & Regression Evaluation Endpoints (Sections 30, 32)
# ---------------------------------------------------------------------------
from core.evaluation.golden_harness import GoldenRegressionHarness
from core.evaluation.models import GoldenRegressionResult

golden_harness = GoldenRegressionHarness()
_latest_golden_result: Optional[GoldenRegressionResult] = None


@app.post("/api/v1/evaluation/run-golden-suite", response_model=GoldenRegressionResult)
async def run_golden_evaluation() -> GoldenRegressionResult:
    """Execute end-to-end regression evaluation against golden dataset."""
    global _latest_golden_result
    try:
        res = golden_harness.run_suite()
        _latest_golden_result = res
        audit_logger.log_event(
            event_type=AuditEventType.REPORT_CREATED,
            action="golden_suite_evaluation",
            resource_id=res.run_id,
            details={
                "provenance_coverage": res.metrics.provenance_coverage,
                "unsupported_claim_rate": res.metrics.unsupported_claim_rate,
                "passed": res.metrics.passed_quality_threshold,
            },
        )
        return res
    except Exception as exc:
        logger.error("Golden suite evaluation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Golden regression suite failed: {str(exc)}",
        )


@app.get("/api/v1/evaluation/latest-report", response_model=Optional[GoldenRegressionResult])
async def get_latest_golden_evaluation() -> Optional[GoldenRegressionResult]:
    """Retrieve the most recent golden regression result."""
    return _latest_golden_result
from core.orchestrator.models import PipelineConfig, PipelineSession, PipelineStage
from core.orchestrator.pipeline import EnterpriseReportPipeline
from core.connectors.upload import AuthorizedReportUploader

enterprise_pipeline = EnterpriseReportPipeline(audit_logger=audit_logger)
report_uploader = AuthorizedReportUploader(audit_logger=audit_logger)


class PipelineStartRequest(BaseModel):
    source_folder: str
    subsidiary: str = "Central Coalfields Limited"
    reporting_year: str = "2024-25"
    reporting_period: str = "Annual"
    template_style: str = "classic"
    reference_report_path: Optional[str] = None
    run_sync: bool = False


class PipelineApproveRequest(BaseModel):
    session_id: str
    approver_name: str
    approval_notes: Optional[str] = None


class PipelineUploadRequest(BaseModel):
    session_id: str
    approver_name: Optional[str] = None
    destination_target: Optional[str] = None


@app.post("/api/v1/pipeline/start", response_model=PipelineSession)
async def start_enterprise_pipeline(
    req: PipelineStartRequest,
    background_tasks: BackgroundTasks,
) -> PipelineSession:
    """Launch the unified enterprise report generation pipeline."""
    session_id = str(uuid.uuid4())
    config = PipelineConfig(
        session_id=session_id,
        source_folder=req.source_folder,
        subsidiary=req.subsidiary,
        reporting_year=req.reporting_year,
        reporting_period=req.reporting_period,
        template_style=req.template_style,
        reference_report_path=req.reference_report_path,
    )

    if req.run_sync:
        session = enterprise_pipeline.run(config)
        return session
    else:
        now = datetime.now().isoformat()
        session = PipelineSession(
            session_id=session_id,
            config=config,
            current_stage=PipelineStage.INITIALIZING,
            progress_percent=0.0,
            created_at=now,
            updated_at=now,
        )
        enterprise_pipeline.save_session(session)
        background_tasks.add_task(enterprise_pipeline.run, config)
        return session


@app.get("/api/v1/pipeline/status/{session_id}", response_model=PipelineSession)
async def get_pipeline_session_status(session_id: str) -> PipelineSession:
    """Retrieve live status, stage logs, and metrics for a pipeline session."""
    session = enterprise_pipeline.load_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline session '{session_id}' not found.",
        )
    return session


@app.post("/api/v1/pipeline/approve", response_model=PipelineSession)
async def approve_pipeline_report(req: PipelineApproveRequest) -> PipelineSession:
    """Designate formal human sign-off for an enterprise report."""
    session = enterprise_pipeline.load_session(req.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline session '{req.session_id}' not found.",
        )
    session.is_approved = True
    session.approved_by = req.approver_name
    session.approval_timestamp = datetime.now().isoformat()
    session.approval_notes = req.approval_notes
    session.updated_at = datetime.now().isoformat()
    enterprise_pipeline.save_session(session)
    return session


@app.post("/api/v1/pipeline/upload")
async def upload_pipeline_report(req: PipelineUploadRequest) -> Dict[str, Any]:
    """Execute authorized enterprise report delivery with signature verification."""
    session = enterprise_pipeline.load_session(req.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline session '{req.session_id}' not found.",
        )
    try:
        res = report_uploader.upload_report(
            session=session,
            destination_target=req.destination_target,
            approver_name=req.approver_name,
        )
        enterprise_pipeline.save_session(session)
        return res
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@app.get("/api/v1/connectors/available")
async def list_available_connectors() -> List[Dict[str, Any]]:
    """Enumerate configured local and future enterprise connectors."""
    return [
        {
            "type": "local_folder",
            "name": "Local Filesystem Connector",
            "status": "active",
            "supported": True,
            "description": "Scans confidential local directories, external drives, and local network shares.",
        },
        {
            "type": "network_share",
            "name": "Enterprise SMB / UNC Share Connector",
            "status": "ready",
            "supported": True,
            "description": "Directly indexes corporate Windows SMB / UNC network storage shares.",
        },
        {
            "type": "sharepoint_dms",
            "name": "Microsoft SharePoint / DMS Connector",
            "status": "ready",
            "supported": True,
            "description": "Synchronizes approved corporate financial and operational document libraries.",
        },
        {
            "type": "cil_sap_erp_api",
            "name": "CIL SAP / ERP Gateway Connector",
            "status": "ready",
            "supported": True,
            "description": "Fetches operational coal production and offtake data from CIL enterprise microservices.",
        },
    ]



# ---------------------------------------------------------------------------
# Phase 14: Incremental Engine, Storage Lifecycle & Observability (Sections 28, 34-37)
# ---------------------------------------------------------------------------
from core.reports.incremental_engine import IncrementalReportEngine, SectionDependencyGraph
from core.storage.lifecycle import StorageManager, ArtifactCategory
from core.observability.telemetry import ObservabilityManager
from core.observability.exporter import SanitizedDiagnosticExporter
from core.domain.reports import Report

storage_manager = StorageManager(workspace_dir="data/workspace")
observability_manager = ObservabilityManager(log_dir="data/workspace/audit_logs")
diagnostic_exporter = SanitizedDiagnosticExporter(
    workspace_dir="data/workspace",
    observability_manager=observability_manager,
    storage_manager=storage_manager,
)
incremental_engine = IncrementalReportEngine(
    validation_engine=validation_engine,
)


class InvalidateSectionsRequest(BaseModel):
    report_id: Optional[str] = None
    report_data: Optional[Dict[str, Any]] = None
    changed_sources: List[str]


class RegenerateSectionsRequest(BaseModel):
    report_id: Optional[str] = None
    report_data: Optional[Dict[str, Any]] = None
    dirty_section_ids: List[str]


class StorageCleanupRequest(BaseModel):
    max_age_seconds: float = 0.0
    dry_run: bool = False


class ExportDiagnosticsRequest(BaseModel):
    bundle_name: Optional[str] = None


@app.post("/api/v1/reports/incremental/invalidate", response_model=Dict[str, Any])
async def invalidate_sections_endpoint(req: InvalidateSectionsRequest) -> Dict[str, Any]:
    """Compute dirty sections needing regeneration based on changed source documents."""
    report_dict = req.report_data
    if not report_dict and req.report_id:
        p = Path("data/workspace/reports") / f"{req.report_id}.json"
        if not p.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {req.report_id} not found")
        with open(p, "r", encoding="utf-8") as f:
            report_dict = json.load(f)

    if not report_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either report_id or report_data must be provided."
        )

    graph = SectionDependencyGraph.build_from_report(report_dict)
    dirty_sections = graph.get_affected_sections(req.changed_sources)
    all_sections = [s.get("section_id") for s in report_dict.get("sections", []) if s.get("section_id")]
    clean_sections = [s for s in all_sections if s not in dirty_sections]

    return {
        "total_sections": len(all_sections),
        "changed_sources": req.changed_sources,
        "dirty_sections": sorted(list(dirty_sections)),
        "clean_sections": clean_sections,
        "graph": graph.to_dict(),
    }


@app.post("/api/v1/reports/incremental/regenerate", response_model=Dict[str, Any])
async def regenerate_sections_endpoint(req: RegenerateSectionsRequest) -> Dict[str, Any]:
    """Surgically regenerate dirty sections and preserve clean cached sections."""
    report_dict = req.report_data
    report_file: Optional[Path] = None
    if not report_dict and req.report_id:
        p = Path("data/workspace/reports") / f"{req.report_id}.json"
        if not p.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {req.report_id} not found")
        report_file = p
        with open(p, "r", encoding="utf-8") as f:
            report_dict = json.load(f)

    if not report_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either report_id or report_data must be provided."
        )

    try:
        report_data = Report.model_validate(report_dict)
    except Exception:
        report_data = Report(
            report_id=report_dict.get("report_id", f"rep_{uuid.uuid4().hex[:8]}"),
            title=report_dict.get("title", "Corporate Annual Report"),
            subsidiary_name=report_dict.get("subsidiary_name", report_dict.get("subsidiary", "CCL")),
            reporting_period=report_dict.get("reporting_period", report_dict.get("financial_year", "2024-25")),
            created_at=datetime.now(),
            metadata=report_dict.get("metadata", {}),
            sections=[],
        )

    result = incremental_engine.regenerate_sections(
        current_report=report_data,
        dirty_section_ids=set(req.dirty_section_ids),
    )

    if report_file and report_file.exists():
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(result.report.model_dump_json(indent=2))

    audit_logger.log_event(
        event_type=AuditEventType.AGENT_EDIT_ACCEPTED,
        action="incremental_regenerate",
        resource_id=result.report.report_id,
        details={
            "regenerated_sections": result.regenerated_section_ids,
            "duration_sec": result.duration_sec,
        },
    )

    observability_manager.record_stage(
        stage_name="INCREMENTAL_REGENERATION",
        duration_sec=result.duration_sec,
        status="SUCCESS",
        metrics={
            "regenerated_count": len(result.regenerated_section_ids),
            "unaffected_count": len(result.unaffected_section_ids),
        },
    )

    return {
        "report_id": result.report.report_id,
        "original_section_count": result.original_section_count,
        "regenerated_section_ids": result.regenerated_section_ids,
        "unaffected_section_ids": result.unaffected_section_ids,
        "duration_sec": result.duration_sec,
        "validation_passed": result.validation.passed,
    }


@app.get("/api/v1/storage/breakdown", response_model=Dict[str, Any])
async def get_storage_breakdown_endpoint() -> Dict[str, Any]:
    """Retrieve workspace disk consumption across all tracked artifact categories."""
    breakdown = storage_manager.get_storage_breakdown()
    total_bytes = sum(v.total_bytes for v in breakdown.values())
    return {
        "categories": {k: v.to_dict() for k, v in breakdown.items()},
        "total_workspace_bytes": total_bytes,
        "formatted_total": format_bytes(total_bytes),
    }


@app.post("/api/v1/storage/cleanup", response_model=Dict[str, Any])
async def cleanup_storage_endpoint(req: StorageCleanupRequest) -> Dict[str, Any]:
    """Safely purge expired temporary render files, strictly protecting original sources."""
    res = storage_manager.cleanup_temporary_artifacts(
        max_age_seconds=req.max_age_seconds,
        dry_run=req.dry_run,
    )
    audit_logger.log_event(
        event_type=AuditEventType.CONFIG_CHANGE,
        action="storage_cleanup",
        resource_id="workspace_temp",
        details=res,
    )
    return res


class StoragePurgeCategoryRequest(BaseModel):
    category: str = Field(..., description="Category to purge (must not be original_source)")
    confirmation: str = Field(..., description="Confirmation token matching PURGE_<CATEGORY>")


@app.post("/api/v1/storage/purge-category", response_model=Dict[str, Any])
async def purge_storage_category_endpoint(req: StoragePurgeCategoryRequest) -> Dict[str, Any]:
    """Purges non-source categories only if explicit confirmation token matches. Rejects original_source."""
    try:
        cat = ArtifactCategory(req.category)
        res = storage_manager.safe_purge_category(cat, req.confirmation)
        audit_logger.log_event(
            event_type=AuditEventType.CONFIG_CHANGE,
            action="storage_purge_category",
            resource_id=req.category,
            details=res,
        )
        return res
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as exc:
        logger.exception("Failed to purge storage category: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.get("/api/v1/observability/telemetry", response_model=Dict[str, Any])
async def get_telemetry_endpoint(limit: int = 50) -> Dict[str, Any]:
    """Retrieve recent operational telemetry logs and stage duration aggregates."""
    return {
        "recent_events": observability_manager.get_recent_telemetry(limit=limit),
        "stage_aggregates": observability_manager.get_stage_aggregates(),
    }


@app.post("/api/v1/observability/export-diagnostics", response_model=Dict[str, Any])
async def export_diagnostics_endpoint(req: ExportDiagnosticsRequest) -> Dict[str, Any]:
    """Generate a sanitized, air-gapped diagnostic zip bundle redacting confidential content."""
    bundle_info = diagnostic_exporter.export_bundle(bundle_name=req.bundle_name)
    audit_logger.log_event(
        event_type=AuditEventType.EXPORT_PDF,
        action="export_sanitized_diagnostics",
        resource_id=bundle_info.bundle_filename,
        details={
            "sha256": bundle_info.sha256_hash,
            "bytes": bundle_info.file_size_bytes,
        },
    )
    return bundle_info.to_dict()


@app.get("/api/v1/observability/download-diagnostics/{bundle_filename}")
async def download_diagnostics_endpoint(bundle_filename: str):
    """Download a generated sanitized diagnostic ZIP package."""
    path = Path("data/workspace/temp/diagnostic_exports") / bundle_filename
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic bundle {bundle_filename} not found",
        )
    return FileResponse(
        str(path),
        media_type="application/zip",
        filename=bundle_filename,
    )



# =====================================================================
# Phase 15 Endpoints: Settings, Vertical Slice & Document Normalization
# =====================================================================

class SelectSubsidiaryRequest(BaseModel):
    code: str


class NormalizeDocumentRequest(BaseModel):
    document_id: str


@app.get("/api/v1/settings", response_model=ApplicationSettings)
async def get_settings_endpoint() -> ApplicationSettings:
    """Retrieve current unified application settings."""
    return settings_manager.get_settings()


@app.post("/api/v1/settings", response_model=ApplicationSettings)
async def update_settings_endpoint(updates: Dict[str, Any]) -> ApplicationSettings:
    """Update application settings with validation and audit logging."""
    updated = settings_manager.update_settings(updates)
    audit_logger.log_event(
        event_type=AuditEventType.CONFIG_CHANGE,
        action="update_application_settings",
        resource_id="app_settings",
        details=updates,
    )
    return updated


@app.post("/api/v1/settings/reset", response_model=ApplicationSettings)
async def reset_settings_endpoint() -> ApplicationSettings:
    """Reset application settings to factory CIL defaults."""
    reset_val = settings_manager.reset_to_defaults()
    audit_logger.log_event(
        event_type=AuditEventType.CONFIG_CHANGE,
        action="reset_application_settings",
        resource_id="app_settings",
        details={"status": "reset_to_defaults"},
    )
    return reset_val


@app.get("/api/v1/settings/subsidiaries", response_model=List[SubsidiaryProfile])
async def get_subsidiaries_endpoint() -> List[SubsidiaryProfile]:
    """List all recognized Coal India subsidiary profiles."""
    return settings_manager.get_available_subsidiaries()


@app.post("/api/v1/settings/subsidiaries/select", response_model=ApplicationSettings)
async def select_subsidiary_endpoint(req: SelectSubsidiaryRequest) -> ApplicationSettings:
    """Switch active Coal India subsidiary profile."""
    try:
        updated = settings_manager.select_active_subsidiary(req.code)
        audit_logger.log_event(
            event_type=AuditEventType.CONFIG_CHANGE,
            action="select_active_subsidiary",
            resource_id=req.code,
            details={"subsidiary_name": updated.subsidiary.full_name},
        )
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@app.post("/api/v1/pipeline/vertical-slice", response_model=VerticalSliceResult)
async def run_vertical_slice_endpoint(
    req: Optional[VerticalSliceConfig] = None,
) -> VerticalSliceResult:
    """Execute Section 40 autonomous first vertical slice over 10-20 representative source files."""
    cfg = req or VerticalSliceConfig()
    try:
        result = vertical_slice_runner.run_vertical_slice(cfg)
        return result
    except Exception as exc:
        logger.exception("Vertical slice execution failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vertical slice execution failed: {exc}",
        )


@app.post("/api/v1/documents/normalize", response_model=Dict[str, Any])
async def normalize_document_endpoint(req: NormalizeDocumentRequest) -> Dict[str, Any]:
    """Generate and cache secondary Markdown representation for an ingested CanonicalDocument."""
    doc_path = Path("data/workspace/canonical_documents") / f"{req.document_id}.json"
    if not doc_path.exists():
        # Check cache dir
        doc_path = Path("data/cache") / f"{req.document_id}.json"
    if not doc_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {req.document_id} not found in workspace",
        )

    try:
        raw_text = doc_path.read_text(encoding="utf-8")
        doc = CanonicalDocument.model_validate_json(raw_text)
        saved_path = document_normalizer.normalize_and_save(doc)
        return {
            "document_id": doc.document_id,
            "markdown_path": str(saved_path),
            "markdown_content": doc.markdown_content,
        }
    except Exception as exc:
        logger.exception("Failed to normalize document %s: %s", req.document_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to normalize document: {exc}",
        )



class SelectOCREngineRequest(BaseModel):
    engine_name: str


class ProcessPageOCRRequest(BaseModel):
    image_base64: str
    page_number: int = 1
    engine_name: Optional[str] = None


class OCRBenchmarkRequest(BaseModel):
    sample_pages: int = 3
    engines: Optional[List[str]] = None


@app.get("/api/v1/ocr/engines")
async def list_ocr_engines_endpoint() -> Dict[str, Any]:
    """List all registered OCR engines and their operational health."""
    return {
        "active_engine": ocr_manager.get_active_engine_name(),
        "engines": [h.model_dump() for h in ocr_manager.list_engines()],
    }


@app.post("/api/v1/ocr/engines/select")
async def select_ocr_engine_endpoint(req: SelectOCREngineRequest) -> Dict[str, Any]:
    """Select the active default OCR engine."""
    try:
        ocr_manager.set_active_engine(req.engine_name)
        return {
            "status": "success",
            "active_engine": ocr_manager.get_active_engine_name(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@app.post("/api/v1/ocr/process-page")
async def process_ocr_page_endpoint(req: ProcessPageOCRRequest) -> Dict[str, Any]:
    """Process a single document page image through the active or specified OCR engine."""
    try:
        img_bytes = base64.b64decode(req.image_base64)
        page_res = ocr_manager.process_page_image(
            image_bytes=img_bytes,
            page_number=req.page_number,
            engine_name=req.engine_name,
        )
        return page_res.model_dump()
    except Exception as exc:
        logger.exception("OCR page processing failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {exc}",
        )


@app.post("/api/v1/ocr/benchmark", response_model=OCRBenchmarkReport)
async def run_ocr_benchmark_endpoint(req: Optional[OCRBenchmarkRequest] = None) -> OCRBenchmarkReport:
    """Run empirical benchmark across local OCR engines."""
    params = req or OCRBenchmarkRequest()
    try:
        report = ocr_benchmark.run_benchmark(
            sample_pages=params.sample_pages,
            engine_names=params.engines,
        )
        return report
    except Exception as exc:
        logger.exception("OCR benchmark failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR benchmark failed: {exc}",
        )


# ---------------------------------------------------------------------------
# Phase 19: Section 22 Human + Agent Review System & Diff Endpoints
# ---------------------------------------------------------------------------

class ProposeEditRequest(BaseModel):
    report_id: str
    section_id: str
    user_instruction: str


class ImageAnalyzeRequest(BaseModel):
    file_path: str
    document_id: Optional[str] = None
    page_number: Optional[int] = None


class ImageLayoutResolveRequest(BaseModel):
    section_type: str
    asset_ids: List[str]
    preferred_layout: Optional[str] = None


class ReportInvalidateRequest(BaseModel):
    changed_sources: List[str] = Field(default_factory=list)
    dirty_section_ids: Optional[List[str]] = None


@app.post("/api/v1/agent/review/propose-edit", response_model=EditProposal)
async def propose_edit_endpoint(req: ProposeEditRequest) -> EditProposal:
    """Trigger grounded, source-aware edit proposal from natural language instruction."""
    try:
        return editing_agent.propose_edit(
            report_id=req.report_id,
            section_id=req.section_id,
            user_instruction=req.user_instruction,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed to propose edit: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.get("/api/v1/agent/review/proposals")
async def list_proposals_endpoint() -> List[Dict[str, Any]]:
    """List all generated edit proposals for human review."""
    proposals = []
    p_dir = Path("data/workspace/proposals")
    if p_dir.exists():
        for p in p_dir.glob("*.json"):
            try:
                proposals.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                pass
    return sorted(proposals, key=lambda x: x.get("created_at", ""), reverse=True)


@app.get("/api/v1/agent/review/proposals/{proposal_id}", response_model=EditProposal)
async def get_proposal_endpoint(proposal_id: str) -> EditProposal:
    """Retrieve specific edit proposal including structured diff lines and validation status."""
    p_file = Path("data/workspace/proposals") / f"{proposal_id}.json"
    if not p_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Proposal {proposal_id} not found")
    return EditProposal.model_validate_json(p_file.read_text(encoding="utf-8"))


@app.post("/api/v1/agent/review/proposals/{proposal_id}/accept")
async def accept_proposal_endpoint(proposal_id: str) -> Dict[str, Any]:
    """Human approval: Applies proposal to report model, increments version, and saves to disk."""
    try:
        report = editing_agent.accept_proposal(proposal_id)
        return {
            "status": "accepted",
            "proposal_id": proposal_id,
            "report_id": report.report_id,
            "version": report.version,
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed to accept proposal: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.post("/api/v1/agent/review/proposals/{proposal_id}/reject")
async def reject_proposal_endpoint(proposal_id: str) -> Dict[str, Any]:
    """Human rejection: Discards proposal without mutating report model."""
    try:
        proposal = editing_agent.reject_proposal(proposal_id)
        return {"status": "rejected", "proposal_id": proposal.proposal_id}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed to reject proposal: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ---------------------------------------------------------------------------
# Phase 19: Section 18 Image Intelligence & Asset Catalog Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/images/analyze", response_model=ImageAsset)
async def analyze_image_endpoint(req: ImageAnalyzeRequest) -> ImageAsset:
    """Analyze image file for dimensions, quality score, perceptual dHash, and topic categorization."""
    p = Path(req.file_path)
    if not p.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Image file not found: {req.file_path}")
    try:
        return asset_catalog.register_image(
            file_path=str(p),
            source_document_id=req.document_id,
            page_number=req.page_number,
        )
    except Exception as exc:
        logger.exception("Image analysis failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.get("/api/v1/images/catalog", response_model=List[ImageAsset])
async def list_image_catalog_endpoint(
    tag: Optional[str] = None,
    include_duplicates: bool = True,
) -> List[ImageAsset]:
    """Query image catalog by tag or retrieve all cataloged assets."""
    return asset_catalog.list_assets(tag=tag, include_duplicates=include_duplicates)


@app.post("/api/v1/images/layout-resolve", response_model=SectionImagePresentation)
async def resolve_image_layout_endpoint(req: ImageLayoutResolveRequest) -> SectionImagePresentation:
    """Deterministic Layout Engine: Generates layout specifications without exposing coordinates to LLM."""
    assets = [asset_catalog.get_asset(aid) for aid in req.asset_ids]
    valid_assets = [a for a in assets if a is not None]
    pref_enum = (
        ImageLayoutType(req.preferred_layout)
        if req.preferred_layout and req.preferred_layout in ImageLayoutType._value2member_map_
        else None
    )
    return DeterministicLayoutEngine.resolve_layout(
        section_type=req.section_type,
        available_assets=valid_assets,
        preferred_layout=pref_enum,
    )


# ---------------------------------------------------------------------------
# Phase 19: Section 28 Invalidation & Section 32 Quality Metrics Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/reports/{report_id}/quality-metrics", response_model=ReportQualityMetrics)
async def evaluate_report_quality_endpoint(report_id: str) -> ReportQualityMetrics:
    """Evaluate comprehensive empirical quality metrics (provenance coverage, unsupported claims, math errors)."""
    rep_file = Path("data/workspace/reports") / f"{report_id}.json"
    if not rep_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found")
    try:
        report = Report.model_validate_json(rep_file.read_text(encoding="utf-8"))
        return quality_evaluator.evaluate_report(report)
    except Exception as exc:
        logger.exception("Failed to calculate report quality metrics: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.post("/api/v1/reports/{report_id}/invalidate")
async def invalidate_report_sections_endpoint(report_id: str, req: ReportInvalidateRequest) -> Dict[str, Any]:
    """Selective Invalidation: Calculates downstream sections needing regeneration when sources change."""
    rep_file = Path("data/workspace/reports") / f"{report_id}.json"
    if not rep_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found")
    try:
        report = Report.model_validate_json(rep_file.read_text(encoding="utf-8"))
        graph = SectionDependencyGraph.build_from_report(report)
        affected = graph.get_affected_sections(req.changed_sources)
        if req.dirty_section_ids:
            affected.update(req.dirty_section_ids)
        return {
            "report_id": report_id,
            "changed_sources": req.changed_sources,
            "affected_section_ids": list(affected),
            "total_affected": len(affected),
            "total_sections": len(report.sections),
        }
    except Exception as exc:
        logger.exception("Failed to calculate section invalidation: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ---------------------------------------------------------------------------
# Phase 20: Section 14 Previous Report Analysis & YoY Comparative Endpoints
# ---------------------------------------------------------------------------

class CompareStructuresRequest(BaseModel):
    prior_sections: List[str]
    current_sections: List[str]
    prior_period: str = "FY 2022-23"
    current_period: str = "FY 2023-24"


class GenerateYoYTableRequest(BaseModel):
    category: str = "operational"
    prior_metrics: Dict[str, float]
    current_metrics: Dict[str, float]
    prior_period: str = "FY 2022-23"
    current_period: str = "FY 2023-24"
    source_ref: str = ""


@app.post("/api/v1/reports/compare-structures", response_model=StructuralChangeReport)
async def compare_report_structures_endpoint(req: CompareStructuresRequest) -> StructuralChangeReport:
    """Compares outline structure between prior year and current year to detect structural evolution."""
    try:
        return comparative_analyzer.compare_structures(
            prior_sections=req.prior_sections,
            current_sections=req.current_sections,
            prior_period=req.prior_period,
            current_period=req.current_period,
        )
    except Exception as exc:
        logger.exception("Failed to compare report structures: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.post("/api/v1/reports/generate-yoy-table", response_model=YoYComparativeTable)
async def generate_yoy_comparative_table_endpoint(req: GenerateYoYTableRequest) -> YoYComparativeTable:
    """Generates standardized Year-over-Year comparative table with variance calculations."""
    try:
        return comparative_analyzer.generate_yoy_comparative_table(
            category=req.category,
            prior_metrics=req.prior_metrics,
            current_metrics=req.current_metrics,
            prior_period=req.prior_period,
            current_period=req.current_period,
            source_ref=req.source_ref,
        )
    except Exception as exc:
        logger.exception("Failed to generate YoY comparative table: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

# ---------------------------------------------------------------------------
# Section 25 & 38: Embedded Static Desktop UI Serving (Zero-Node Workstation Fallback)
# ---------------------------------------------------------------------------
DIST_DIR = Path(__file__).resolve().parent.parent / "desktop" / "dist"
if DIST_DIR.exists():
    _assets_dir = DIST_DIR / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="desktop_assets")
    app.mount("/ui", StaticFiles(directory=str(DIST_DIR), html=True), name="desktop_ui")


@app.get("/", include_in_schema=False)
async def serve_desktop_root():
    """Serves the compiled Desktop React UI index.html, or a fallback health status if not built."""
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({
        "status": "healthy",
        "service": "cil-local-report-generator",
        "version": "0.1.0",
        "message": "Desktop UI build not found in apps/desktop/dist. Run npm run build to compile.",
    })


def start():

    """CLI entrypoint to run server."""
    uvicorn.run(
        "apps.processing.server:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=False,
    )


if __name__ == "__main__":
    start()

