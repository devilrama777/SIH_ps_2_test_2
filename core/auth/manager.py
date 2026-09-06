"""
Local User Authentication & Multi-User Isolation Manager.

Maintains SQLite persistence for local user accounts, active desktop sessions,
and isolated per-user filesystem directories.
"""
from __future__ import annotations

import os
import sqlite3
import time
import secrets
from pathlib import Path
from typing import Optional, List

from core.auth.hasher import hash_password, verify_password
from core.auth.models import (
    UserRecord,
    UserPublic,
    SessionRecord,
    AuthResponse,
)
from core.security.audit_logger import AuditLogger
from core.security.models import AuditEventType

DEFAULT_SESSION_DURATION_SECONDS = 86400  # 24 hours
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 30  # 30-second local backoff cooldown


class AuthManager:
    """
    Manages local user authentication, session state, and per-user directory trees.
    """

    def __init__(
        self,
        db_path: str | Path = "data/users.db",
        workspace_base: str | Path = "data/workspace",
        audit_logger: Optional[AuditLogger] = None,
    ):
        self.db_path = Path(db_path)
        self.workspace_base = Path(workspace_base)
        self.audit_logger = audit_logger or AuditLogger()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    role TEXT NOT NULL DEFAULT 'analyst',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    last_login_at REAL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    last_activity_at REAL NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS login_attempts (
                    username TEXT PRIMARY KEY,
                    failed_count INTEGER NOT NULL DEFAULT 0,
                    last_attempt_at REAL NOT NULL,
                    locked_until REAL NOT NULL DEFAULT 0
                )
                """
            )
            conn.commit()

    def get_user_count(self) -> int:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM users")
            return cur.fetchone()[0]

    def has_users(self) -> bool:
        return self.get_user_count() > 0

    def get_user_by_username(self, username: str) -> Optional[UserRecord]:
        clean_user = username.strip().lower()
        with self._get_conn() as conn:
            cur = conn.execute("SELECT * FROM users WHERE LOWER(username) = ?", (clean_user,))
            row = cur.fetchone()
            if row:
                return UserRecord(**dict(row))
        return None

    def get_user_by_id(self, user_id: str) -> Optional[UserPublic]:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            if row:
                return UserRecord(**dict(row)).to_public()
        return None

    def create_user(
        self,
        username: str,
        display_name: str,
        password: str,
        role: str = "analyst",
    ) -> UserPublic:
        """
        Create a new local user account with cryptographically hashed password.
        """
        clean_user = username.strip().lower()
        if not clean_user or len(clean_user) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        if not display_name.strip():
            display_name = clean_user.capitalize()

        if self.get_user_by_username(clean_user) is not None:
            raise ValueError(f"Username '{clean_user}' already exists.")

        user_id = f"usr_{secrets.token_hex(8)}"
        pw_hash, salt = hash_password(password)
        now = time.time()

        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO users (id, username, display_name, password_hash, salt, status, role, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?)
                """,
                (user_id, clean_user, display_name.strip(), pw_hash, salt, role, now, now),
            )
            conn.commit()

        # Initialize dedicated user workspace tree
        self.get_user_workspace(user_id)

        if self.audit_logger:
            try:
                self.audit_logger.log_event(
                    event_type=AuditEventType.AUTHENTICATION,
                    action="account_created",
                    user=clean_user,
                    status="success",
                    details={"display_name": display_name.strip(), "user_id": user_id, "role": role},
                )
            except Exception:
                pass

        return UserPublic(
            id=user_id,
            username=clean_user,
            display_name=display_name.strip(),
            status="active",
            role=role,
            created_at=now,
            updated_at=now,
        )

    def authenticate(self, username: str, password: str) -> Optional[AuthResponse]:
        """
        Validate credentials, handle brute-force protection, issue local session token.
        """
        clean_user = username.strip().lower()
        now = time.time()

        # Check local brute-force cooldown
        with self._get_conn() as conn:
            cur = conn.execute("SELECT * FROM login_attempts WHERE username = ?", (clean_user,))
            attempt = cur.fetchone()
            if attempt and attempt["locked_until"] > now:
                if self.audit_logger:
                    try:
                        self.audit_logger.log_event(
                            event_type=AuditEventType.AUTHENTICATION,
                            action="login_locked",
                            user=clean_user,
                            status="blocked",
                            details={"locked_until": attempt["locked_until"]},
                        )
                    except Exception:
                        pass
                return None

        user_record = self.get_user_by_username(clean_user)
        if not user_record or user_record.status != "active":
            self._record_failed_attempt(clean_user)
            if self.audit_logger:
                try:
                    self.audit_logger.log_event(
                        event_type=AuditEventType.AUTHENTICATION,
                        action="login_failure",
                        user=clean_user,
                        status="failure",
                        details={"reason": "invalid_user_or_inactive"},
                    )
                except Exception:
                    pass
            return None

        if not verify_password(password, user_record.password_hash, user_record.salt):
            self._record_failed_attempt(clean_user)
            if self.audit_logger:
                try:
                    self.audit_logger.log_event(
                        event_type=AuditEventType.AUTHENTICATION,
                        action="login_failure",
                        user=clean_user,
                        status="failure",
                        details={"reason": "invalid_password"},
                    )
                except Exception:
                    pass
            return None

        # Reset failed login attempts on success
        with self._get_conn() as conn:
            conn.execute("DELETE FROM login_attempts WHERE username = ?", (clean_user,))
            conn.execute(
                "UPDATE users SET last_login_at = ? WHERE id = ?",
                (now, user_record.id),
            )
            conn.commit()

        # Create session
        session_token = secrets.token_hex(32)
        expires_at = now + DEFAULT_SESSION_DURATION_SECONDS
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO sessions (token, user_id, created_at, expires_at, last_activity_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_token, user_record.id, now, expires_at, now),
            )
            conn.commit()

        if self.audit_logger:
            try:
                self.audit_logger.log_event(
                    event_type=AuditEventType.AUTHENTICATION,
                    action="login_success",
                    user=clean_user,
                    status="success",
                    details={"user_id": user_record.id},
                )
            except Exception:
                pass

        user_public = user_record.to_public()
        user_public.last_login_at = now
        return AuthResponse(session_token=session_token, user=user_public)

    def _record_failed_attempt(self, username: str) -> None:
        now = time.time()
        with self._get_conn() as conn:
            cur = conn.execute("SELECT * FROM login_attempts WHERE username = ?", (username,))
            attempt = cur.fetchone()
            if attempt:
                new_count = attempt["failed_count"] + 1
                locked_until = now + LOCKOUT_DURATION_SECONDS if new_count >= MAX_FAILED_ATTEMPTS else 0
                conn.execute(
                    """
                    UPDATE login_attempts
                    SET failed_count = ?, last_attempt_at = ?, locked_until = ?
                    WHERE username = ?
                    """,
                    (new_count, now, locked_until, username),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO login_attempts (username, failed_count, last_attempt_at, locked_until)
                    VALUES (?, 1, ?, 0)
                    """,
                    (username, now),
                )
            conn.commit()

    def validate_session(self, token: str) -> Optional[UserPublic]:
        """Validate an active session token and extend sliding expiration."""
        if not token:
            return None
        now = time.time()
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                SELECT s.expires_at, u.*
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = ? AND u.status = 'active'
                """,
                (token,),
            )
            row = cur.fetchone()
            if not row:
                return None

            if row["expires_at"] < now:
                # Expired session -> delete
                conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()
                return None

            # Update last activity
            conn.execute(
                "UPDATE sessions SET last_activity_at = ? WHERE token = ?",
                (now, token),
            )
            conn.commit()

            return UserRecord(
                id=row["id"],
                username=row["username"],
                display_name=row["display_name"],
                password_hash=row["password_hash"],
                salt=row["salt"],
                status=row["status"],
                role=row["role"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                last_login_at=row["last_login_at"],
            ).to_public()

    def logout(self, token: str) -> bool:
        """Invalidate the session token and log logout event."""
        if not token:
            return False
        user = self.validate_session(token)
        with self._get_conn() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()

        if user and self.audit_logger:
            try:
                self.audit_logger.log_event(
                    event_type=AuditEventType.AUTHENTICATION,
                    action="logout",
                    user=user.username,
                    status="success",
                    details={"user_id": user.id},
                )
            except Exception:
                pass
        return True

    def get_user_workspace(self, user_id: str) -> Path:
        """
        Returns the isolated workspace path for a specific user, creating standard subfolders.
        """
        user_ws = self.workspace_base / "users" / user_id
        for sub in ["workspace", "documents", "reports", "assets", "indexes", "cache"]:
            (user_ws / sub).mkdir(parents=True, exist_ok=True)
        return user_ws
