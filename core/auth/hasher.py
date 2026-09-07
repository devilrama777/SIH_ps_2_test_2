"""
Secure Password Hashing Module — Local Desktop Authentication.

Uses PBKDF2-HMAC-SHA256 with 100,000 iterations and 32-byte cryptographically secure
random salt. Complies with Section 31 of Master Security & Auth Specification.
"""
from __future__ import annotations

import hashlib
import os
import secrets

ITERATIONS = 100_000
HASH_NAME = "sha256"
SALT_BYTES = 32


def generate_salt() -> str:
    """Generate a 32-byte cryptographically secure random salt hex string."""
    return secrets.token_hex(SALT_BYTES)


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """
    Hash a plaintext password using PBKDF2-HMAC-SHA256.

    Returns:
        tuple of (password_hash_hex, salt_hex)
    """
    if not password:
        raise ValueError("Password cannot be empty")
    if not salt:
        salt = generate_salt()

    salt_bytes = bytes.fromhex(salt)
    pw_bytes = password.encode("utf-8")
    derived_key = hashlib.pbkdf2_hmac(HASH_NAME, pw_bytes, salt_bytes, ITERATIONS)
    return derived_key.hex(), salt


def verify_password(password: str, expected_hash: str, salt: str) -> bool:
    """
    Verify a plaintext password against the stored PBKDF2 hash using constant-time comparison.
    """
    if not password or not expected_hash or not salt:
        return False
    try:
        calculated_hash, _ = hash_password(password, salt)
        return secrets.compare_digest(calculated_hash, expected_hash)
    except Exception:
        return False
