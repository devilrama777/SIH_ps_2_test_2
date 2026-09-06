"""
Layout Intelligence & Chart OCR Analysis Engine.
Section 9, 10 & 18 of Master Implementation Specification.

Detects, classifies, and extracts structured numerical data and labels
from embedded charts, graphs, and visual figures in mining reports.
Runs 100% locally with Pillow and local OCR integration.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from PIL import Image

from core.domain.documents import (
    BoundingBox,
    DocumentElement,
    ElementType,
)
from core.extraction.ocr.manager import OCRManager


class ChartDataPoint(BaseModel):
    """Structured data point extracted from a chart or graph."""
    series: Optional[str] = None
    label: str
    value: float
    unit: Optional[str] = None


class ChartMetadata(BaseModel):
    """Structured metadata representing an analyzed chart/graph."""
    title: Optional[str] = None
    chart_type: str = "unknown"  # "bar", "line", "pie", "area", "unknown"
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    legend_labels: List[str] = Field(default_factory=list)
    data_points: List[ChartDataPoint] = Field(default_factory=list)
    ocr_raw_text: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ChartExtractor:
    """
    Local layout intelligence engine that identifies charts/plots
    and extracts structured time series / categorical metrics.
    """

    def __init__(self, ocr_manager: Optional[OCRManager] = None) -> None:
        self.ocr_manager = ocr_manager or OCRManager()

    def is_chart_heuristic(self, img: Image.Image) -> bool:
        """
        Determines whether an image is likely a chart or graph using
        color histogram diversity and aspect ratio heuristics.
        """
        w, h = img.size
        if w < 50 or h < 50:
            return False

        # Convert to RGB if needed
        rgb_img = img.convert("RGB")
        # Check standard aspect ratios common for analytical figures
        aspect = w / h
        if aspect < 0.25 or aspect > 4.0:
            return False

        # Check unique color counts in thumbnail
        thumb = rgb_img.resize((100, 100))
        colors = thumb.getcolors(maxcolors=10000)
        num_colors = len(colors) if colors else 10000

        # Natural photos typically have > 3000 distinct colors in a 100x100 thumb
        # Synthesized charts, diagrams, and plots typically have fewer distinct colors (e.g. 50-2500)
        # and sharp contrast boundaries.
        return 30 <= num_colors <= 3500

    def classify_chart_type(self, text: str) -> str:
        """Infer chart type from associated textual cues or titles."""
        text_lower = text.lower()
        if any(k in text_lower for k in ["bar chart", "production bar", "histogram", "column"]):
            return "bar"
        if any(k in text_lower for k in ["line graph", "trend", "trajectory", "monthly curve"]):
            return "line"
        if any(k in text_lower for k in ["pie chart", "share of", "percentage share", "distribution %"]):
            return "pie"
        if any(k in text_lower for k in ["area chart", "cumulative"]):
            return "area"
        return "bar"  # default standard for CIL production reports

    def parse_data_points_from_ocr(self, ocr_text: str) -> List[ChartDataPoint]:
        """
        Extract numerical series from OCR text extracted from chart axis/data labels.
        Example: 'FY 2023-24: 85.4 MT' or 'Piparwar 12.5'
        """
        data_points: List[ChartDataPoint] = []
        lines = [ln.strip() for ln in ocr_text.splitlines() if ln.strip()]

        # Pattern: [Label or Period] followed by a number
        pattern = re.compile(
            r"([A-Za-z0-9\s\-_/]+?)[\s:=–-]+(\d+(?:\.\d+)?)\s*([A-Za-z%]*)"
        )

        for line in lines:
            m = pattern.search(line)
            if m:
                label = m.group(1).strip()
                val_str = m.group(2).strip()
                unit = m.group(3).strip() or None
                try:
                    val = float(val_str)
                    if label and len(label) < 60:
                        data_points.append(
                            ChartDataPoint(
                                label=label,
                                value=val,
                                unit=unit or ("MT" if "mt" in line.lower() else None),
                            )
                        )
                except ValueError:
                    continue

        return data_points

    def extract_from_image(self, image_path: Path | str) -> ChartMetadata:
        """Extract chart metadata and metrics from an image file."""
        path = Path(image_path)
        if not path.exists():
            return ChartMetadata(confidence=0.0)

        with Image.open(path) as img:
            is_chart = self.is_chart_heuristic(img)

        # Run OCR to get text
        image_bytes = path.read_bytes()
        ocr_result = self.ocr_manager.process_page_image(image_bytes=image_bytes, page_number=1)
        ocr_text = "\n".join(l.text for l in ocr_result.lines) if ocr_result else ""

        title = None
        lines = [l.strip() for l in ocr_text.splitlines() if l.strip()]
        if lines:
            # Title is typically the first non-trivial line
            title = lines[0][:100]

        chart_type = self.classify_chart_type(ocr_text)
        data_points = self.parse_data_points_from_ocr(ocr_text)

        confidence = 0.85 if is_chart else 0.40
        if data_points:
            confidence = min(0.95, confidence + 0.1)

        return ChartMetadata(
            title=title,
            chart_type=chart_type,
            data_points=data_points,
            ocr_raw_text=ocr_text,
            confidence=confidence,
        )

    def enhance_element(
        self,
        element: DocumentElement,
        image_path: Optional[Path | str] = None,
    ) -> DocumentElement:
        """
        Enhance a generic DocumentElement into a CHART element if chart attributes
        are identified.
        """
        if image_path and Path(image_path).exists():
            meta = self.extract_from_image(image_path)
            if meta.confidence >= 0.5:
                element.type = ElementType.CHART
                element.metadata["chart_metadata"] = meta.model_dump()
                if meta.title and not element.text:
                    element.text = f"Chart: {meta.title}"
        elif element.text and any(k in element.text.lower() for k in ["chart", "graph", "trend", "figure"]):
            element.type = ElementType.CHART
            meta = ChartMetadata(
                title=element.text[:80],
                chart_type=self.classify_chart_type(element.text),
                data_points=self.parse_data_points_from_ocr(element.text),
                confidence=0.75,
            )
            element.metadata["chart_metadata"] = meta.model_dump()

        return element
