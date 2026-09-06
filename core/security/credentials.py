"""
Secure Credential Vault — Section 24 of Master Implementation Specification.

Provides OS-level DPAPI (Windows) and machine-salted key derivation for storing
credentials and secrets without plaintext .env or JSON files.
"""
from __future__ import annotations

import base64
import json
import os
import platform
from pathlib import Path
from typing import Dict, Optional

# Windows Data Protection API (DPAPI) via ctypes
IS_WINDOWS = platform.system() == "Windows"


class DataBlob:
    pass


if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_byte)),
        ]


class SecureCredentialVault:
    """
    Encrypts and persists credentials using Windows DPAPI or host machine-derived keys.
    """

    def __init__(self, vault_path: str = "data/workspace/vault.bin"):
        self.vault_path = Path(vault_path)
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, str] = {}
        self._load_vault()

    def store_secret(self, key: str, value: str) -> None:
        """Securely store a credential."""
        self._cache[key] = value
        self._save_vault()

    def retrieve_secret(self, key: str) -> Optional[str]:
        """Retrieve a decrypted credential by key."""
        return self._cache.get(key)

    def delete_secret(self, key: str) -> bool:
        """Remove a secret from the vault."""
        if key in self._cache:
            del self._cache[key]
            self._save_vault()
            return True
        return False

    def list_keys(self) -> list[str]:
        """List all secret keys stored in vault (values remain hidden)."""
        return list(self._cache.keys())

    def _encrypt_bytes(self, data: bytes) -> bytes:
        if IS_WINDOWS:
            try:
                crypt32 = ctypes.windll.crypt32
                kernel32 = ctypes.windll.kernel32

                in_blob = DATA_BLOB()
                in_blob.cbData = len(data)
                in_blob.pbData = ctypes.cast(
                    (ctypes.c_byte * len(data))(*data),
                    ctypes.POINTER(ctypes.c_byte),
                )

                out_blob = DATA_BLOB()
                if crypt32.CryptProtectData(
                    ctypes.byref(in_blob),
                    "CIL_Report_Vault",
                    None,
                    None,
                    None,
                    0,
                    ctypes.byref(out_blob),
                ):
                    result = ctypes.string_at(out_blob.pbData, out_blob.cbData)
                    kernel32.LocalFree(out_blob.pbData)
                    return result
            except Exception:
                pass

        # Fallback XOR key derivation from host node
        import uuid
        key = str(uuid.getnode()).encode("utf-8") * 16
        return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

    def _decrypt_bytes(self, data: bytes) -> bytes:
        if IS_WINDOWS:
            try:
                crypt32 = ctypes.windll.crypt32
                kernel32 = ctypes.windll.kernel32

                in_blob = DATA_BLOB()
                in_blob.cbData = len(data)
                in_blob.pbData = ctypes.cast(
                    (ctypes.c_byte * len(data))(*data),
                    ctypes.POINTER(ctypes.c_byte),
                )

                out_blob = DATA_BLOB()
                if crypt32.CryptUnprotectData(
                    ctypes.byref(in_blob),
                    None,
                    None,
                    None,
                    None,
                    0,
                    ctypes.byref(out_blob),
                ):
                    result = ctypes.string_at(out_blob.pbData, out_blob.cbData)
                    kernel32.LocalFree(out_blob.pbData)
                    return result
            except Exception:
                pass

        # Fallback XOR decrypt
        import uuid
        key = str(uuid.getnode()).encode("utf-8") * 16
        return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

    def _save_vault(self) -> None:
        plaintext = json.dumps(self._cache).encode("utf-8")
        encrypted = self._encrypt_bytes(plaintext)
        with open(self.vault_path, "wb") as f:
            f.write(encrypted)

    def _load_vault(self) -> None:
        if not self.vault_path.exists():
            return
        try:
            with open(self.vault_path, "rb") as f:
                encrypted = f.read()
            if encrypted:
                decrypted = self._decrypt_bytes(encrypted)
                self._cache = json.loads(decrypted.decode("utf-8"))
        except Exception:
            self._cache = {}
