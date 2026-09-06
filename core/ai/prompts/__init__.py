"""
AI Gateway Prompts and Templates.
"""
from core.ai.prompts.templates import (
    SYSTEM_PROMPT_FACTUAL,
    SYSTEM_PROMPT_REPORT_PLANNER,
    SYSTEM_PROMPT_AGENTIC_EDITOR,
    build_summarize_prompt,
    build_classify_prompt,
    build_plan_prompt,
    build_edit_section_prompt,
)

__all__ = [
    "SYSTEM_PROMPT_FACTUAL",
    "SYSTEM_PROMPT_REPORT_PLANNER",
    "SYSTEM_PROMPT_AGENTIC_EDITOR",
    "build_summarize_prompt",
    "build_classify_prompt",
    "build_plan_prompt",
    "build_edit_section_prompt",
]
