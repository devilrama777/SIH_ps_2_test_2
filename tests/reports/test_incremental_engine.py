import pytest
from core.domain.reports import Report, ReportSection, NarrativeBlock
from core.domain.evidence import EvidenceReference, ProvenanceRecord
from core.reports.incremental_engine import SectionDependencyGraph, IncrementalReportEngine


def test_section_dependency_graph_transitive_resolution():
    graph = SectionDependencyGraph()

    # Section 1: Production (depends on coal_prod.xlsx)
    graph.register_dependency("sec_prod", "ccl_coal_prod.xlsx")

    # Section 2: Financial (depends on audit_statement.txt)
    graph.register_dependency("sec_fin", "audit_statement.txt")

    # Section 3: Executive Summary (depends on sec_prod and sec_fin)
    graph.register_section_dependency("sec_exec", "sec_prod")
    graph.register_section_dependency("sec_exec", "sec_fin")

    # Section 4: CSR (independent, depends on csr_report.docx)
    graph.register_dependency("sec_csr", "csr_report.docx")

    # Case 1: Only coal_prod.xlsx changes -> sec_prod and sec_exec should be dirty
    affected = graph.get_affected_sections(["ccl_coal_prod.xlsx"])
    assert affected == {"sec_prod", "sec_exec"}
    assert "sec_fin" not in affected
    assert "sec_csr" not in affected

    # Case 2: Only csr_report.docx changes -> only sec_csr should be dirty
    affected_csr = graph.get_affected_sections(["csr_report.docx"])
    assert affected_csr == {"sec_csr"}


def test_build_dependency_graph_from_report():
    report = Report(
        report_id="rep_test_1",
        title="CCL Annual Report FY24",
        reporting_period="FY 2023-24",
        subsidiary_name="Central Coalfields Limited",
        sections=[
            ReportSection(
                section_id="sec_exec",
                title="Executive Summary",
                level=1,
                narrative_blocks=[NarrativeBlock(block_id="nb_1", text="Overall summary")],
            ),
            ReportSection(
                section_id="sec_prod",
                title="Production Performance",
                level=1,
                source_refs=["ccl_production.xlsx"],
                narrative_blocks=[
                    NarrativeBlock(
                        block_id="nb_2",
                        text="Total production reached 84.5 MT.",
                        evidence_refs=[
                            EvidenceReference(
                                evidence_id="ev_1",
                                provenance=ProvenanceRecord(
                                    provenance_id="prov_1",
                                    document_id="ccl_production.xlsx",
                                    source_reference="ccl_production.xlsx",
                                ),
                                excerpt_text="84.5 MT",
                            )
                        ],
                    )
                ],
            ),
            ReportSection(
                section_id="sec_env",
                title="Environmental Management",
                level=1,
                source_refs=["env_compliance.pdf"],
                narrative_blocks=[
                    NarrativeBlock(
                        block_id="nb_3",
                        text="Afforestation drives planted 200,000 saplings.",
                        evidence_refs=[
                            EvidenceReference(
                                evidence_id="ev_2",
                                provenance=ProvenanceRecord(
                                    provenance_id="prov_2",
                                    document_id="env_compliance.pdf",
                                    source_reference="env_compliance.pdf",
                                ),
                                excerpt_text="200,000 saplings",
                            )
                        ],
                    )
                ],
            ),
        ],
    )

    graph = SectionDependencyGraph.build_from_report(report)
    dict_repr = graph.to_dict()

    assert "sec_prod" in dict_repr["section_to_sources"]
    assert "ccl_production.xlsx" in dict_repr["section_to_sources"]["sec_prod"]
    assert "env_compliance.pdf" in dict_repr["section_to_sources"]["sec_env"]

    # When env_compliance.pdf changes, sec_env and sec_exec are affected
    dirty = graph.get_affected_sections(["env_compliance.pdf"])
    assert "sec_env" in dirty
    assert "sec_exec" in dirty  # Executive summary depends on environmental


def test_incremental_engine_selective_regeneration():
    report = Report(
        report_id="rep_test_inc",
        title="CCL Incremental Report",
        reporting_period="FY 2023-24",
        subsidiary_name="Central Coalfields Limited",
        sections=[
            ReportSection(
                section_id="sec_1",
                title="Section One",
                level=1,
                narrative_blocks=[NarrativeBlock(block_id="nb_1", text="Old content one")],
            ),
            ReportSection(
                section_id="sec_2",
                title="Section Two",
                level=1,
                narrative_blocks=[NarrativeBlock(block_id="nb_2", text="Preserved content two")],
            ),
        ],
    )

    engine = IncrementalReportEngine()

    # Invalidate sec_1 only
    result = engine.regenerate_sections(
        current_report=report,
        dirty_section_ids={"sec_1"},
    )

    assert result.original_section_count == 2
    assert result.regenerated_section_ids == ["sec_1"]
    assert result.unaffected_section_ids == ["sec_2"]
    assert result.duration_sec >= 0.0

    # Section 2 preserved verbatim
    assert result.report.sections[1].narrative_blocks[0].text == "Preserved content two"
    assert "last_incremental_update" in result.report.metadata
