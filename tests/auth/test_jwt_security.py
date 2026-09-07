"""
Unit & Penetration Tests for JSON Web Token (JWT) Security Engine.

Verifies:
1. RFC 7519 compliant HS256 JWT encoding and decoding.
2. Token signature verification and tamper detection.
3. Expiration time enforcement (expired tokens rejected).
4. Pure-Python fallback execution without PyJWT dependency.
5. Explicit JWT revocation / blacklist handling upon user logout.
"""
import time
import pytest
from pathlib import Path

from core.auth.jwt_handler import JWTHandler, _b64url_encode, _b64url_decode
from core.auth.manager import AuthManager


def test_jwt_standard_lifecycle(tmp_path):
    key_file = tmp_path / "jwt_secret.key"
    handler = JWTHandler(key_path=key_file)

    payload = {
        "sub": "usr_998877",
        "username": "mining_expert",
        "display_name": "S. K. Verma",
        "role": "geologist",
    }
    token = handler.create_access_token(payload, expires_delta_seconds=3600)
    assert token is not None
    parts = token.split(".")
    assert len(parts) == 3

    # Decode and verify claims
    decoded = handler.decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "usr_998877"
    assert decoded["username"] == "mining_expert"
    assert decoded["role"] == "geologist"
    assert decoded["exp"] > time.time()
    assert decoded["iat"] <= time.time()
    assert "jti" in decoded


def test_jwt_tamper_detection(tmp_path):
    key_file = tmp_path / "jwt_secret.key"
    handler = JWTHandler(key_path=key_file)

    token = handler.create_access_token({"sub": "usr_1", "username": "admin"})
    parts = token.split(".")

    # 1. Tampered payload
    tampered_payload_token = f"{parts[0]}.eyJzdWIiOiJ1c3JfMSIsInVzZXJuYW1lIjoiaGFja2VkIn0.{parts[2]}"
    assert handler.decode_access_token(tampered_payload_token) is None

    # 2. Tampered signature
    tampered_sig_token = f"{parts[0]}.{parts[1]}.{parts[2][:-3]}xyz"
    assert handler.decode_access_token(tampered_sig_token) is None

    # 3. Wrong secret key
    other_handler = JWTHandler(secret_key="completely_different_signing_secret_key_32bytes")
    assert other_handler.decode_access_token(token) is None


def test_jwt_expiration_enforcement(tmp_path):
    key_file = tmp_path / "jwt_secret.key"
    handler = JWTHandler(key_path=key_file)

    # Token expires in -10 seconds (already expired)
    token = handler.create_access_token({"sub": "usr_1"}, expires_delta_seconds=-10)
    assert handler.decode_access_token(token) is None


def test_jwt_pure_python_fallback(tmp_path, monkeypatch):
    """Verify that pure-Python HS256 engine works even if PyJWT is absent."""
    import sys
    import core.auth.jwt_handler
    mod = sys.modules["core.auth.jwt_handler"]
    monkeypatch.setattr(mod, "_HAS_PYJWT", False)
    monkeypatch.setattr(mod, "pyjwt", None)

    key_file = tmp_path / "fallback_key.key"
    handler = mod.JWTHandler(key_path=key_file)

    token = handler.create_access_token({"sub": "usr_airgap", "role": "analyst"}, expires_delta_seconds=600)
    assert len(token.split(".")) == 3

    decoded = handler.decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "usr_airgap"
    assert decoded["role"] == "analyst"


def test_jwt_revocation_blacklist(tmp_path):
    """Verify that logged-out JWT tokens are placed on revocation blacklist."""
    db_path = tmp_path / "users.db"
    ws_base = tmp_path / "workspace"
    mgr = AuthManager(db_path=db_path, workspace_base=ws_base)

    mgr.create_user("raj_kumar", "Raj Kumar", "Password#2026!")
    auth_res = mgr.authenticate("raj_kumar", "Password#2026!")
    token = auth_res.session_token

    # Active session is valid
    assert mgr.validate_session(token) is not None

    # Revoke via logout
    mgr.logout(token)

    # Token is now revoked in local database
    assert mgr.validate_session(token) is None
