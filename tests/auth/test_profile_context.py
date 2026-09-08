"""
Tests for ProfileContext and Profile Ownership Isolation.

Verifies:
1. get_default_profile creates isolated desktop profile directory structure.
2. get_profile_for_user creates user-scoped directories and distinct DB paths.
3. Path containment: profile directories never collide or leak between users.
4. FastAPI dependency get_active_profile returns default profile without auth header
   and scoped user profile when authenticated.
"""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from core.auth.models import UserPublic
from core.auth.context import (
    ProfileContext,
    get_profile_for_user,
    get_default_profile,
    DEFAULT_DESKTOP_PROFILE_ID,
)
from apps.processing.server import app, auth_manager


client = TestClient(app)


def test_default_desktop_profile(tmp_path):
    ctx = get_default_profile(workspace_root=tmp_path)
    assert ctx.profile_id == DEFAULT_DESKTOP_PROFILE_ID
    assert ctx.base_dir.exists()
    assert ctx.documents_dir.exists()
    assert ctx.reports_dir.exists()
    assert ctx.indexes_dir.exists()
    assert ctx.cache_dir.exists()
    assert ctx.assets_dir.exists()

    db_path = ctx.get_scoped_db_path("reports.db")
    assert db_path == ctx.base_dir / "reports.db"


def test_user_profile_isolation(tmp_path):
    user_a = UserPublic(
        id="usr_aaa",
        username="analyst_a",
        display_name="Analyst A",
        role="analyst",
        created_at=1000.0,
        updated_at=1000.0,
    )
    user_b = UserPublic(
        id="usr_bbb",
        username="analyst_b",
        display_name="Analyst B",
        role="analyst",
        created_at=2000.0,
        updated_at=2000.0,
    )

    ctx_a = get_profile_for_user(user_a, workspace_root=tmp_path)
    ctx_b = get_profile_for_user(user_b, workspace_root=tmp_path)

    assert ctx_a.profile_id == "usr_aaa"
    assert ctx_b.profile_id == "usr_bbb"
    assert ctx_a.base_dir != ctx_b.base_dir
    assert ctx_a.reports_dir != ctx_b.reports_dir

    db_a = ctx_a.get_scoped_db_path("vector_index.db")
    db_b = ctx_b.get_scoped_db_path("vector_index.db")
    assert db_a != db_b
    assert str(db_a).startswith(str(ctx_a.base_dir))
    assert str(db_b).startswith(str(ctx_b.base_dir))


def test_active_profile_api_endpoint(tmp_path):
    # Override auth manager paths
    auth_manager.db_path = tmp_path / "test_users.db"
    auth_manager.workspace_base = tmp_path / "test_workspace"
    auth_manager._init_db()

    # 1. Without auth: defaults to desktop profile
    res_default = client.get("/api/v1/profiles/active")
    assert res_default.status_code == 200
    data_default = res_default.json()
    assert data_default["profile_id"] == DEFAULT_DESKTOP_PROFILE_ID

    # 2. Register user & authenticate
    setup_res = client.post(
        "/api/v1/auth/first-run-setup",
        json={
            "username": "profile_user",
            "display_name": "Profile User",
            "password": "SecurePassword#2026",
        },
    )
    assert setup_res.status_code == 200
    token = setup_res.json()["session_token"]
    user_id = setup_res.json()["user"]["id"]

    # 3. With auth header: returns scoped user profile
    headers = {"Authorization": f"Bearer {token}"}
    res_user = client.get("/api/v1/profiles/active", headers=headers)
    assert res_user.status_code == 200
    data_user = res_user.json()
    assert data_user["profile_id"] == user_id
    assert data_user["username"] == "profile_user"
    assert "users" in data_user["base_dir"]
