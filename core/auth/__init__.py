"""
Local Authentication, Profiles & Workspace Isolation Package.
"""
from core.auth.hasher import hash_password, verify_password
from core.auth.models import (
    UserPublic,
    UserRecord,
    SessionRecord,
    LoginRequest,
    FirstRunSetupRequest,
    AuthResponse,
    SetupStatusResponse,
)
from core.auth.manager import AuthManager

from core.auth.context import (
    ProfileContext,
    get_profile_for_user,
    get_default_profile,
    DEFAULT_DESKTOP_PROFILE_ID,
)

__all__ = [
    "hash_password",
    "verify_password",
    "UserPublic",
    "UserRecord",
    "SessionRecord",
    "LoginRequest",
    "FirstRunSetupRequest",
    "AuthResponse",
    "SetupStatusResponse",
    "AuthManager",
    "ProfileContext",
    "get_profile_for_user",
    "get_default_profile",
    "DEFAULT_DESKTOP_PROFILE_ID",
]
