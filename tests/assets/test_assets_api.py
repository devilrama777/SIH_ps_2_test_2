"""
API tests for Image Intelligence endpoints in server.py (Phase 7).
"""
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from apps.processing.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_asset_api_lifecycle(client, tmp_path):
    import random
    # 1. Create a synthetic test image with unique color to avoid collision across pytest runs
    r_val = random.randint(10, 240)
    img_path = tmp_path / f"ccl_solar_farm_{r_val}.png"
    img = Image.new("RGB", (1280, 720), color=(r_val, 150, 60))
    img.save(img_path)

    # 2. Register via API
    reg_resp = client.post(
        "/api/v1/assets/register",
        json={
            "file_path": str(img_path),
            "source_document_id": "doc_solar_audit",
            "page_number": 3,
        },
    )
    assert reg_resp.status_code == 200
    asset_data = reg_resp.json()
    asset_id = asset_data["asset_id"]
    assert asset_data["width"] == 1280
    assert asset_data["height"] == 720
    assert "sustainability" in asset_data["tags"]

    # 3. Retrieve asset
    get_resp = client.get(f"/api/v1/assets/{asset_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["asset_id"] == asset_id

    # 4. List assets
    list_resp = client.get("/api/v1/assets?tag=sustainability")
    assert list_resp.status_code == 200
    assets_list = list_resp.json()
    assert any(a["asset_id"] == asset_id for a in assets_list)

    # 5. Assign to section
    assign_resp = client.post(
        "/api/v1/assets/assign",
        json={
            "section_id": "sec_solar_01",
            "asset_id": asset_id,
            "layout_type": "single_hero",
            "caption": "Ground Mounted Solar Power Array at Piparwar Area",
        },
    )
    assert assign_resp.status_code == 200
    assign_data = assign_resp.json()
    assert assign_data["section_id"] == "sec_solar_01"
    assert assign_data["layout_type"] == "single_hero"

    # 6. Retrieve assignments for section
    sec_resp = client.get("/api/v1/assets/sections/sec_solar_01")
    assert sec_resp.status_code == 200
    assignments = sec_resp.json()
    assert len(assignments) >= 1
    assert any(a["asset_id"] == asset_id for a in assignments)
