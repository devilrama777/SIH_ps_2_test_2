"""
Report Agent Package — Sections 22 & 23 of Master Implementation Specification.
"""
from core.reports.agent.tools import ControlledAgentTools, ToolExecutionResult
from core.reports.agent.editing_agent import ReportEditingAgent, EditProposal, DiffLine

__all__ = [
    "ControlledAgentTools",
    "ToolExecutionResult",
    "ReportEditingAgent",
    "EditProposal",
    "DiffLine",
]
