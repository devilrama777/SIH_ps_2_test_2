"""
Tests for Application Settings, SettingsManager, and Settings API — Section 24 & 33 (Phase 15).
"""
import json
import pytest
from pathlib import Path

from core.domain.settings import (
    AISettings,
    ApplicationSettings,
    SecuritySettings,
    StorageSettings,
    SubsidiaryProfile,
    TemplateSettings,
)
from core.settings.manager import SettingsManager, STANDARD_CIL_SUBSIDIARIES


@pytest.fixture
def temp_settings_manager(tmp_path: Path) -> SettingsManager:
    config_file = tmp_path / "app_settings.json"
    return SettingsManager(config_path=config_file)


def test_settings_initialization_defaults(temp_settings_manager: SettingsManager):
    settings = temp_settings_manager.get_settings()
    assert settings.version == "0.1.0"
    assert settings.subsidiary.code == "CCL"
    assert "Central Coalfields" in settings.subsidiary.full_name
    assert settings.ai.active_backend == "rule_based"
    assert settings.security.strict_local_loopback is True
    assert settings.security.allow_external_network is False
    assert settings.template.default_visual_mode == "modern"
    assert temp_settings_manager.config_path.exists()


def test_settings_update_ai_and_template(temp_settings_manager: SettingsManager):
    updated = temp_settings_manager.update_settings({
        "ai": {
            "temperature": 0.05,
            "cpu_threads": 12,
            "model_name": "Llama-3.1-8B-Instruct",
        },
        "template": {
            "default_visual_mode": "classic",
            "brand_primary_color": "#002B49",
        },
    })
    assert updated.ai.temperature == 0.05
    assert updated.ai.cpu_threads == 12
    assert updated.ai.model_name == "Llama-3.1-8B-Instruct"
    assert updated.template.default_visual_mode == "classic"
    assert updated.template.brand_primary_color == "#002B49"

    # Verify persistence by reloading with a fresh manager instance
    new_manager = SettingsManager(config_path=temp_settings_manager.config_path)
    reloaded = new_manager.get_settings()
    assert reloaded.ai.temperature == 0.05
    assert reloaded.ai.cpu_threads == 12
    assert reloaded.template.default_visual_mode == "classic"


def test_select_active_subsidiary(temp_settings_manager: SettingsManager):
    updated = temp_settings_manager.select_active_subsidiary("NCL")
    assert updated.subsidiary.code == "NCL"
    assert "Northern Coalfields" in updated.subsidiary.full_name
    assert "Singrauli" in updated.subsidiary.headquarters

    with pytest.raises(ValueError, match="Unknown subsidiary code"):
        temp_settings_manager.select_active_subsidiary("XYZ_INVALID")


def test_reset_to_defaults(temp_settings_manager: SettingsManager):
    temp_settings_manager.select_active_subsidiary("SECL")
    temp_settings_manager.update_settings({"template": {"default_visual_mode": "classic"}})

    reset_settings = temp_settings_manager.reset_to_defaults()
    assert reset_settings.subsidiary.code == "CCL"
    assert reset_settings.template.default_visual_mode == "modern"


def test_available_subsidiaries_list(temp_settings_manager: SettingsManager):
    subs = temp_settings_manager.get_available_subsidiaries()
    assert len(subs) >= 8
    codes = [s.code for s in subs]
    assert "CCL" in codes
    assert "BCCL" in codes
    assert "ECL" in codes
    assert "SECL" in codes
    assert "NCL" in codes
    assert "WCL" in codes
    assert "MCL" in codes
    assert "CMPDIL" in codes
    assert "CIL_HQ" in codes


# REST API tests using FastAPI TestClient
from fastapi.testclient import TestClient
from apps.processing.server import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_settings_rest_api_lifecycle(client):
    # 1. GET /api/v1/settings
    res = client.get("/api/v1/settings")
    assert res.status_code == 200
    data = res.json()
    assert "subsidiary" in data
    assert "ai" in data
    assert "security" in data

    # 2. GET /api/v1/settings/subsidiaries
    res_subs = client.get("/api/v1/settings/subsidiaries")
    assert res_subs.status_code == 200
    subs_list = res_subs.json()
    assert len(subs_list) >= 8

    # 3. POST /api/v1/settings/subsidiaries/select
    res_sel = client.post("/api/v1/settings/subsidiaries/select", json={"code": "BCCL"})
    assert res_sel.status_code == 200
    assert res_sel.json()["subsidiary"]["code"] == "BCCL"

    # 4. POST /api/v1/settings (update)
    res_up = client.post("/api/v1/settings", json={
        "ai": {"temperature": 0.15, "cpu_threads": 6},
        "template": {"default_visual_mode": "classic"}
    })
    assert res_up.status_code == 200
    assert res_up.json()["ai"]["temperature"] == 0.15
    assert res_up.json()["ai"]["cpu_threads"] == 6
    assert res_up.json()["template"]["default_visual_mode"] == "classic"

    # 5. POST /api/v1/settings/reset
    res_rst = client.post("/api/v1/settings/reset")
    assert res_rst.status_code == 200
    assert res_rst.json()["subsidiary"]["code"] == "CCL"

