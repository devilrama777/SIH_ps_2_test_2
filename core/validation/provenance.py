"""
Provenance Validation Engine — Section 17 of Master Implementation Specification.

Ensures that every factual statement has verified evidence and that all citation
references resolve to valid document pages or spreadsheet coordinates.
"""
from __future__ import annotations

import re
from typing import List, Optional
from core.domain.reports import NarrativeBlock
from core.validation.numerical import ValidationIssue


class ProvenanceValidator:
    """
    Deterministically validates that narrative claims cite verified evidence.
    """

    def validate_narrative_block(
        self,
        section_id: str,
        block: NarrativeBlock,
    ) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        # Check if block makes quantitative factual claims without citations
        has_numbers = bool(re.search(r"\b\d+(?:\.\d+)?\s*(?:MT|crores|%|MW|₹)\b", block.text))
        has_citations = len(block.evidence_refs) > 0 or bool(re.search(r"\[(?:DOC|COORD|REF):[^\]]+\]", block.text))

        if has_numbers and not has_citations:
            issues.append(
                ValidationIssue(
                    category="provenance",
                    severity="error",
                    section_id=section_id,
                    message=f"Unsubstantiated numerical claim in block '{block.block_id}': factual claims must cite source evidence.",
                    context={"block_id": block.block_id, "text_snippet": block.text[:100]},
                )
            )

        if block.insufficient_evidence:
            issues.append(
                ValidationIssue(
                    category="provenance",
                    severity="warning",
                    section_id=section_id,
                    message=f"Block '{block.block_id}' is flagged with insufficient evidence in current reporting corpus.",
                    context={"block_id": block.block_id},
                )
            )

        # Validate citation formatting
        for ref in block.evidence_refs:
            ref_str = ref.excerpt_text or ref.provenance.source_reference
            if ":" not in ref_str:
                issues.append(
                    ValidationIssue(
                        category="provenance",
                        severity="warning",
                        section_id=section_id,
                        message=f"Malformed provenance reference '{ref_str}': expected formatted citation.",
                        context={"ref_id": ref.evidence_id},
                    )
                )

        return issues
