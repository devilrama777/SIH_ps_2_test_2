"""
Tests for ImageAssetAnalyzer — Section 18 Image Intelligence.
"""
from pathlib import Path
from PIL import Image
from core.assets.analyzer import ImageAssetAnalyzer
from core.assets.models import ImageLayoutType, ImageQualityGrade


def test_image_analyzer_profiling(tmp_path):
    # Create test image: 1600x900 (aspect ratio ~1.77)
    img_path = tmp_path / "ccl_solar_plant.jpg"
    img = Image.new("RGB", (1600, 900), color=(30, 144, 255))
    img.putpixel((100, 100), (255, 255, 0))
    img.save(img_path)

    asset = ImageAssetAnalyzer.analyze_image(str(img_path))
    assert asset.width == 1600
    assert asset.height == 900
    assert 1.77 <= asset.aspect_ratio <= 1.78
    assert asset.quality_grade == ImageQualityGrade.EXCELLENT
    assert asset.recommended_layout == ImageLayoutType.SINGLE_HERO
    assert len(asset.sha256_hash) == 64
    assert len(asset.phash) == 16
    assert "sustainability" in asset.tags


def test_image_analyzer_low_res(tmp_path):
    # Small thumbnail: 120x120
    img_path = tmp_path / "small_icon.png"
    img = Image.new("RGBA", (120, 120), color=(255, 0, 0, 255))
    img.save(img_path)

    asset = ImageAssetAnalyzer.analyze_image(str(img_path))
    assert asset.quality_grade == ImageQualityGrade.UNSUITABLE


def test_dhash_and_hamming_distance(tmp_path):
    from PIL import ImageDraw

    img1_path = tmp_path / "dragline_1.png"
    img1 = Image.new("RGB", (400, 400), color=(50, 50, 50))
    draw1 = ImageDraw.Draw(img1)
    draw1.rectangle([0, 0, 200, 400], fill=(200, 200, 200))
    img1.save(img1_path)

    img2_path = tmp_path / "dragline_2.png"
    img2 = Image.new("RGB", (400, 400), color=(55, 55, 55))
    draw2 = ImageDraw.Draw(img2)
    draw2.rectangle([0, 0, 200, 400], fill=(205, 205, 205))
    img2.save(img2_path)

    asset1 = ImageAssetAnalyzer.analyze_image(str(img1_path))
    asset2 = ImageAssetAnalyzer.analyze_image(str(img2_path))

    dist = ImageAssetAnalyzer.hamming_distance(asset1.phash, asset2.phash)
    assert dist <= 2
