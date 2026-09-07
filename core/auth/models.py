"""
Data models for Local Authentication, User Profiles, and Sessions.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class UserPublic(BaseModel):
    """Sanitized user profile safe for frontend exposure."""
    id: str
    username: str
    display_name: str
    status: str = "active"
    role: str = "analyst"
    created_at: float
    updated_at: float
    last_login_at: Optional[float] = None


class UserRecord(BaseModel):
    """Complete user record for backend persistence."""
    id: str
    username: str
    display_name: str
    password_hash: str
    salt: str
    status: str = "active"
    role: str = "analyst"
    created_at: float
    updated_at: float
    last_login_at: Optional[float] = None

    def to_public(self) -> UserPublic:
        return UserPublic(
            id=self.id,
            username=self.username,
            display_name=self.display_name,
            status=self.status,
            role=self.role,
            created_at=self.created_at,
            updated_at=self.updated_at,
            last_login_at=self.last_login_at,
        )


class SessionRecord(BaseModel):
    """Session state for authenticated local sessions."""
    token: str
    user_id: str
    created_at: float
    expires_at: float
    last_activity_at: float


class LoginRequest(BaseModel):
    username: str
    password: str


class FirstRunSetupRequest(BaseModel):
    username: str
    display_name: str
    password: str


class AuthResponse(BaseModel):
    session_token: str
    access_token: Optional[str] = None
    token_type: str = "Bearer"
    user: UserPublic


class SetupStatusResponse(BaseModel):
    has_users: bool
    requires_setup: bool
