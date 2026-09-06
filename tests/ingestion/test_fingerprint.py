"""
Tests for streaming SHA-256 fingerprinting.
"""
import hashlib
from pathlib import Path
from core.ingestion.fingerprint import compute_bytes_hash, compute_file_hash


def test_compute_bytes_hash():
    sample = b"Coal India Limited Subsidiary Data"
    expected = hashlib.sha256(sample).hexdigest()
    assert compute_bytes_hash(sample) == expected


def test_compute_file_hash(tmp_path: Path):
    test_file = tmp_path / "test_production.csv"
    content = b"Colliery,Month,Production_MT\nNorth,March,1245.70\n"
    test_file.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()
    computed = compute_file_hash(test_file)
    assert computed == expected
    assert len(computed) == 64
