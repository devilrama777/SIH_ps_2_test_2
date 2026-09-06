"""
Root test configuration and fixtures for CIL Report Intelligence test suite.
"""

import os
import tempfile
from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def workspace_root() -> Path:
    """Returns absolute path to the repository workspace root."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def temp_workspace():
    """Provides a safe temporary directory isolated for unit tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
