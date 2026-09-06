"""
Golden Regression Harness — Section 30, Section 39 (Phase 11), and Section 40 of Master Plan.

Runs the complete vertical slice on the Golden Reference Dataset and calculates
verifiable Section 32 quality metrics, proving end-to-end correctness.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Optional

from core.ai import LocalAIGateway
from core.assets.catalog import AssetCatalog
from core.assets.models import ImageLayoutType
from core.assets.layout_selector import LayoutSelector
from core.evaluation.golden_dataset import GoldenDatasetBuilder
from core.evaluation.metrics import QualityMetricCalculator
from core.evaluation.models import GoldenRegressionResult, ReportQualityMetrics
from core.extraction import UnifiedDocumentExtractor
from core.ingestion.discovery import discover_files
from core.reports.generator.report_generator import MasterReportGenerator
from core.reports.generator.section_generator import SectionGenerator
from core.reports.pdf.renderer import PdfRenderer
from core.reports.planner.evidence_mapper import EvidenceToSectionMapper
from core.reports.planner.planner import ReportPlanner
from core.retrieval.db import ReportDatabase
from core.retrieval.indexer import DocumentIndexer
from core.retrieval.search import HybridSearchEngine
from core.security.audit_logger import AuditLogger
from core.validation.engine import ValidationEngine


class GoldenRegressionHarness:
    """
    Executes automated end-to-end regression validation against the golden reference dataset.
    """

    def __init__(
        self,
        golden_dir: str = "testdata/reference_report",
        workspace_dir: str = "data/workspace/golden_run",
    ):
        self.golden_dir = Path(golden_dir)
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def run_suite(self) -> GoldenRegressionResult:
        """Run complete vertical slice from ingestion to PDF export on golden fixtures."""
        start_time = time.time()
        run_id = f"gold_{uuid.uuid4().hex[:8]}"

        # 1. Ensure golden dataset is generated
        builder = GoldenDatasetBuilder(base_dir=str(self.golden_dir))
        builder.build_dataset()

        # Load ground truth
        gt_path = self.golden_dir / "ground_truth.json"
        ground_truth = json.loads(gt_path.read_text(encoding="utf-8")) if gt_path.exists() else {}

        # 2. Discover files
        discovered = discover_files(str(self.golden_dir))

        # 3. Canonical extraction
        extractor = UnifiedDocumentExtractor()
        canonical_dir = self.workspace_dir / "canonical"
        canonical_dir.mkdir(parents=True, exist_ok=True)
        canonical_docs = []

        for df in discovered:
            if not df.filename.endswith(".json"):
                try:
                    cdoc = extractor.extract(df.absolute_path)
                    if df.temporal.financial_year:
                        cdoc.reporting_year = df.temporal.financial_year
                    if df.temporal.reporting_period:
                        cdoc.reporting_period = df.temporal.reporting_period
                    canonical_docs.append(cdoc)
                    # Persist canonical doc
                    (canonical_dir / f"{cdoc.document_id}.json").write_text(
                        cdoc.model_dump_json(indent=2), encoding="utf-8"
                    )
                except Exception:
                    continue

        # 4. Indexing into SQLite FTS5
        db_path = str(self.workspace_dir / "golden_fts.db")
        report_db = ReportDatabase(db_path=db_path)
        indexer = DocumentIndexer(db=report_db)
        for cdoc in canonical_docs:
            indexer.index_document(cdoc)

        search_engine = HybridSearchEngine(db=report_db)

        # 5. Local AI & Report Planner
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
        plan = planner.generate_plan(
            current_evidence_corpus=evidence_corpus,
            report_title="Central Coalfields Limited Annual Report 2023-24",
            reporting_period="FY 2023-24",
            subsidiary_name="Central Coalfields Limited",
            template_name="modern",
            attach_evidence=True,
        )

        # 6. Report Generation & Validation
        val_engine = ValidationEngine()
        reports_dir = str(self.workspace_dir / "reports")
        report_gen = MasterReportGenerator(
            section_generator=SectionGenerator(ai_gateway=ai_gateway),
            validation_engine=val_engine,
            output_dir=reports_dir,
        )
        report, val_report = report_gen.generate_report(plan)

        # 7. Image Asset Cataloging & Assignment
        assets_db = str(self.workspace_dir / "assets.db")
        asset_catalog = AssetCatalog(db_path=assets_db)
        photo_dir = self.golden_dir / "photographs"
        if photo_dir.exists():
            for p in photo_dir.glob("*.png"):
                asset = asset_catalog.register_image(str(p), source_document_id=p.name)
                # Assign to first section
                if report.sections:
                    asset_catalog.assign_to_section(
                        section_id=report.sections[0].section_id,
                        asset_id=asset.asset_id,
                        layout_type=ImageLayoutType.SINGLE_HERO,
                        caption=f"Operational site: {p.stem}",
                    )

        # 8. PDF Rendering
        pdf_renderer = PdfRenderer(asset_catalog=asset_catalog, output_dir=reports_dir)
        pdf_result = pdf_renderer.render_report(report, template_name="modern")

        # 9. Audit Logging & Verification
        from core.security.models import AuditEventType
        audit_db = str(self.workspace_dir / "audit.db")
        audit_logger = AuditLogger(db_path=audit_db)
        audit_logger.log_event(
            event_type=AuditEventType.REPORT_CREATED,
            action="golden_regression_run",
            resource_id=report.report_id,
            details={"sections": len(report.sections), "pdf": pdf_result.pdf_path},
        )
        chain_valid = audit_logger.verify_chain_integrity()

        # 10. Quality Metrics Calculation
        calc = QualityMetricCalculator(canonical_dir=str(canonical_dir))
        metrics = calc.evaluate_report(report, ground_truth=ground_truth)

        duration = time.time() - start_time

        return GoldenRegressionResult(
            run_id=run_id,
            total_golden_fixtures=len(discovered),
            ingested_documents=len(canonical_docs),
            generated_sections=len(report.sections),
            metrics=metrics,
            validation_passed=val_report.passed,
            audit_chain_verified=chain_valid,
            pdf_generated=bool(pdf_result.pdf_path and Path(pdf_result.pdf_path).exists()),
            pdf_path=pdf_result.pdf_path,
            execution_duration_sec=round(duration, 2),
        )
