"""
Profile / Workspace Ownership Context.

Provides unified ProfileContext for desktop single-user mode and multi-user
isolation. Ensures database paths, document repositories, report outputs,
and index caches are strictly scoped to the active profile.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from core.auth.models import UserPublic


DEFAULT_DESKTOP_PROFILE_ID = "default_local_profile"
DEFAULT_DESKTOP_USERNAME = "local_analyst"
DEFAULT_DESKTOP_DISPLAY_NAME = "Local Analyst"


@dataclass
class ProfileContext:
    """Encapsulates the identity and filesystem boundaries of an active workspace profile."""
    profile_id: str
    username: str
    display_name: str
    role: str
    base_dir: Path
    documents_dir: Path
    reports_dir: Path
    indexes_dir: Path
    cache_dir: Path
    assets_dir: Path

    def ensure_directories(self) -> None:
        """Ensure all profile-scoped directories exist on disk."""
        for d in [
            self.base_dir,
            self.documents_dir,
            self.reports_dir,
            self.indexes_dir,
            self.cache_dir,
            self.assets_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def get_scoped_db_path(self, db_filename: str) -> Path:
        """Return a database path scoped specifically to this profile."""
        self.ensure_directories()
        return self.base_dir / db_filename

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "username": self.username,
            "display_name": self.display_name,
            "role": self.role,
            "base_dir": str(self.base_dir),
            "documents_dir": str(self.documents_dir),
            "reports_dir": str(self.reports_dir),
            "indexes_dir": str(self.indexes_dir),
            "cache_dir": str(self.cache_dir),
            "assets_dir": str(self.assets_dir),
        }


def get_profile_for_user(
    user: UserPublic,
    workspace_root: Path | str = "data/workspace",
) -> ProfileContext:
    """Generate a fully isolated ProfileContext for an authenticated UserPublic."""
    root = Path(workspace_root).resolve()
    user_base = root / "users" / user.id
    ctx = ProfileContext(
        profile_id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        base_dir=user_base,
        documents_dir=user_base / "documents",
        reports_dir=user_base / "reports",
        indexes_dir=user_base / "indexes",
        cache_dir=user_base / "cache",
        assets_dir=user_base / "assets",
    )
    ctx.ensure_directories()
    return ctx


def get_default_profile(
    workspace_root: Path | str = "data/workspace",
) -> ProfileContext:
    """Generate the default ProfileContext for standalone local desktop mode."""
    root = Path(workspace_root).resolve()
    default_base = root / "profiles" / DEFAULT_DESKTOP_PROFILE_ID
    ctx = ProfileContext(
        profile_id=DEFAULT_DESKTOP_PROFILE_ID,
        username=DEFAULT_DESKTOP_USERNAME,
        display_name=DEFAULT_DESKTOP_DISPLAY_NAME,
        role="admin",
        base_dir=default_base,
        documents_dir=default_base / "documents",
        reports_dir=default_base / "reports",
        indexes_dir=default_base / "indexes",
        cache_dir=default_base / "cache",
        assets_dir=default_base / "assets",
    )
    ctx.ensure_directories()
    return ctx
