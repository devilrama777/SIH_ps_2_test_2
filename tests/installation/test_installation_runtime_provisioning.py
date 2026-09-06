"""
Tests for Master Plan Section 38: Unified Local Installation & Runtime Provisioning.

Validates:
1. Complete 5-tier installation stack inspection:
   - Application
   - Python runtime & dependencies
   - Document processing & OCR toolchains
   - Local model runtime
   - Selected model files
2. Model catalog inspection with licensing terms and resource requirements.
3. Strict license acceptance requirement before model download.
4. Cryptographic SHA-256 verification during offline model imports.
5. Active model switching and integration with local AI settings.
6. All Section 38 REST API endpoints via TestClient.
"""

from pathlib import Path
import hashlib
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app, model_provisioner
from core.installation.provisioner import (
    CatalogModelInfo,
    InstallationTier,
    ModelInstallStatus,
    ModelLicenseType,
    ModelProvisioner,
    RuntimeProvisioner,
)

client = TestClient(app)


def test_verify_5_installation_tiers(tmp_path):
    """Verify that RuntimeProvisioner inspects all 5 Section 38 tiers."""
    prov = RuntimeProvisioner(
        workspace_dir=str(tmp_path / "workspace"),
        models_dir=str(tmp_path / "models"),
    )
    status = prov.inspect_system_readiness()

    assert InstallationTier.APPLICATION.value in status.tiers
    assert InstallationTier.PYTHON_RUNTIME.value in status.tiers
    assert InstallationTier.DOCUMENT_PROCESSING.value in status.tiers
    assert InstallationTier.MODEL_RUNTIME.value in status.tiers
    assert InstallationTier.MODEL_FILES.value in status.tiers

    # Core execution tiers must be functional in test venv
    assert status.tiers[InstallationTier.PYTHON_RUNTIME.value].is_ready is True
    assert status.tiers[InstallationTier.DOCUMENT_PROCESSING.value].is_ready is True
    assert status.tiers[InstallationTier.MODEL_RUNTIME.value].is_ready is True


def test_model_catalog_and_status(tmp_path):
    """Verify approved model catalog entries and initial installation states."""
    mp = ModelProvisioner(models_dir=str(tmp_path / "models"))
    catalog = mp.get_catalog()

    model_ids = [m.model_id for m in catalog]
    assert "qwen2.5-1.5b-instruct-q4" in model_ids
    assert "mistral-7b-instruct-v0.2-q4" in model_ids
    assert "gemma-2-9b-it-q4" in model_ids

    for m in catalog:
        assert m.license_type in [ModelLicenseType.APACHE_2_0.value, ModelLicenseType.GEMMA_TERMS.value]
        assert m.min_ram_gb >= 4
        assert m.context_length > 0
        assert m.status == ModelInstallStatus.AVAILABLE.value
        assert m.is_active is False


def test_model_download_license_enforcement(tmp_path):
    """Verify Section 38 mandate: license terms must be accepted before model download."""
    mp = ModelProvisioner(models_dir=str(tmp_path / "models"))

    # Attempt download without accepting license -> PermissionError
    with pytest.raises(PermissionError) as exc_info:
        mp.download_model("mistral-7b-instruct-v0.2-q4", accept_license=False)
    assert "License Agreement Required" in str(exc_info.value)

    # Download with license acceptance -> Success
    res = mp.download_model(
        "mistral-7b-instruct-v0.2-q4",
        accept_license=True,
        simulate_bytes=b"GGUF_MOCK_MISTRAL_WEIGHTS",
    )
    assert res["status"] == "COMPLETED"
    assert res["license_accepted"] is True
    assert Path(res["destination_path"]).exists()
    assert Path(res["destination_path"]).read_bytes() == b"GGUF_MOCK_MISTRAL_WEIGHTS"


