"""
Temporal Metadata Extraction & Indexing — Section 5 of Master Implementation Specification.

Supports both:
- Case A: Directory hierarchy (e.g. 2024-25/Q4/March/production.xlsx)
- Case B: Embedded in filenames (e.g. coal_production_report_march_2025.csv)

Extracts financial years, reporting quarters, reporting months, and specific event dates.
Handles snake_case, kebab-case, space-separated, and slash-separated paths.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]
MONTH_ABBRS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

MONTH_NAME_MAP = {
    "jan": "January", "feb": "February", "mar": "March", "apr": "April",
    "may": "May", "jun": "June", "jul": "July", "aug": "August",
    "sep": "September", "oct": "October", "nov": "November", "dec": "December",
    "january": "January", "february": "February", "march": "March", "april": "April",
    "june": "June", "july": "July", "august": "August", "september": "September",
    "october": "October", "november": "November", "december": "December",
}

# Boundary pattern allowing underscores, hyphens, spaces, slashes, or start/end of string
DELIM = r"(?:^|[^a-zA-Z0-9])"
DELIM_END = r"(?:$|[^a-zA-Z0-9])"

# Full ISO date: YYYY-MM-DD
ISO_DATE_PATTERN = re.compile(
    DELIM + r"((?:19|20)\d{2}[-_/](?:0[1-9]|1[0-2])[-_/](?:0[1-9]|[12]\d|3[01]))" + DELIM_END
)

# Financial Year: FY 2024-25, 2024-25, FY24-25, FY 2024-2025
# Must not be followed by another -DD which would indicate an ISO date
FY_PATTERN = re.compile(
    r"(?i)(?:fy\s*[-_]?\s*)?((?:20\d{2})[-_/](?:\d{2}|\d{4}))(?![-\d])"
)

# Quarters: Q1-Q4 or Quarter 1-4
QUARTER_PATTERN = re.compile(
    DELIM + r"(q[1-4]|quarter\s*[1-4])" + DELIM_END, re.IGNORECASE
)

# Months (full name or 3-letter abbreviation)
MONTH_PATTERN = re.compile(
    DELIM + r"(" + "|".join(MONTHS + MONTH_ABBRS) + r")" + DELIM_END, re.IGNORECASE
)

# Standalone 4-digit Year (e.g. 2024, 2025)
YEAR_PATTERN = re.compile(DELIM + r"(20[1-3]\d)" + DELIM_END)


class TemporalMetadata(BaseModel):
    """Extracted time-based classification for an ingested document."""
    financial_year: Optional[str] = None  # e.g., "2024-25"
    reporting_quarter: Optional[str] = None  # e.g., "Q4"
    reporting_month: Optional[str] = None  # e.g., "March"
    reporting_period: Optional[str] = None  # e.g., "March 2025" or "FY 2024-25 Q4"
    extracted_dates: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_method: str = "path_heuristic"


def normalize_financial_year(fy_str: str) -> str:
    """Normalize various FY representations to standard YYYY-YY (e.g. '2024-25')."""
    cleaned = re.sub(r"[^\d]", "-", fy_str)
    parts = [p for p in cleaned.split("-") if p]
    if len(parts) >= 2:
        y1, y2 = parts[0], parts[1]
        if len(y1) == 4 and len(y2) == 4:
            return f"{y1}-{y2[-2:]}"
        if len(y1) == 4 and len(y2) == 2:
            return f"{y1}-{y2}"
    return fy_str


def extract_temporal_metadata(file_path: str | Path) -> TemporalMetadata:
    """
    Extract temporal attributes from full path (incorporating Case A folder structure
    and Case B filename patterns).
    """
    path = Path(file_path)
    path_str = str(path).replace("\\", "/")
    filename = path.stem.lower()

    fy: Optional[str] = None
    quarter: Optional[str] = None
    month: Optional[str] = None
    dates: List[str] = []
    confidence = 0.0

    # 1. Search for ISO Dates first (e.g. 2025-03-31)
    iso_matches = ISO_DATE_PATTERN.findall(path_str)
    if iso_matches:
        dates.extend(iso_matches)
        confidence = max(confidence, 0.9)

    # 2. Search for Financial Year (e.g. FY 2024-25 or 2024-25)
    # Check that this match is not an ISO date prefix
    fy_matches = FY_PATTERN.findall(path_str)
    for m in fy_matches:
        # Check if this match was part of an extracted ISO date
        if any(m in d for d in dates):
            continue
        fy = normalize_financial_year(m)
        confidence = max(confidence, 0.85)
        break

    # 3. Search for Quarter (e.g. Q1, Q4, Quarter 3)
    q_matches = QUARTER_PATTERN.findall(path_str)
    if q_matches:
        raw_q = q_matches[-1].upper()
        if "QUARTER" in raw_q:
            quarter = f"Q{re.sub(r'[^0-9]', '', raw_q)}"
        else:
            quarter = raw_q
        confidence = max(confidence, 0.8)

    # 4. Search for Month in filename and path
    m_matches = MONTH_PATTERN.findall(filename)
    if not m_matches:
        m_matches = MONTH_PATTERN.findall(path_str)

    if m_matches:
        raw_month = m_matches[-1].lower()
        month = MONTH_NAME_MAP.get(raw_month)
        confidence = max(confidence, 0.75)

    # 5. Extract standalone year if FY not found
    year = None
    if not fy:
        y_matches = YEAR_PATTERN.findall(path_str)
        # Avoid year if it was part of an ISO date
        non_iso_years = [y for y in y_matches if not any(y in d for d in dates)]
        if non_iso_years:
            year = non_iso_years[-1]
            confidence = max(confidence, 0.7)

    # Synthesize human-readable reporting period
    reporting_period = None
    if month and (year or fy):
        y_label = year or (fy.split("-")[0] if fy else "")
        reporting_period = f"{month} {y_label}".strip()
    elif quarter and fy:
        reporting_period = f"FY {fy} {quarter}"
    elif fy:
        reporting_period = f"FY {fy}"
    elif month:
        reporting_period = month
    elif year:
        reporting_period = f"Year {year}"
    elif dates:
        reporting_period = dates[0]

    # Determine whether folder or filename was the primary source
    has_filename_cues = bool(
        MONTH_PATTERN.search(filename)
        or QUARTER_PATTERN.search(filename)
        or FY_PATTERN.search(filename)
        or ISO_DATE_PATTERN.search(filename)
    )
    source_method = "filename" if has_filename_cues else "folder_path"

    return TemporalMetadata(
        financial_year=fy,
        reporting_quarter=quarter,
        reporting_month=month,
        reporting_period=reporting_period,
        extracted_dates=dates,
        confidence=confidence if (fy or quarter or month or dates or year) else 0.0,
        source_method=source_method,
    )
