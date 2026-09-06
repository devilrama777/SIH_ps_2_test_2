"""
Tests for Image Intelligence System & Asset Catalog — Section 18 of Master Implementation Specification.
"""
from __future__ import annotations

from pathlib import Path
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.reports.image_intelligence import (
    DeterministicLayoutEngine,
    ImageAsset,
    ImageAssetAnalyzer,
    ImageAssetCatalog,
    ImageLayoutType,
    ImageQualityGrade,
)

client = TestClient(app)


@pytest.fixture
def sample_image_files(tmp_path: Path):
    """Generates synthetic test images for image intelligence testing."""
    img1_path = tmp_path / "dragline_excavator_coal_mine.png"
    img1 = Image.new("RGB", (800, 600), color=(120, 80, 40))
    img1.save(img1_path)

    # Near duplicate of img1
    img2_path = tmp_path / "dragline_excavator_variant.png"
    img2 = Image.new("RGB", (800, 600), color=(122, 82, 42))
    img2.save(img2_path)

    # Different image: Green tree plantation
    img3_path = tmp_path / "tree_plantation_eco_reclamation.png"
    img3 = Image.new("RGB", (1024, 768), color=(34, 139, 34))
    img3.save(img3_path)

    return img1_path, img2_path, img3_path


def test_image_analyzer_dhash_and_duplicates(sample_image_files):
    img1_path, img2_path, img3_path = sample_image_files

    asset1 = ImageAssetAnalyzer.analyze(str(img1_path))
    asset2 = ImageAssetAnalyzer.analyze(str(img2_path))
    asset3 = ImageAssetAnalyzer.analyze(str(img3_path))

    assert asset1.width == 800
    assert asset1.height == 600
    assert asset1.quality_grade in [ImageQualityGrade.ACCEPTABLE, ImageQualityGrade.EXCELLENT]
    assert "mining" in asset1.tags
    assert "sustainability" in asset3.tags

    # Perceptual duplicate check
    dist_1_2 = ImageAssetAnalyzer.hamming_distance(asset1.phash, asset2.phash)
    dist_1_3 = ImageAssetAnalyzer.hamming_distance(asset1.phash, asset3.phash)

    # Near duplicates have small hamming distance
    assert dist_1_2 <= 5
    # Distinct topic images have higher distance
    assert dist_1_3 >= dist_1_2


def test_image_asset_catalog_sqlite(tmp_path: Path, sample_image_files):
    img1_path, img2_path, img3_path = sample_image_files
    db_path = tmp_path / "test_assets.db"
    catalog = ImageAssetCatalog(db_path=str(db_path))

    asset1 = catalog.register_image(str(img1_path))
    asset2 = catalog.register_image(str(img2_path))
    asset3 = catalog.register_image(str(img3_path))

    # 1. Retrieve
    retrieved = catalog.get_asset(asset1.asset_id)
    assert retrieved is not None
    assert retrieved.filename == img1_path.name
    assert "mining" in retrieved.tags

    # 2. Duplicate detection in catalog
    dupes = catalog.find_duplicates(asset1, hamming_threshold=5)
    assert len(dupes) >= 1
    assert dupes[0][0].asset_id == asset2.asset_id

    # 3. Topic/Tag search
    env_assets = catalog.list_assets(tag="sustainability")
    assert len(env_assets) >= 1
    assert env_assets[0].asset_id == asset3.asset_id


def test_deterministic_layout_engine(sample_image_files):
    img1_path, img2_path, img3_path = sample_image_files
    assets = [
        ImageAssetAnalyzer.analyze(str(img1_path)),
        ImageAssetAnalyzer.analyze(str(img2_path)),
        ImageAssetAnalyzer.analyze(str(img3_path)),
    ]

    # 1. Hero layout
    hero_pres = DeterministicLayoutEngine.resolve_layout(
        section_type="executive_summary",
        available_assets=assets,
        preferred_layout=ImageLayoutType.SINGLE_HERO,
    )
    assert hero_pres.layout_type == ImageLayoutType.SINGLE_HERO
    assert len(hero_pres.slots) == 1
    assert hero_pres.slots[0].width_percent == 100.0

    # 2. Two-column layout
    col_pres = DeterministicLayoutEngine.resolve_layout(
        section_type="operational_review",
        available_assets=assets,
        preferred_layout=ImageLayoutType.TWO_COLUMN_TEXT_IMAGE,
    )
    assert col_pres.layout_type == ImageLayoutType.TWO_COLUMN_TEXT_IMAGE
    assert len(col_pres.slots) == 1
    assert col_pres.slots[0].alignment == "right"


def test_image_intelligence_rest_api(sample_image_files):
    img1_path, _, _ = sample_image_files

    # 1. POST /api/v1/images/analyze
    payload = {
        "file_path": str(img1_path),
        "document_id": "doc_test_api_01",
        "page_number": 2,
    }
    resp = client.post("/api/v1/images/analyze", json=payload)
    assert resp.status_code == 200
    asset_data = resp.json()
    assert asset_data["asset_id"].startswith("img_")
    asset_id = asset_data["asset_id"]

    # 2. GET /api/v1/images/catalog
    list_resp = client.get("/api/v1/images/catalog")
    assert list_resp.status_code == 200
    catalog = list_resp.json()
    assert any(a["asset_id"] == asset_id for a in catalog)

    # 3. POST /api/v1/images/layout-resolve
    resolve_payload = {
        "section_type": "operational_performance",
        "asset_ids": [asset_id],
        "preferred_layout": "single_hero",
    }
    layout_resp = client.post("/api/v1/images/layout-resolve", json=resolve_payload)
    assert layout_resp.status_code == 200
    layout_data = layout_resp.json()
    assert layout_data["layout_type"] == "single_hero"
    assert len(layout_data["slots"]) == 1
