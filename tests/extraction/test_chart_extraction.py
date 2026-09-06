"""
Unit Tests for Phase 32: Layout Intelligence & Chart OCR Analysis.
Section 9, 10 & 18 of Master Implementation Specification.
"""
from __future__ import annotations

from pathlib import Path
import pytest
from PIL import Image, ImageDraw

from core.domain.documents import (
    BoundingBox,
    DocumentElement,
    ElementType,
)
from core.extraction.chart_extractor import (
    ChartDataPoint,
    ChartExtractor,
    ChartMetadata,
)


@pytest.fixture
def chart_image_path(tmp_path: Path) -> Path:
    """Creates a synthetic chart image with bar graphics and text."""
    p = tmp_path / "synthetic_bar_chart.png"
    img = Image.new("RGB", (400, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw axis lines
    draw.line([(50, 250), (350, 250)], fill=(0, 0, 0), width=2)
    draw.line([(50, 250), (50, 50)], fill=(0, 0, 0), width=2)

    # Draw bars
    draw.rectangle([(80, 150), (120, 250)], fill=(30, 144, 255))
    draw.rectangle([(160, 100), (200, 250)], fill=(30, 144, 255))
    draw.rectangle([(240, 70), (280, 250)], fill=(30, 144, 255))

    img.save(p)
    return p


def test_chart_heuristic(chart_image_path: Path):
    extractor = ChartExtractor()
    with Image.open(chart_image_path) as img:
        is_chart = extractor.is_chart_heuristic(img)
        assert is_chart is True


def test_classify_chart_type():
    extractor = ChartExtractor()
    assert extractor.classify_chart_type("Raw Coal Production Bar Chart FY24") == "bar"
    assert extractor.classify_chart_type("Monthly Offtake Trajectory and Trend") == "line"
    assert extractor.classify_chart_type("Percentage Share Distribution %") == "pie"
    assert extractor.classify_chart_type("Cumulative Overburden Removal Area Chart") == "area"


def test_parse_data_points_from_ocr():
    extractor = ChartExtractor()
    ocr_sample = (
        "CIL Coal Production Overview\n"
        "Piparwar: 14.5 MT\n"
        "Rajrappa: 8.2 MT\n"
        "Ashoka: 21.0 MT\n"
    )
    points = extractor.parse_data_points_from_ocr(ocr_sample)
    assert len(points) == 3
    assert points[0].label == "Piparwar"
    assert points[0].value == 14.5
    assert points[0].unit == "MT"
    assert points[1].label == "Rajrappa"
    assert points[1].value == 8.2


def test_enhance_element_to_chart():
    extractor = ChartExtractor()
    el = DocumentElement(
        element_id="el_chart_01",
        document_id="doc_test",
        type=ElementType.IMAGE,
        text="Figure 4: Annual Coal Production Bar Chart - Piparwar Mine: 15.2 MT",
    )

    enhanced = extractor.enhance_element(el)
    assert enhanced.type == ElementType.CHART
    assert "chart_metadata" in enhanced.metadata
    meta = enhanced.metadata["chart_metadata"]
    assert meta["chart_type"] == "bar"
    assert len(meta["data_points"]) >= 1
