"""
JSON Web Token (JWT) Security Engine — Local Desktop Authentication.

Provides RFC 7519 compliant JSON Web Token encoding and decoding using HMAC-SHA256 (HS256).
Persists a cryptographically secure 256-bit signing key locally in the workspace.
Includes pure-Python fallback to ensure 100% offline air-gapped reliability without external C dependencies.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Attempt to import PyJWT; fall back gracefully to built-in HS256 engine if needed
try:
    import jwt as pyjwt
    _HAS_PYJWT = True
except ImportError:
    pyjwt = None
    _HAS_PYJWT = False


DEFAULT_JWT_EXPIRE_SECONDS = 86400  # 24 hours
ALGORITHM = "HS256"


def _b64url_encode(data: bytes) -> str:
    """Encode bytes to URL-safe base64 string without trailing padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    """Decode URL-safe base64 string with optional padding."""
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("ascii"))


class JWTHandler:
    """
    Handles generation, signing, and verification of JSON Web Tokens for local authentication.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        key_path: str | Path = "data/workspace/jwt_secret.key",
    ):
        self.key_path = Path(key_path)
        if secret_key:
            self.secret_key = secret_key
        else:
            self.secret_key = self._load_or_create_secret()

    def _load_or_create_secret(self) -> str:
        """Load the local 256-bit signing secret from disk, or generate a fresh one."""
        try:
            if self.key_path.exists():
                content = self.key_path.read_text(encoding="utf-8").strip()
                if len(content) >= 32:
                    return content
        except Exception:
            pass

        new_key = secrets.token_hex(32)
        try:
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            self.key_path.write_text(new_key, encoding="utf-8")
        except Exception:
            pass
        return new_key

    def create_access_token(
        self,
        payload: Dict[str, Any],
        expires_delta_seconds: int = DEFAULT_JWT_EXPIRE_SECONDS,
    ) -> str:
        """
        Generate and sign a JWT access token containing user claims.
        """
        now = int(time.time())
        claims = dict(payload)
        claims["iat"] = now
        claims["exp"] = now + expires_delta_seconds
        if "jti" not in claims:
            claims["jti"] = secrets.token_hex(16)

        if _HAS_PYJWT and pyjwt is not None:
            return pyjwt.encode(claims, self.secret_key, algorithm=ALGORITHM)

        # Standard pure-Python RFC 7519 HS256 implementation
        header = {"alg": ALGORITHM, "typ": "JWT"}
        header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = _b64url_encode(json.dumps(claims, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        signature_b64 = _b64url_encode(signature)

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def decode_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify the signature and expiration of a JWT access token, returning claims.
        Returns None if invalid, expired, or tampered.
        """
        if not token or not isinstance(token, str):
            return None

        clean_token = token.strip()
        if _HAS_PYJWT and pyjwt is not None:
            try:
                decoded = pyjwt.decode(
                    clean_token,
                    self.secret_key,
                    algorithms=[ALGORITHM],
                    options={"require": ["exp", "iat", "sub"]},
                )
                return decoded
            except Exception:
                return None

        # Standard pure-Python verification
        parts = clean_token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

        # Verify signature in constant time
        expected_sig = hmac.new(
            self.secret_key.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        try:
            actual_sig = _b64url_decode(signature_b64)
            if not secrets.compare_digest(expected_sig, actual_sig):
                return None
        except Exception:
            return None

        # Verify header
        try:
            header = json.loads(_b64url_decode(header_b64).decode("utf-8"))
            if header.get("alg") != ALGORITHM:
                return None
        except Exception:
            return None

        # Verify payload & expiration
        try:
            payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
            now = int(time.time())
            exp = payload.get("exp")
            if exp is None or now > exp:
                return None
            return payload
        except Exception:
            return None


# Global singleton
jwt_handler = JWTHandler()
