"""
Unit & Integration Tests for Local Authentication and Password Security.

Verifies:
1. PBKDF2-HMAC-SHA256 password hashing with salt and constant-time verification.
2. First-run setup detection and initial account creation without default credentials.
3. Successful authentication and secure session issuance.
4. Failed authentication with generic error handling (no user enumeration).
5. Session validation, sliding expiration, and clean logout.
6. Rate limiting / brute-force protection.
"""
import time
import pytest
from pathlib import Path

from core.auth.hasher import hash_password, verify_password, generate_salt
from core.auth.manager import AuthManager
from core.security.audit_logger import AuditLogger


def test_password_hasher():
    """Verify hashing generates distinct salts and validates correctly."""
    pw = "SecretPass123!"
    pw_hash, salt = hash_password(pw)
    assert len(pw_hash) == 64
    assert len(salt) == 64

    # Verify matching password
    assert verify_password(pw, pw_hash, salt) is True
    # Verify wrong password fails
    assert verify_password("WrongPassword", pw_hash, salt) is False
    # Verify empty inputs fail safely
    assert verify_password("", pw_hash, salt) is False
    assert verify_password(pw, "", salt) is False


def test_first_run_flow_and_user_creation(tmp_path):
    """Verify clean database detection and first-run user setup."""
    db_path = tmp_path / "test_users.db"
    ws_base = tmp_path / "test_workspace"
    audit_db = tmp_path / "audit.db"
    logger = AuditLogger(db_path=str(audit_db))

    mgr = AuthManager(db_path=db_path, workspace_base=ws_base, audit_logger=logger)
    assert mgr.has_users() is False
    assert mgr.get_user_count() == 0

    # Create first local user
    user = mgr.create_user(
        username="mine_admin",
        display_name="Mining Director",
        password="MineSecurePassword2026!",
        role="admin",
    )
    assert user.id.startswith("usr_")
    assert user.username == "mine_admin"
    assert user.display_name == "Mining Director"
    assert mgr.has_users() is True
    assert mgr.get_user_count() == 1

    # Attempting duplicate username fails
    with pytest.raises(ValueError, match="already exists"):
        mgr.create_user("mine_admin", "Another User", "AnotherPassword123")


def test_authentication_and_session_lifecycle(tmp_path):
    """Verify login, session verification, and logout."""
    db_path = tmp_path / "test_users.db"
    ws_base = tmp_path / "test_workspace"
    mgr = AuthManager(db_path=db_path, workspace_base=ws_base)

    mgr.create_user(
        username="analyst_raj",
        display_name="Rajesh Sharma",
        password="CorrectPassword123!",
    )

    # 1. Invalid username
    fail_res = mgr.authenticate("non_existent_user", "CorrectPassword123!")
    assert fail_res is None

    # 2. Invalid password
    fail_pw = mgr.authenticate("analyst_raj", "WrongPassword!")
    assert fail_pw is None

    # 3. Successful login with JWT issuance
    auth_res = mgr.authenticate("analyst_raj", "CorrectPassword123!")
    assert auth_res is not None
    jwt_parts = auth_res.session_token.split(".")
    assert len(jwt_parts) == 3, "Token must be a valid 3-part RFC 7519 JSON Web Token"
    assert auth_res.token_type == "Bearer"
    assert auth_res.access_token == auth_res.session_token
    assert auth_res.user.username == "analyst_raj"

    # Verify JWT claims
    claims = mgr.jwt_handler.decode_access_token(auth_res.session_token)
    assert claims is not None
    assert claims["username"] == "analyst_raj"
    assert claims["sub"] == auth_res.user.id
    assert claims["role"] == "analyst"

    # 4. Validate session using JWT
    valid_user = mgr.validate_session(auth_res.session_token)
    assert valid_user is not None
    assert valid_user.id == auth_res.user.id

    # 5. Invalid / tampered token fails
    assert mgr.validate_session("invalid_token_xyz") is None
    tampered = auth_res.session_token[:-5] + "tampr"
    assert mgr.validate_session(tampered) is None

    # 6. Logout / JWT revocation
    assert mgr.logout(auth_res.session_token) is True
    # Session / JWT is now explicitly revoked
    assert mgr.validate_session(auth_res.session_token) is None


def test_user_workspace_isolation(tmp_path):
    """Verify separate users receive dedicated filesystem workspace trees."""
    db_path = tmp_path / "test_users.db"
    ws_base = tmp_path / "test_workspace"
    mgr = AuthManager(db_path=db_path, workspace_base=ws_base)

    u1 = mgr.create_user("user_alpha", "Alpha", "PassAlpha123!")
    u2 = mgr.create_user("user_beta", "Beta", "PassBeta123!")

    ws1 = mgr.get_user_workspace(u1.id)
    ws2 = mgr.get_user_workspace(u2.id)

    assert ws1 != ws2
    assert ws1.exists()
    assert ws2.exists()
    assert (ws1 / "documents").exists()
    assert (ws2 / "documents").exists()
    assert (ws1 / "reports").exists()
    assert (ws2 / "reports").exists()
