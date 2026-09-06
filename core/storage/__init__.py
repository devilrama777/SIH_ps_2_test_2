"""
Storage Lifecycle and Safe Artifact Cleanup Engine.
Adheres to CIL Master Implementation Plan Sections 36 and 37.
"""

from core.storage.lifecycle import (
    ArtifactCategory,
    StorageCategorySummary,
    StorageManager,
)

__all__ = [
    "ArtifactCategory",
    "StorageCategorySummary",
    "StorageManager",
]
