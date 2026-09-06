"""
Tests for OCR Benchmark Harness and REST API Endpoints — Section 7 & 34 of Master Implementation Plan.
"""
from __future__ import annotations

import base64
import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from apps.processing.server import app
from core.extraction.ocr.benchmark import OCRBenchmarkHarness, OCRBenchmarkReport
from core.extraction.ocr.manager import MultiEngineOCRManager


client = TestClient(app)


def test_ocr_benchmark_harness_execution():
    manager = MultiEngineOCRManager()
    harness = OCRBenchmarkHarness(ocr_manager=manager)

    report = harness.run_benchmark(sample_pages=1, engine_names=["pymupdf_raster_ocr", "paddleocr_ppstructure_v3"])
    assert isinstance(report, OCRBenchmarkReport)
    assert report.sample_pages_count == 1
    assert "pymupdf_raster_ocr" in report.results

    res = report.results["pymupdf_raster_ocr"]
    assert res.pages_processed == 1
    assert res.pages_per_second > 0.0
    assert res.avg_confidence > 0.0
    assert res.ram_usage_mb > 0.0
    assert report.recommended_default in ["pymupdf_raster_ocr", "paddleocr_ppstructure_v3"]


def test_api_list_and_select_ocr_engines():
    # 1. GET /api/v1/ocr/engines
    resp = client.get("/api/v1/ocr/engines")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_engine" in data
    assert "engines" in data
    assert len(data["engines"]) >= 3

    # 2. POST /api/v1/ocr/engines/select
    resp2 = client.post("/api/v1/ocr/engines/select", json={"engine_name": "pymupdf_raster_ocr"})
    assert resp2.status_code == 200
    assert resp2.json()["active_engine"] == "pymupdf_raster_ocr"

    # 3. Bad engine selection
    resp3 = client.post("/api/v1/ocr/engines/select", json={"engine_name": "invalid_cloud_api"})
    assert resp3.status_code == 400


def test_api_process_ocr_page():
    img = Image.new("RGB", (400, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 30), "TEST OCR API PAYLOAD", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")

    payload = {
        "image_base64": b64_str,
        "page_number": 1,
        "engine_name": "pymupdf_raster_ocr",
    }
    resp = client.post("/api/v1/ocr/process-page", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["page_number"] == 1
    assert "lines" in data
    assert "overall_confidence" in data


def test_api_ocr_benchmark_endpoint():
    payload = {
        "sample_pages": 1,
        "engines": ["pymupdf_raster_ocr"],
    }
    resp = client.post("/api/v1/ocr/benchmark", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["sample_pages_count"] == 1
    assert "pymupdf_raster_ocr" in data["results"]
