"""
Cryptographic File Fingerprinting — Section 6 of Master Implementation Specification.

Uses 64KB chunked streaming SHA-256 calculation to handle multi-hundred-megabyte
source documents without memory spikes.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO, Union

CHUNK_SIZE = 64 * 1024  # 64 KB chunks


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 digest of a file using streaming chunks.
    Raises FileNotFoundError if file does not exist.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Source file not found: {path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_stream_hash(stream: BinaryIO) -> str:
    """Compute SHA-256 digest from a readable binary stream."""
    hasher = hashlib.sha256()
    while chunk := stream.read(CHUNK_SIZE):
        hasher.update(chunk)
    return hasher.hexdigest()


def compute_bytes_hash(data: bytes) -> str:
    """Compute SHA-256 digest directly from in-memory bytes."""
    return hashlib.sha256(data).hexdigest()
