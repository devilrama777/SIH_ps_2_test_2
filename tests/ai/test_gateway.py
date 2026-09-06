"""
Unit tests for LocalAIGateway operations and provenance citations.
"""
from core.ai.gateway.local_gateway import LocalAIGateway
from core.ai.backends.rule_based import RuleBasedLocalBackend


def test_ai_gateway_generate_and_citation_extraction():
    gateway = LocalAIGateway(RuleBasedLocalBackend())
    res = gateway.generate("Summarize findings from [DOC:FY25_audit.pdf:P14] with 1245 MT.")

    assert res.tokens_generated > 0
    assert res.latency_seconds >= 0.0
    assert res.grounding_metadata["is_grounded"] is True
    assert "[DOC:FY25_audit.pdf:P14]" in res.grounding_metadata["cited_references"]


def test_ai_gateway_chat():
    gateway = LocalAIGateway(RuleBasedLocalBackend())
    messages = [
        {"role": "system", "content": "You are a CIL report reviewer."},
        {"role": "user", "content": "Review coal dispatch from [DOC:dispatch.pdf:P02]."},
    ]
    res = gateway.chat(messages)
    assert len(res.content) > 0
    assert res.model_name == "local-rule-engine-v1"


def test_ai_gateway_summarize():
    gateway = LocalAIGateway(RuleBasedLocalBackend())
    evidence = "Production reached 773.6 MT in [DOC:CIL_Annual_Report.pdf:P05]."
    res = gateway.summarize(evidence, focus_areas=["production"])

    assert len(res.content) > 0
    assert "[DOC:CIL_Annual_Report.pdf:P05]" in res.content


def test_ai_gateway_classify():
    gateway = LocalAIGateway(RuleBasedLocalBackend())
    text = "The company planted 2 million saplings for environmental reclamation."
    category = gateway.classify(text, ["Financials", "Environmental", "Governance"])

    assert category == "Environmental"


def test_ai_gateway_extract_semantics():
    gateway = LocalAIGateway(RuleBasedLocalBackend())
    schema = {"production_mt": 0.0, "subsidiary_name": ""}
    data = gateway.extract_semantics(
        "production_mt: 773.60 subsidiary_name: CCL",
        schema=schema,
    )
    assert "production_mt" in data
    assert "subsidiary_name" in data


def test_ai_gateway_plan_report():
    gateway = LocalAIGateway(RuleBasedLocalBackend())
    plan = gateway.plan_report(
        reference_structure={"chapters": ["Production", "Financials"]},
        current_evidence_summary={"total_records": 150},
    )

    assert "chapters" in plan
    assert len(plan["chapters"]) >= 3
    assert plan["report_title"] is not None


def test_ai_gateway_edit_section():
    gateway = LocalAIGateway(RuleBasedLocalBackend())
    res = gateway.edit_section(
        section_content="Draft production was 700 MT.",
        evidence_package={"verified_figure": "773.6 MT [DOC:audit.pdf:P10]"},
        instructions="Update draft to audited 773.6 MT.",
    )

    assert len(res.content) > 0
    assert res.finish_reason == "stop"
