import os
import pytest
from fastapi.testclient import TestClient
from apps.processing.server import app
from core.security.network_guard import NetworkSecurityGuard, AirGapViolationError


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_network_security_guard_loopback():
    assert NetworkSecurityGuard.is_loopback("127.0.0.1") is True
    assert NetworkSecurityGuard.is_loopback("localhost") is True
    assert NetworkSecurityGuard.is_loopback("127.0.0.99") is True
    assert NetworkSecurityGuard.is_loopback("api.openai.com") is False
    assert NetworkSecurityGuard.is_loopback("8.8.8.8") is False


def test_network_security_guard_posture():
    posture = NetworkSecurityGuard.verify_air_gap_posture()
    assert posture["air_gap_enforced"] is True
    assert posture["external_ai_calls_permitted"] is False
    assert "127.0.0.1" in posture["allowed_bind_interfaces"]


def test_security_status_endpoint(client):
    response = client.get("/api/v1/security/status")
    assert response.status_code == 200
    data = response.json()
    assert data["air_gap_enforced"] is True
    assert data["no_cloud_ai_calls"] is True
    assert data["audit_chain_valid"] is True
    assert isinstance(data["total_audit_logs"], int)
    assert len(data["active_controls"]) >= 4


def test_security_vault_and_audit_api(client):
    # 1. Store a secret
    post_res = client.post(
        "/api/v1/security/vault",
        json={"key": "TEST_DB_CRED", "value": "test_pass_123"},
    )
    assert post_res.status_code == 200
    assert post_res.json()["status"] == "stored"

    # 2. Verify key listed
    keys_res = client.get("/api/v1/security/vault/keys")
    assert keys_res.status_code == 200
    assert "TEST_DB_CRED" in keys_res.json()

    # 3. Verify audit log was recorded for config change
    logs_res = client.get("/api/v1/security/audit-logs?event_type=config_change")
    assert logs_res.status_code == 200
    logs = logs_res.json()
    assert len(logs) >= 1
    assert logs[0]["action"] == "store_vault_secret"
    assert logs[0]["resource_id"] == "TEST_DB_CRED"
    assert logs[0]["prev_hash"] is not None
    assert len(logs[0]["entry_hash"]) == 64
