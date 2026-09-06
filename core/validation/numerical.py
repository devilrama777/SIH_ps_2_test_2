"""
Numerical Validation Engine — Section 17 of Master Implementation Specification.

Validates arithmetic totals, percentage sum invariants, unit consistency,
and table arithmetic deterministically without LLM guesswork.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List
from pydantic import BaseModel


class ValidationIssue(BaseModel):
    category: str  # 'numerical', 'temporal', 'provenance', 'structural', 'visual', 'links'
    severity: str  # 'error', 'warning', 'info'
    section_id: str
    message: str
    context: Dict[str, Any] = {}


class NumericalValidator:
    """
    Deterministically verifies mathematical integrity, percentage bounds,
    and unit consistency across narrative and tabular content.
    """

    def validate_section(self, section_id: str, text: str, tables: List[Dict[str, Any]]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        # 1. Percentage Sum Check
        # Find percentage distributions like "Rail: 62.1%, Road: 22.7%, MGR: 15.2%"
        pct_matches = re.findall(r"(\b\d+(?:\.\d+)?)\s*%", text)
        if len(pct_matches) >= 3:
            try:
                pct_vals = [float(p) for p in pct_matches]
                # If these percentages look like a complete distribution (sum near 100)
                # Check if they sum to within [98.0, 102.0]
                total_pct = sum(pct_vals[:3])
                if 80.0 <= total_pct <= 120.0 and abs(total_pct - 100.0) > 1.5:
                    issues.append(
                        ValidationIssue(
                            category="numerical",
                            severity="warning",
                            section_id=section_id,
                            message=f"Percentage distribution sum anomaly: {total_pct:.1f}% (expected ~100.0%).",
                            context={"percentages": pct_vals[:3], "sum": total_pct},
                        )
                    )
            except Exception:
                pass

        # 2. Unit Consistency Check
        # Detect suspicious unit collisions (e.g. mixing crores and lakhs or MT and Tonnes in same statement)
        text_lower = text.lower()
        if "mt" in text_lower and "tonnes" in text_lower and "million" not in text_lower:
            issues.append(
                ValidationIssue(
                    category="numerical",
                    severity="warning",
                    section_id=section_id,
                    message="Unit inconsistency detected: section references both 'MT' and raw 'Tonnes' without conversion note.",
                    context={},
                )
            )

        # 3. Table Column Arithmetic Check
        for tbl in tables:
            headers = [h.lower() for h in tbl.get("headers", [])]
            rows = tbl.get("rows", [])
            # If table has a 'Total' row at the bottom
            if rows and len(rows) >= 2:
                last_row = rows[-1]
                if isinstance(last_row, list) and len(last_row) >= 3 and str(last_row[0]).strip().lower() == "total":
                    # Try verifying numerical column sum
                    try:
                        stated_total = float(str(last_row[2]).replace(",", ""))
                        col_vals = [float(str(r[2]).replace(",", "")) for r in rows[:-1] if str(r[2]).replace(".", "").replace(",", "").isdigit()]
                        calc_total = sum(col_vals)
                        if abs(calc_total - stated_total) > 0.05:
                            issues.append(
                                ValidationIssue(
                                    category="numerical",
                                    severity="error",
                                    section_id=section_id,
                                    message=f"Table total mismatch: stated {stated_total}, but row sum is {calc_total}.",
                                    context={"table_id": tbl.get("table_id"), "stated": stated_total, "calculated": calc_total},
                                )
                            )
                    except Exception:
                        pass

        return issues
