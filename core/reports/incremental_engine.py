"""
Section-Level Dependency Graph and Incremental Report Regeneration Engine.
Strictly adheres to CIL Master Implementation Plan Section 28.
Never regenerate an entire 400-page report because one paragraph or source changed.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Set

from core.domain.reports import Report, ReportSection, NarrativeBlock, SectionType, ValidationStatus
from core.domain.evidence import EvidenceReference
from core.reports.generator.section_generator import SectionGenerator
from core.reports.planner.planner import PlannedSection
from core.reports.planner.evidence_mapper import SectionEvidencePackage
from core.validation.engine import ValidationEngine, ValidationReport

logger = logging.getLogger(__name__)


@dataclass
class SectionDependencyGraph:
    """
    Tracks upstream source dependencies and cross-section dependencies.
    Maps:
      - section_id -> Set of source document URIs
      - source_uri -> Set of affected section_ids
      - section_id -> Set of upstream section_ids (e.g. executive summary depends on finance & operations)
    """
    section_to_sources: Dict[str, Set[str]] = field(default_factory=dict)
    source_to_sections: Dict[str, Set[str]] = field(default_factory=dict)
    section_to_upstream_sections: Dict[str, Set[str]] = field(default_factory=dict)
    downstream_sections: Dict[str, Set[str]] = field(default_factory=dict)

    def register_dependency(self, section_id: str, source_uri: str) -> None:
        """Register that a section relies on a specific source URI."""
        norm_source = Path(source_uri).name.lower()
        self.section_to_sources.setdefault(section_id, set()).add(norm_source)
        self.source_to_sections.setdefault(norm_source, set()).add(section_id)

    def register_section_dependency(self, dependent_section_id: str, upstream_section_id: str) -> None:
        """Register that dependent_section_id synthesizes or aggregates upstream_section_id."""
        self.section_to_upstream_sections.setdefault(dependent_section_id, set()).add(upstream_section_id)
        self.downstream_sections.setdefault(upstream_section_id, set()).add(dependent_section_id)

    def get_affected_sections(self, changed_source_uris: List[str]) -> Set[str]:
        """
        Compute the transitive closure of dirty sections needing regeneration
        when a set of source files have changed.
        """
        dirty_sections: Set[str] = set()

        for uri in changed_source_uris:
            norm = Path(uri).name.lower()
            if norm in self.source_to_sections:
                for sec_id in self.source_to_sections[norm]:
                    dirty_sections.add(sec_id)

        # Transitive resolution for downstream summarizing sections (e.g. Executive Summary)
        changed_size = True
        while changed_size:
            current_len = len(dirty_sections)
            new_dirty = set(dirty_sections)
            for sec_id in dirty_sections:
                if sec_id in self.downstream_sections:
                    for downstream_id in self.downstream_sections[sec_id]:
                        new_dirty.add(downstream_id)
            dirty_sections = new_dirty
            changed_size = len(dirty_sections) > current_len

        return dirty_sections

    @classmethod
    def build_from_report(cls, report: Any) -> "SectionDependencyGraph":
        """Build dependency graph from evidence citations inside Report, ReportData, or dict."""
        graph = cls()

        sections = []
        if isinstance(report, dict):
            sections = report.get("sections", [])
        elif hasattr(report, "sections"):
            sections = report.sections

        for sec in sections:
            sec_id = getattr(sec, "section_id", None) if not isinstance(sec, dict) else sec.get("section_id")
            title = getattr(sec, "title", "") if not isinstance(sec, dict) else sec.get("title", "")
            if not sec_id:
                continue

            # 1. From direct source_refs
            source_refs = getattr(sec, "source_refs", []) if not isinstance(sec, dict) else sec.get("source_refs", [])
            for s_ref in source_refs:
                if s_ref:
                    graph.register_dependency(sec_id, str(s_ref))

            # 2. From direct evidence list
            evidence = getattr(sec, "evidence", []) if not isinstance(sec, dict) else sec.get("evidence", [])
            for ev in evidence:
                uri = getattr(ev, "source_uri", None) if not isinstance(ev, dict) else ev.get("source_uri")
                if uri:
                    graph.register_dependency(sec_id, str(uri))

            # 3. From paragraphs with provenance / source anchors
            paragraphs = getattr(sec, "paragraphs", []) if not isinstance(sec, dict) else sec.get("paragraphs", [])
            for p in paragraphs:
                prov_list = getattr(p, "provenance", []) if not isinstance(p, dict) else p.get("provenance", [])
                for prov in prov_list:
                    doc_id = getattr(prov, "document_id", None) if not isinstance(prov, dict) else prov.get("document_id")
                    if doc_id:
                        graph.register_dependency(sec_id, str(doc_id))

            # 4. From narrative_blocks
            blocks = getattr(sec, "narrative_blocks", []) if not isinstance(sec, dict) else sec.get("narrative_blocks", [])
            for b in blocks:
                ev_refs = getattr(b, "evidence_refs", []) if not isinstance(b, dict) else b.get("evidence_refs", [])
                for ev in ev_refs:
                    doc_id = getattr(ev, "document_id", None) if not isinstance(ev, dict) else ev.get("document_id")
                    if doc_id:
                        graph.register_dependency(sec_id, str(doc_id))

            # 5. From tables with coordinate provenance
            tables = getattr(sec, "tables", []) if not isinstance(sec, dict) else sec.get("tables", [])
            for t in tables:
                rows = getattr(t, "rows", []) if not isinstance(t, dict) else t.get("rows", [])
                for row in rows:
                    if isinstance(row, list):
                        for cell in row:
                            prov = getattr(cell, "provenance", None) if not isinstance(cell, dict) else cell.get("provenance")
                            doc_id = getattr(prov, "document_id", None) if not isinstance(prov, dict) else (prov.get("document_id") if prov else None)
                            if doc_id:
                                graph.register_dependency(sec_id, str(doc_id))

        # Common corporate convention: Executive Summary depends on Operational and Financial sections
        exec_ids = []
        body_ids = []
        for sec in sections:
            sec_id = getattr(sec, "section_id", None) if not isinstance(sec, dict) else sec.get("section_id")
            title = getattr(sec, "title", "") if not isinstance(sec, dict) else sec.get("title", "")
            if not sec_id:
                continue
            if "executive" in title.lower() or "overview" in title.lower():
                exec_ids.append(sec_id)
            else:
                body_ids.append(sec_id)

        for ex_id in exec_ids:
            for b_id in body_ids:
                graph.register_section_dependency(ex_id, b_id)

        return graph

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_to_sources": {k: sorted(list(v)) for k, v in self.section_to_sources.items()},
            "source_to_sections": {k: sorted(list(v)) for k, v in self.source_to_sections.items()},
            "section_to_upstream_sections": {k: sorted(list(v)) for k, v in self.section_to_upstream_sections.items()},
            "downstream_sections": {k: sorted(list(v)) for k, v in self.downstream_sections.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SectionDependencyGraph":
        graph = cls()
        graph.section_to_sources = {k: set(v) for k, v in data.get("section_to_sources", {}).items()}
        graph.source_to_sections = {k: set(v) for k, v in data.get("source_to_sections", {}).items()}
        graph.section_to_upstream_sections = {k: set(v) for k, v in data.get("section_to_upstream_sections", {}).items()}
        graph.downstream_sections = {k: set(v) for k, v in data.get("downstream_sections", {}).items()}
        return graph


@dataclass
class IncrementalRegenerationResult:
    """Outcome of surgical report regeneration."""
    original_section_count: int
    regenerated_section_ids: List[str]
    unaffected_section_ids: List[str]
    duration_sec: float
    report: Report
    validation: ValidationReport


class IncrementalReportEngine:
    """
    Orchestrates selective section-level invalidation and regeneration.
    Fulfills Section 28.
    """

    def __init__(
        self,
        section_generator: Optional[SectionGenerator] = None,
        validation_engine: Optional[ValidationEngine] = None,
    ):
        self.section_generator = section_generator or SectionGenerator()
        self.validation_engine = validation_engine or ValidationEngine()

    def invalidate(
        self,
        current_report: Any,
        changed_source_uris: List[str],
        dependency_graph: Optional[SectionDependencyGraph] = None,
    ) -> Dict[str, Any]:
        """
        Identify affected sections without running regeneration.
        Returns detailed invalidation diagnosis.
        """
        graph = dependency_graph or SectionDependencyGraph.build_from_report(current_report)
        dirty_section_ids = graph.get_affected_sections(changed_source_uris)

        all_sec_ids = []
        sections = getattr(current_report, "sections", []) if not isinstance(current_report, dict) else current_report.get("sections", [])
        for s in sections:
            s_id = getattr(s, "section_id", None) if not isinstance(s, dict) else s.get("section_id")
            if s_id:
                all_sec_ids.append(s_id)

        clean_section_ids = [sid for sid in all_sec_ids if sid not in dirty_section_ids]

        return {
            "total_sections": len(all_sec_ids),
            "changed_sources": changed_source_uris,
            "dirty_sections": sorted(list(dirty_section_ids)),
            "clean_sections": clean_section_ids,
            "graph": graph.to_dict(),
        }

    def regenerate_sections(
        self,
        current_report: Report,
        dirty_section_ids: Set[str],
        new_evidence_packages: Optional[Dict[str, SectionEvidencePackage]] = None,
    ) -> IncrementalRegenerationResult:
        """
        Surgically regenerate only dirty sections and stitch them back into the Report model.
        Clean sections are preserved intact.
        """
        start_time = time.perf_counter()
        regenerated_sections: List[ReportSection] = []
        clean_sections: List[str] = []

        new_evidence_packages = new_evidence_packages or {}

        # Recompile sections
        final_sections: List[ReportSection] = []
        for sec in current_report.sections:
            if sec.section_id in dirty_section_ids:
                # Selective regeneration via PlannedSection
                planned = PlannedSection(
                    section_id=sec.section_id,
                    title=sec.title,
                    level=sec.level,
                    type=sec.type,
                    discovery_reason=sec.discovery_reason,
                    evidence_package=new_evidence_packages.get(sec.section_id),
                )
                fresh_sec = self.section_generator.generate_section_content(planned)
                final_sections.append(fresh_sec)
                regenerated_sections.append(fresh_sec)
            else:
                # Cached clean preservation
                final_sections.append(sec)
                clean_sections.append(sec.section_id)

        # Assemble updated Report
        updated_report = Report(
            report_id=current_report.report_id,
            title=current_report.title,
            reporting_period=current_report.reporting_period,
            subsidiary_name=current_report.subsidiary_name,
            template_name=current_report.template_name,
            created_at=current_report.created_at,
            metadata=dict(current_report.metadata),
            sections=final_sections,
        )
        updated_report.metadata["last_incremental_update"] = datetime.now(timezone.utc).isoformat()
        updated_report.metadata["regenerated_sections"] = [s.section_id for s in regenerated_sections]

        # Revalidate the full updated report
        val_report = self.validation_engine.validate_report(updated_report)

        duration = time.perf_counter() - start_time

        return IncrementalRegenerationResult(
            original_section_count=len(current_report.sections),
            regenerated_section_ids=[s.section_id for s in regenerated_sections],
            unaffected_section_ids=clean_sections,
            duration_sec=round(duration, 4),
            report=updated_report,
            validation=val_report,
        )