def test_offline_model_import_with_checksum_verification(tmp_path):
    """Verify offline model import with cryptographic SHA-256 verification."""
    models_dir = tmp_path / "target_models"
    mp = ModelProvisioner(models_dir=str(models_dir))

    # Create dummy source GGUF file on simulated USB drive
    usb_dir = tmp_path / "usb_drive"
    usb_dir.mkdir()
    source_model = usb_dir / "custom_model.gguf"
    model_bytes = b"BINARY_GGUF_DATA_FOR_OFFLINE_TEST"
    source_model.write_bytes(model_bytes)
    actual_hash = hashlib.sha256(model_bytes).hexdigest()

    # 1. Successful import skipping catalog checksum (custom model)
    res = mp.import_offline_model(str(source_model), skip_checksum=True)
    assert res["filename"] == "custom_model.gguf"
    assert res["sha256_checksum"] == actual_hash
    assert Path(res["installed_path"]).exists()

    # 2. Corrupted import against catalog hash -> ValueError
    fake_mistral = usb_dir / "corrupted_mistral.gguf"
    fake_mistral.write_bytes(b"CORRUPTED_BYTES")
    with pytest.raises(ValueError) as exc:
        mp.import_offline_model(
            str(fake_mistral),
            expected_model_id="mistral-7b-instruct-v0.2-q4",
            skip_checksum=False,
        )
    assert "Cryptographic hash mismatch" in str(exc.value)

    # 3. Missing file -> FileNotFoundError
    with pytest.raises(FileNotFoundError):
        mp.import_offline_model("non_existent_path.gguf")


def test_model_activation(tmp_path):
    """Verify switching active model and rejecting uninstalled models."""
    models_dir = tmp_path / "models"
    mp = ModelProvisioner(models_dir=str(models_dir))

    # 1. Cannot activate uninstalled model -> FileNotFoundError
    with pytest.raises(FileNotFoundError):
        mp.activate_model("gemma-2-9b-it-q4")

    # 2. Install mock model and activate
    mp.download_model("gemma-2-9b-it-q4", accept_license=True, simulate_bytes=b"MOCK_GEMMA")
    act_res = mp.activate_model("gemma-2-9b-it-q4")
    assert act_res["status"] == "ACTIVATED"
    assert act_res["active_model_id"] == "gemma-2-9b-it-q4"

    # 3. Unknown model -> ValueError
    with pytest.raises(ValueError):
        mp.activate_model("unknown-model-xyz")


def test_installation_rest_api_endpoints():
    """Verify all Section 38 REST API endpoints via TestClient."""
    # 1. GET /api/v1/installation/status
    res = client.get("/api/v1/installation/status")
    assert res.status_code == 200
    data = res.json()
    assert "tiers" in data
    assert "application" in data["tiers"]
    assert "python_runtime" in data["tiers"]
    assert "document_processing" in data["tiers"]
    assert "model_runtime" in data["tiers"]
    assert "model_files" in data["tiers"]

    # 2. GET /api/v1/installation/models/catalog
    res = client.get("/api/v1/installation/models/catalog")
    assert res.status_code == 200
    cat_data = res.json()
    assert "catalog" in cat_data
    assert len(cat_data["catalog"]) >= 3

    # 3. POST /api/v1/installation/models/download without license -> 403 Forbidden
    res = client.post(
        "/api/v1/installation/models/download",
        json={"model_id": "qwen2.5-1.5b-instruct-q4", "accept_license": False},
    )
    assert res.status_code == 403
    assert "License Agreement Required" in res.json()["detail"]

    # 4. POST /api/v1/installation/models/download with license -> 200 OK
    res = client.post(
        "/api/v1/installation/models/download",
        json={"model_id": "qwen2.5-1.5b-instruct-q4", "accept_license": True},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"

    # 5. POST /api/v1/installation/models/activate -> 200 OK
    res = client.post(
        "/api/v1/installation/models/activate",
        json={"model_id": "qwen2.5-1.5b-instruct-q4"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ACTIVATED"

    # 6. POST /api/v1/installation/verify-runtimes -> 200 OK
    res = client.post("/api/v1/installation/verify-runtimes")
    assert res.status_code == 200
    assert "tiers" in res.json()
