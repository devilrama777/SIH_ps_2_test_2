"""
Master Enterprise Report Generation Pipeline.
Phase 13 (Section 33, 40, and 46 of Master Implementation Plan).

Coordinates the complete vertical slice from raw source folder discovery to final
air-gapped PDF rendering and cryptographic audit logging.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional
import uuid

from core.ai import LocalAIGateway
from core.assets.catalog import AssetCatalog
from core.assets.models import ImageLayoutType
from core.connectors.local import LocalFolderConnector
from core.ingestion.discovery import discover_files
from core.evaluation.metrics import QualityMetricCalculator
from core.extraction import UnifiedDocumentExtractor
from core.orchestrator.models import (
    PipelineConfig,
    PipelineLogEntry,
    PipelineSession,
    PipelineStage,
)
from core.reports.generator.report_generator import MasterReportGenerator
from core.reports.generator.section_generator import SectionGenerator
from core.reports.pdf.renderer import PdfRenderer
from core.reports.planner.evidence_mapper import EvidenceToSectionMapper
from core.reports.planner.planner import ReportPlanner
from core.retrieval.db import ReportDatabase
from core.retrieval.indexer import DocumentIndexer
from core.retrieval.search import HybridSearchEngine
from core.security.audit_logger import AuditLogger
from core.security.models import AuditEventType
from core.validation.engine import ValidationEngine

logger = logging.getLogger("core.orchestrator.pipeline")


class EnterpriseReportPipeline:
    """Master orchestrator executing the unified 8-stage enterprise report generation workflow."""

    def __init__(
        self,
        workspace_dir: Optional[Path] = None,
        audit_logger: Optional[AuditLogger] = None,
    ):
        self.workspace_dir = (workspace_dir or Path("data/workspace")).resolve()
        self.sessions_dir = self.workspace_dir / "pipeline_sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.audit_logger = audit_logger or AuditLogger(db_path=str(self.workspace_dir / "audit_log.db"))

    def _log(
        self,
        session: PipelineSession,
        stage: PipelineStage,
        message: str,
        level: str = "INFO",
        progress: Optional[float] = None,
    ) -> None:
        entry = PipelineLogEntry(
            timestamp=datetime.now().isoformat(),
            stage=stage,
            message=message,
            level=level,
        )
        session.logs.append(entry)
        session.current_stage = stage
        if progress is not None:
            session.progress_percent = round(progress, 1)
        session.updated_at = datetime.now().isoformat()
        self.save_session(session)
        logger.info("[%s] [%s] %s", session.session_id[:8], stage.value.upper(), message)

    def save_session(self, session: PipelineSession) -> None:
        session_file = self.sessions_dir / f"{session.session_id}.json"
        session_file.write_text(session.model_dump_json(indent=2), encoding="utf-8")

    def load_session(self, session_id: str) -> Optional[PipelineSession]:
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            return None
        return PipelineSession.model_validate_json(session_file.read_text(encoding="utf-8"))

    def run(
        self,
        config: PipelineConfig,
        progress_callback: Optional[Callable[[PipelineSession], None]] = None,
    ) -> PipelineSession:
        now = datetime.now().isoformat()
        session = PipelineSession(
            session_id=config.session_id,
            config=config,
            current_stage=PipelineStage.INITIALIZING,
            progress_percent=0.0,
            created_at=now,
            updated_at=now,
        )
        self.save_session(session)

        try:
            # 1. DISCOVERY
            self._log(session, PipelineStage.DISCOVERY, f"Scanning source folder: {config.source_folder}", progress=5.0)
            discovered_files = discover_files(config.source_folder)
            self._log(session, PipelineStage.DISCOVERY, f"Discovered {len(discovered_files)} supported files", progress=15.0)

            # 2. EXTRACTION
            self._log(session, PipelineStage.EXTRACTION, "Extracting text, tables, and coordinates into Canonical Model", progress=20.0)
            extractor = UnifiedDocumentExtractor()
            canonical_docs = []
            for df in discovered_files:
                if not df.filename.endswith(".json"):
                    try:
                        doc = extractor.extract(df.absolute_path, discovered=df)
                        if df.temporal.financial_year:
                            doc.reporting_year = df.temporal.financial_year
                        else:
                            doc.reporting_year = config.reporting_year
                        if df.temporal.reporting_period:
                            doc.reporting_period = df.temporal.reporting_period
                        else:
                            doc.reporting_period = config.reporting_period
                        canonical_docs.append(doc)
                    except Exception as ext_err:
                        logger.warning("Skining failed document %s: %s", df.filename, ext_err)
            self._log(session, PipelineStage.EXTRACTION, f"Extracted {len(canonical_docs)} canonical documents", progress=35.0)

            # 3. INDEXING
            self._log(session, PipelineStage.INDEXING, "Indexing canonical document chunks in SQLite FTS5 vector store", progress=40.0)
            db_path = self.workspace_dir / "indexes" / f"fts_{session.session_id}.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            report_db = ReportDatabase(db_path=str(db_path))
            indexer = DocumentIndexer(db=report_db)
            for doc in canonical_docs:
                indexer.index_document(doc)
            search_engine = HybridSearchEngine(db=report_db)
            self._log(session, PipelineStage.INDEXING, "FTS5 hybrid search index built successfully", progress=50.0)

            # 4. PLANNING
            self._log(session, PipelineStage.PLANNING, f"Creating dynamic report blueprint for {config.subsidiary}", progress=55.0)
            ai_gateway = LocalAIGateway()
            evidence_corpus = [
                {
                    "id": cdoc.document_id,
                    "text": cdoc.markdown_content or " ".join([el.text for p in cdoc.pages for el in p.elements if el.text]),
                }
                for cdoc in canonical_docs
            ]
            evidence_mapper = EvidenceToSectionMapper(search_engine=search_engine)
            planner = ReportPlanner(evidence_mapper=evidence_mapper)
            report_title = f"{config.subsidiary} Annual Report {config.reporting_year}"
            report_plan = planner.generate_plan(
                current_evidence_corpus=evidence_corpus,
                report_title=report_title,
                reporting_period=config.reporting_year,
                subsidiary_name=config.subsidiary,
                template_name=config.template_style,
                attach_evidence=True,
            )
            self._log(session, PipelineStage.PLANNING, f"Generated blueprint with {len(report_plan.sections)} chapters", progress=65.0)

            # 5. GENERATION
            self._log(session, PipelineStage.GENERATION, "Generating sections, financial tables, charts, and citations", progress=70.0)
            reports_dir = self.workspace_dir / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            val_engine = ValidationEngine()
            generator = MasterReportGenerator(
                section_generator=SectionGenerator(ai_gateway=ai_gateway),
                validation_engine=val_engine,
                output_dir=str(reports_dir),
            )
            report, val_report = generator.generate_report(report_plan)
            session.report_id = report.report_id
            self._log(session, PipelineStage.GENERATION, f"Synthesized report '{report.title}' ({report.report_id})", progress=80.0)

            # 6. VALIDATION & QUALITY METRICS
            self._log(session, PipelineStage.VALIDATION, "Executing 6-dimension deterministic validation engine", progress=85.0)
            calc = QualityMetricCalculator()
            metrics = calc.evaluate_report(report)
            session.metrics = {
                "source_coverage": round(metrics.source_coverage, 3),
                "provenance_coverage": round(metrics.provenance_coverage, 3),
                "unsupported_claim_rate": round(metrics.unsupported_claim_rate, 3),
                "numerical_error_rate": round(metrics.numerical_error_rate, 3),
                "validation_passed": val_report.passed,
                "validation_findings_count": len(val_report.issues),
            }
            self._log(session, PipelineStage.VALIDATION, f"Quality audit complete: {metrics.provenance_coverage*100:.1f}% provenance coverage", progress=90.0)

            # 7. ASSET INTELLIGENCE & PDF RENDERING
            self._log(session, PipelineStage.ASSET_INTELLIGENCE, "Cataloging image assets and determining visual placement", progress=92.0)
            assets_db = str(self.workspace_dir / f"assets_{session.session_id}.db")
            asset_catalog = AssetCatalog(db_path=assets_db)
            source_p = Path(config.source_folder)
            for img_path in list(source_p.rglob("*.png")) + list(source_p.rglob("*.jpg")):
                try:
                    asset = asset_catalog.register_image(str(img_path), source_document_id=img_path.name)
                    if report.sections:
                        asset_catalog.assign_to_section(
                            section_id=report.sections[0].section_id,
                            asset_id=asset.asset_id,
                            layout_type=ImageLayoutType.SINGLE_HERO,
                            caption=f"Operational site: {img_path.stem}",
                        )
                except Exception:
                    continue

            self._log(session, PipelineStage.PDF_RENDERING, f"Rendering PDF using {config.template_style.upper()} template", progress=95.0)
            pdf_renderer = PdfRenderer(asset_catalog=asset_catalog, output_dir=str(reports_dir))
            pdf_result = pdf_renderer.render_report(report, template_name=config.template_style)
            session.pdf_path = pdf_result.pdf_path

            # 8. COMPLETION & AUDIT LOGGING
            self.audit_logger.log_event(
                event_type=AuditEventType.REPORT_CREATED,
                action="enterprise_pipeline_execution",
                resource_id=report.report_id,
                details={
                    "session_id": session.session_id,
                    "subsidiary": config.subsidiary,
                    "reporting_year": config.reporting_year,
                    "template": config.template_style,
                    "pdf_path": session.pdf_path,
                    "metrics": session.metrics,
                },
            )

            self._log(session, PipelineStage.COMPLETED, f"Enterprise report generation finished: {Path(session.pdf_path).name}", progress=100.0)
            if progress_callback:
                progress_callback(session)

            return session

        except Exception as exc:
            logger.exception("Enterprise report pipeline failed: %s", exc)
            session.current_stage = PipelineStage.FAILED
            session.error = str(exc)
            session.updated_at = datetime.now().isoformat()
            self._log(session, PipelineStage.FAILED, f"Pipeline execution failed: {exc}", level="ERROR")
            if progress_callback:
                progress_callback(session)
            return session
