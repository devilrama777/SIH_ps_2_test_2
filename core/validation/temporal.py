"""
Temporal Validation Engine — Section 17 of Master Implementation Specification.

Validates reporting periods, financial years, date formats, and chronological ordering.
"""
from __future__ import annotations

import re
from typing import List
from core.validation.numerical import ValidationIssue


class TemporalValidator:
    """
    Verifies temporal alignment between section claims and overall report period.
    """

    def validate_section(
        self,
        section_id: str,
        text: str,
        expected_period: str,
    ) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        # Extract 4-digit years mentioned in text (e.g. 2021, 2024, 2025)
        years = re.findall(r"\b(20\d\d)\b", text)
        expected_years = re.findall(r"\b(20\d\d)\b", expected_period)

        if expected_years:
            target_year = int(expected_years[-1])  # e.g., 2025 for 'FY 2024-25'
            # If text exclusively references an obsolete year from > 3 years ago without mentioning target year
            found_integers = [int(y) for y in years]
            if found_integers and all(y < target_year - 2 for y in found_integers):
                issues.append(
                    ValidationIssue(
                        category="temporal",
                        severity="warning",
                        section_id=section_id,
                        message=f"Temporal mismatch: section narrative exclusively cites historical dates ({years}) "
                                f"while target report period is {expected_period}.",
                        context={"found_years": years, "expected_period": expected_period},
                    )
                )

        return issues
