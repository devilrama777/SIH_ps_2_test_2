"""
Tests for Controlled Agent Tools & Security Sandbox — Section 23 of Master Implementation Plan.
"""
from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.reports.agent.tools import ControlledAgentTools, ToolRiskLevel


client = TestClient(app)


def test_controlled_tools_registry_and_metadata():
    tools = ControlledAgentTools()
    registered = tools.list_tools()

    # Must expose all 11 tools
    assert len(registered) == 11
    tool_names = {t.name for t in registered}
    expected_tools = {
        "search_documents",
        "get_source",
        "get_page",
        "get_table",
        "get_spreadsheet_range",
        "get_image",
        "update_section",
        "validate_section",
        "render_preview",
        "export_pdf",
        "upload_report",
    }
    assert expected_tools == tool_names

    # Check risk levels
    upload_meta = next(t for t in registered if t.name == "upload_report")
    assert upload_meta.risk_level == ToolRiskLevel.HIGH_RISK_EXTERNAL
    assert upload_meta.requires_human_approval is True

    search_meta = next(t for t in registered if t.name == "search_documents")
    assert search_meta.risk_level == ToolRiskLevel.READ_ONLY


def test_search_and_read_only_tools():
    tools = ControlledAgentTools()

    # 1. search_documents
    res = tools.execute_tool("search_documents", {"query": "coal production", "limit": 5})
    assert res.success is True
    assert isinstance(res.data, list)

    # 2. get_spreadsheet_range
    res_sheet = tools.execute_tool(
        "get_spreadsheet_range",
        {"workbook_name": "Financial_March.xlsx", "sheet_name": "Summary", "cell_range": "A1:D10"},
    )
    assert res_sheet.success is True
    assert res_sheet.data["workbook"] == "Financial_March.xlsx"


def test_high_risk_tool_authorization_check():
    tools = ControlledAgentTools()

    # 1. Reject without authorization token
    res_denied = tools.execute_tool(
        "upload_report",
        {"report_id": "rep_test_01", "destination_target": "https://cil.gov.in/reports"},
    )
    assert res_denied.success is False
    assert res_denied.requires_approval is True
    assert "authorization" in res_denied.error.lower()

    # 2. Succeed with valid human authorization token
    res_approved = tools.execute_tool(
        "upload_report",
        {"report_id": "rep_test_01", "destination_target": "https://cil.gov.in/reports"},
        authorization_token="AUTH_CIL_DIRECTOR_APPROVED",
    )
    assert res_approved.success is True
    assert res_approved.data["authorized"] is True


def test_path_traversal_guard():
    tools = ControlledAgentTools()

    # Attempt path escape in get_source
    res = tools.execute_tool("get_source", {"document_id": "../../../../../etc/passwd"})
    assert res.success is False
    assert "violation" in res.error.lower() or "not found" in res.error.lower()


def test_rest_api_agent_tools_endpoints():
    # 1. GET /api/v1/agent/tools
    resp = client.get("/api/v1/agent/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 11

    # 2. POST /api/v1/agent/tools/execute for read-only tool
    payload = {
        "tool_name": "search_documents",
        "arguments": {"query": "safety target", "limit": 3},
    }
    resp2 = client.post("/api/v1/agent/tools/execute", json=payload)
    assert resp2.status_code == 200
    assert resp2.json()["success"] is True

    # 3. POST /api/v1/agent/tools/execute for unauthorized high-risk tool
    payload_high_risk = {
        "tool_name": "upload_report",
        "arguments": {"report_id": "rep_001", "destination_target": "portal"},
    }
    resp3 = client.post("/api/v1/agent/tools/execute", json=payload_high_risk)
    assert resp3.status_code == 403
