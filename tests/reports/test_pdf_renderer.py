"""
Unit and integration tests for PdfRenderer and ReportHtmlBuilder (Phases 8 & 20).
"""
from datetime import datetime
from pathlib import Path
from core.domain.reports import NarrativeBlock, Report, ReportSection, SectionType
from core.reports.pdf.html_builder import ReportHtmlBuilder
from core.reports.pdf.renderer import PdfRenderer


def _make_sample_report(report_id: str = "ccl_report_test") -> Report:
    sec1 = ReportSection(
        section_id="sec_corp",
        title="Corporate Overview & Strategic Mandate",
        level=1,
        type=SectionType.MANDATORY,
        narrative_blocks=[
            NarrativeBlock(
                block_id="nb_01",
                text="Central Coalfields Limited operates major opencast coal projects across Jharkhand [DOC:CCL_Annual.pdf:P4].",
                confidence=1.0,
            )
        ],
    )

    sec2 = ReportSection(
        section_id="sec_ops",
        title="Operational Performance",
        level=1,
        type=SectionType.MANDATORY,
        narrative_blocks=[
            NarrativeBlock(
                block_id="nb_02",
                text="Raw coal production reached a record 84.5 MT in FY 2024-25 [COORD:Ops.xlsx:Prod:G14].",
                confidence=1.0,
            )
        ],
        tables=[
            {
                "title": "Production & Offtake Summary",
                "headers": ["Area", "Production (MT)", "Offtake (MT)"],
                "rows": [
                    ["North Karanpura", "32.4", "30.1"],
                    ["Piprawar", "28.1", "27.5"],
                    ["Total", "60.5", "57.6"],
                ],
            }
        ],
    )

    return Report(
        report_id=report_id,
        title="Annual Report 2024-25",
        reporting_period="FY 2024-25",
        subsidiary_name="Central Coalfields Limited",
        template_name="modern",
        sections=[sec1, sec2],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        version=1,
    )


def test_html_builder_both_templates():
    builder = ReportHtmlBuilder()
    report = _make_sample_report()

    # Template A: Classic
    html_classic = builder.build_html(report, template_name="classic")
    assert "<!DOCTYPE html>" in html_classic
    assert "Central Coalfields Limited" in html_classic
    assert "Table of Contents" in html_classic
    assert "Corporate Overview &amp; Strategic Mandate" in html_classic
    assert "citation-ref" in html_classic
    assert "<table>" in html_classic

    # Template B: Modern
    html_modern = builder.build_html(report, template_name="modern")
    assert "<!DOCTYPE html>" in html_modern
    assert "COAL INDIA LIMITED" in html_modern
    assert "cover-page" in html_modern


def test_pdf_renderer_execution(tmp_path):
    output_dir = tmp_path / "pdf_out"
    renderer = PdfRenderer(output_dir=str(output_dir))
    report = _make_sample_report("rep_pdf_test")

    result = renderer.render_report(report, template_name="modern")

    assert result.report_id == "rep_pdf_test"
    assert result.template_name == "modern"
    assert Path(result.pdf_path).exists()
    assert Path(result.html_path).exists()
    assert result.file_size_bytes > 0
    assert result.page_count >= 1
    assert result.render_time_seconds > 0
