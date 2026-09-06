"""
FastAPI Local Processing Server — Section 25 & Section 39 (Phase 0).

Provides local HTTP/REST endpoints for health checks, system diagnostics,
and orchestrating document intelligence tasks for the desktop shell.
"""
from __future__ import annotations

import platform
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

import psutil
import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from apps.processing.config import settings
from apps.processing.logging_config import setup_logging

logger = setup_logging(settings.log_level)
START_TIME = time.time()


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
    """Hardware capability and resource consumption diagnostics (Section 0 target environment metrics)."""
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
