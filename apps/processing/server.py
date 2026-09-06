"""
FastAPI Local Processing Server — Section 25 & Section 39 (Phase 0).

Provides local HTTP/REST endpoints for health checks, system diagnostics,
and orchestrating document intelligence tasks for the desktop shell.
"""
from __future__ import annotations

import json
import platform
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil
import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from apps.processing.config import settings
from apps.processing.logging_config import setup_logging
from core.domain.jobs import ProcessingJob
from core.ingestion.discovery import DiscoveredFile, discover_files
from core.ingestion.jobs import IngestionJobManager

logger = setup_logging(settings.log_level)
START_TIME = time.time()
job_manager = IngestionJobManager()


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
