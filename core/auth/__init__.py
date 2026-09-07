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
from core.auth.jwt_handler import JWTHandler, jwt_handler
from core.auth.manager import AuthManager

__all__ = [
    "hash_password",
    "verify_password",
    "JWTHandler",
    "jwt_handler",
    "UserPublic",
    "UserRecord",
    "SessionRecord",
    "LoginRequest",
    "FirstRunSetupRequest",
    "AuthResponse",
    "SetupStatusResponse",
    "AuthManager",
]
