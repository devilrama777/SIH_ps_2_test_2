"""
Tests for FastAPI Local Authentication and Session API Endpoints.

Verifies:
1. GET /api/v1/auth/setup-status returns setup requirements.
2. POST /api/v1/auth/first-run-setup initializes first account.
3. POST /api/v1/auth/login succeeds with valid credentials and issues session token.
4. POST /api/v1/auth/login fails with generic message on wrong password.
5. GET /api/v1/auth/session and GET /api/v1/users/me require Bearer token.
6. POST /api/v1/auth/logout invalidates session.
"""
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app, auth_manager

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_auth_db(tmp_path):
    """Ensure a clean test user database for each test run."""
    auth_manager.db_path = tmp_path / "api_test_users.db"
    auth_manager.workspace_base = tmp_path / "api_test_workspace"
    auth_manager._init_db()


def test_auth_api_full_lifecycle():
    # 1. Initial status: requires setup
    res = client.get("/api/v1/auth/setup-status")
    assert res.status_code == 200
    data = res.json()
    assert data["has_users"] is False
    assert data["requires_setup"] is True

    # 2. Unauthenticated access to protected route returns 401
    unauth_res = client.get("/api/v1/auth/session")
    assert unauth_res.status_code == 401
    assert "Authentication required" in unauth_res.json()["detail"]

    # 3. First-run setup creates initial user and logs in
    setup_res = client.post(
        "/api/v1/auth/first-run-setup",
        json={
            "username": "mine_commander",
            "display_name": "Chief Mining Officer",
            "password": "SecurePassword#2026",
        },
    )
    assert setup_res.status_code == 200
    setup_data = setup_res.json()
    token = setup_data["session_token"]
    assert len(token) == 64
    assert setup_data["user"]["username"] == "mine_commander"
    assert setup_data["user"]["role"] == "admin"

    # 4. Attempting first-run setup again is blocked
    second_setup = client.post(
        "/api/v1/auth/first-run-setup",
        json={
            "username": "intruder",
            "display_name": "Intruder",
            "password": "IntruderPassword123",
        },
    )
    assert second_setup.status_code == 400
    assert "already been completed" in second_setup.json()["detail"]

    # 5. Access protected route with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    session_res = client.get("/api/v1/auth/session", headers=headers)
    assert session_res.status_code == 200
    assert session_res.json()["authenticated"] is True
    assert session_res.json()["user"]["username"] == "mine_commander"

    # 6. /users/me returns authenticated profile
    me_res = client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["display_name"] == "Chief Mining Officer"

    # 7. Invalid login fails with generic error (no stack trace, no user enumeration)
    fail_res = client.post(
        "/api/v1/auth/login",
        json={"username": "mine_commander", "password": "WrongPassword!"},
    )
    assert fail_res.status_code == 401
    assert fail_res.json()["detail"] == "Invalid username or password."

    # 8. Valid login succeeds
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "mine_commander", "password": "SecurePassword#2026"},
    )
    assert login_res.status_code == 200
    new_token = login_res.json()["session_token"]
    assert len(new_token) == 64

    # 9. Logout
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {new_token}"},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "success"

    # 10. Previous token is now invalid
    revoked_res = client.get(
        "/api/v1/auth/session",
        headers={"Authorization": f"Bearer {new_token}"},
    )
    assert revoked_res.status_code == 401
