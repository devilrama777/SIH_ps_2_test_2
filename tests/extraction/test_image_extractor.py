"""
Tests for ImageExtractor using Pillow.
"""
from pathlib import Path
from PIL import Image
from core.domain.documents import DocumentType, ElementType
from core.extraction.image_extractor import ImageExtractor


def test_image_extraction(tmp_path: Path):
    """Verify image dimensions, format, and aspect ratio extraction."""
    img_path = tmp_path / "mine_site.png"
    img = Image.new("RGB", (640, 480), color=(100, 150, 200))
    img.save(str(img_path))

    extractor = ImageExtractor()
    canonical = extractor.extract(img_path)

    assert canonical.document_type == DocumentType.IMAGE
    assert len(canonical.pages) == 1
    page = canonical.pages[0]
    assert page.width == 640.0
    assert page.height == 480.0

    assert len(page.elements) == 1
    el = page.elements[0]
    assert el.type == ElementType.IMAGE
    assert el.metadata["width"] == 640
    assert el.metadata["height"] == 480
    assert el.metadata["aspect_ratio"] == round(640 / 480, 3)
