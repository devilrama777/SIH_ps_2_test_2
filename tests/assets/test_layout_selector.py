"""
Tests for DeterministicLayoutSelector — Section 18 Image Layouts.
"""
from datetime import datetime
from core.assets.layout_selector import DeterministicLayoutSelector
from core.assets.models import ImageAsset, ImageLayoutType, ImageQualityGrade


def _make_dummy_asset(asset_id: str, width: int, height: int, aspect_ratio: float) -> ImageAsset:
    return ImageAsset(
        asset_id=asset_id,
        filename=f"{asset_id}.png",
        file_path=f"C:/data/{asset_id}.png",
        format="PNG",
        width=width,
        height=height,
        aspect_ratio=aspect_ratio,
        file_size_bytes=10240,
        sha256_hash="dummyhash",
        quality_grade=ImageQualityGrade.ACCEPTABLE,
        caption="Sample Caption",
        created_at=datetime.utcnow(),
    )


def test_layout_selector_rules():
    # 1. Panoramic -> SINGLE_HERO
    hero_asset = _make_dummy_asset("hero_1", 1600, 800, 2.0)
    layout = DeterministicLayoutSelector.select_layout([hero_asset])
    assert layout == ImageLayoutType.SINGLE_HERO

    # 2. Portrait -> TWO_COLUMN_TEXT_IMAGE
    portrait_asset = _make_dummy_asset("port_1", 600, 900, 0.67)
    layout = DeterministicLayoutSelector.select_layout([portrait_asset])
    assert layout == ImageLayoutType.TWO_COLUMN_TEXT_IMAGE

    # 3. 4 Images -> GRID_2X2
    grid_assets = [_make_dummy_asset(f"grid_{i}", 600, 450, 1.33) for i in range(4)]
    layout = DeterministicLayoutSelector.select_layout(grid_assets)
    assert layout == ImageLayoutType.GRID_2X2

    # 4. HTML generation test
    html_hero = DeterministicLayoutSelector.generate_html_container([hero_asset], ImageLayoutType.SINGLE_HERO)
    assert "report-image-hero" in html_hero
    assert "<figcaption>Sample Caption</figcaption>" in html_hero

    html_grid = DeterministicLayoutSelector.generate_html_container(grid_assets, ImageLayoutType.GRID_2X2)
    assert "report-image-grid-2x2" in html_grid
    assert html_grid.count("grid-item") == 4
