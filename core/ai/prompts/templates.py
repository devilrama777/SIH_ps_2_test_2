"""
Prompt Templates and System Directives for CIL Local AI Gateway.

Strictly enforces:
1. Grounded factual generation — no hallucinations.
2. Mandatory provenance citations for every factual statement: [DOC:xxx:Pxx] or [COORD:xxx:Sheet:Cell].
3. Structured output formatting (JSON / constrained text).
"""
from typing import List, Optional


SYSTEM_PROMPT_FACTUAL = """You are the local document intelligence and report generation assistant for Coal India Limited (CIL) subsidiary annual reports.
You operate in a strictly air-gapped, local environment.
All statements, numerical totals, dates, and findings must be directly grounded in the provided source evidence.
You MUST cite the source document reference and page or coordinate for every factual claim using bracketed notation: [DOC:filename:P{page}] or [COORD:workbook:sheet:cell].
Do not invent figures, dates, or organizational projects not present in the evidence.
If information is missing, state clearly that it is unavailable in the current evidence corpus."""


SYSTEM_PROMPT_REPORT_PLANNER = """You are a senior corporate report architect for Coal India Limited (CIL).
Your role is to propose a structured chapter and section hierarchy for the subsidiary annual performance report.
Integrate both mandatory recurring corporate sections and dynamic sections discovered from current-year evidence.
Every proposed section must specify its required evidence topics and reference source documents."""


SYSTEM_PROMPT_AGENTIC_EDITOR = """You are an agentic corporate editor for CIL annual reports.
Your task is to revise or refine a report section according to executive review instructions.
You must preserve all existing valid citations and incorporate new evidence packages strictly with verified provenance references.
Do not introduce unsubstantiated assertions."""


def build_summarize_prompt(evidence_text: str, focus_areas: Optional[List[str]] = None) -> str:
    focus_str = f"Focus particularly on: {', '.join(focus_areas)}." if focus_areas else ""
    return f"""Summarize the following evidence for inclusion in the CIL subsidiary annual report.
{focus_str}

Preserve exact metrics, tonnages, financial figures, dates, and percentages.
Append exact evidence citations to each bullet point.

Evidence:
{evidence_text}

Summary:"""


def build_classify_prompt(text: str, categories: List[str]) -> str:
    cats_str = ", ".join(categories)
    return f"""Classify the following text into exactly ONE of these categories:
Categories: {cats_str}

Text:
{text}

Category:"""


def build_plan_prompt(reference_structure: str, current_evidence_summary: str) -> str:
    return f"""Analyze the previous year reference report structure alongside current-year evidence to formulate a dynamic report plan.

Reference Report Structure:
{reference_structure}

Current Period Evidence Summary:
{current_evidence_summary}

Provide a JSON plan with report_title, reporting_period, and chapters list."""


def build_edit_section_prompt(section_content: str, evidence_package: str, instructions: str) -> str:
    return f"""Apply the following editorial instructions to the section content, using the provided evidence package.

Section Content:
{section_content}

Evidence Package:
{evidence_package}

Editorial Instructions:
{instructions}

Revised Section (preserving citations):"""
