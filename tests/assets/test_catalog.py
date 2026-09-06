"""
Tests for ImageAssetCatalog — Section 18 Image Catalog & Deduplication.
"""
from PIL import Image
from core.assets.catalog import ImageAssetCatalog
from core.assets.models import ImageLayoutType


def test_asset_catalog_lifecycle_and_deduplication(tmp_path):
    db_path = tmp_path / "test_assets.db"
    catalog = ImageAssetCatalog(db_path=str(db_path))

    # Create image 1
    p1 = tmp_path / "safety_rescue_station.jpg"
    img1 = Image.new("RGB", (800, 600), color=(255, 100, 0))
    img1.save(p1)

    asset1 = catalog.register_image(str(p1), source_document_id="doc_safety_01", page_number=4)
    assert asset1.is_duplicate is False
    assert asset1.duplicate_of is None
    assert "safety" in asset1.tags

    # Register exact same image file again -> Should detect exact SHA duplicate
    asset2 = catalog.register_image(str(p1))
    assert asset2.is_duplicate is True
    assert asset2.duplicate_of == asset1.asset_id

    # Test retrieval
    fetched = catalog.get_asset(asset1.asset_id)
    assert fetched is not None
    assert fetched.filename == "safety_rescue_station.jpg"

    # Test listing
    unique_assets = catalog.list_assets(include_duplicates=False)
    assert len(unique_assets) == 1
    assert unique_assets[0].asset_id == asset1.asset_id

    # Test filter by tag
    safety_assets = catalog.list_assets(tag="safety")
    assert len(safety_assets) == 1


def test_section_image_assignment(tmp_path):
    db_path = tmp_path / "test_assets.db"
    catalog = ImageAssetCatalog(db_path=str(db_path))

    p = tmp_path / "opencast_mining_pit.png"
    img = Image.new("RGB", (1000, 750), color=(50, 50, 50))
    img.save(p)

    asset = catalog.register_image(str(p))

    assignment = catalog.assign_to_section(
        section_id="sec_ops_01",
        asset_id=asset.asset_id,
        layout_type=ImageLayoutType.WITH_CAPTION,
        caption="Heavy Earth Moving Machinery at North Karanpura Opencast Project",
    )

    assert assignment.section_id == "sec_ops_01"
    assert assignment.asset_id == asset.asset_id
    assert assignment.layout_type == ImageLayoutType.WITH_CAPTION

    assignments = catalog.get_section_assignments("sec_ops_01")
    assert len(assignments) == 1
    assert "North Karanpura" in assignments[0].caption
