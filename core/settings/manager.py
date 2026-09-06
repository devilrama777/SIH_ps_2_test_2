"""
SettingsManager: Atomic, thread-safe configuration management and persistence — Section 24 & Section 33.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.domain.settings import (
    AISettings,
    ApplicationSettings,
    SecuritySettings,
    StorageSettings,
    SubsidiaryProfile,
    TemplateSettings,
)

logger = logging.getLogger(__name__)

STANDARD_CIL_SUBSIDIARIES: List[SubsidiaryProfile] = [
    SubsidiaryProfile(
        code="CCL",
        full_name="Central Coalfields Limited",
        headquarters="Darbhanga House, Ranchi, Jharkhand - 834029",
        default_financial_year="FY 2024-25",
        currency_unit="INR Crores",
        statutory_mandate_csr_percent=2.0,
    ),
    SubsidiaryProfile(
        code="BCCL",
        full_name="Bharat Coking Coal Limited",
        headquarters="Koyla Bhawan, Koyla Nagar, Dhanbad, Jharkhand - 826005",
        default_financial_year="FY 2024-25",
        currency_unit="INR Crores",
        statutory_mandate_csr_percent=2.0,
    ),
    SubsidiaryProfile(
        code="ECL",
        full_name="Eastern Coalfields Limited",
        headquarters="Sanctoria, PO: Dishergarh, Dist. Paschim Bardhaman, West Bengal - 713333",
        default_financial_year="FY 2024-25",
        currency_unit="INR Crores",
        statutory_mandate_csr_percent=2.0,
    ),
    SubsidiaryProfile(
        code="SECL",
        full_name="South Eastern Coalfields Limited",
        headquarters="Seepat Road, Bilaspur, Chhattisgarh - 495006",
        default_financial_year="FY 2024-25",
        currency_unit="INR Crores",
        statutory_mandate_csr_percent=2.0,
    ),
    SubsidiaryProfile(
        code="WCL",
        full_name="Western Coalfields Limited",
        headquarters="Coal Estate, Civil Lines, Nagpur, Maharashtra - 440001",
        default_financial_year="FY 2024-25",
        currency_unit="INR Crores",
        statutory_mandate_csr_percent=2.0,
    ),
    SubsidiaryProfile(
        code="NCL",
        full_name="Northern Coalfields Limited",
        headquarters="Singrauli, PO: Singrauli Colliery, Dist. Singrauli, Madhya Pradesh - 486889",
        default_financial_year="FY 2024-25",
        currency_unit="INR Crores",
        statutory_mandate_csr_percent=2.0,
    ),
    SubsidiaryProfile(
        code="MCL",
        full_name="Mahanadi Coalfields Limited",
        headquarters="Jagriti Vihar, Burla, Sambalpur, Odisha - 768020",
        default_financial_year="FY 2024-25",
        currency_unit="INR Crores",
        statutory_mandate_csr_percent=2.0,
    ),
    SubsidiaryProfile(
        code="CMPDIL",
        full_name="Central Mine Planning & Design Institute Limited",
        headquarters="Gondwana Place, Kanke Road, Ranchi, Jharkhand - 834008",
        default_financial_year="FY 2024-25",
        currency_unit="INR Crores",
        statutory_mandate_csr_percent=2.0,
    ),
    SubsidiaryProfile(
        code="CIL_HQ",
        full_name="Coal India Limited (Apex Corporate HQ)",
        headquarters="Coal Bhawan, Premise No-04 MAR, Plot No-AF-III, Action Area-1A, Newtown, Rajarhat, Kolkata - 700156",
        default_financial_year="FY 2024-25",
        currency_unit="INR Crores",
        statutory_mandate_csr_percent=2.0,
    ),
]


class SettingsManager:
    """
    Thread-safe configuration manager providing atomic persistence,
    validation, and default recovery.
    """

    def __init__(self, config_path: Optional[Path | str] = None) -> None:
        self.config_path = Path(config_path or "data/workspace/app_settings.json")
        self._lock = threading.Lock()
        self._settings: ApplicationSettings = self._load_or_initialize()

    def _load_or_initialize(self) -> ApplicationSettings:
        """Loads settings from disk if valid, otherwise creates and saves defaults."""
        if self.config_path.exists():
            try:
                raw_text = self.config_path.read_text(encoding="utf-8")
                data = json.loads(raw_text)
                settings = ApplicationSettings.model_validate(data)
                # Ensure standard subsidiaries list is populated if missing
                if not settings.custom_subsidiaries:
                    settings.custom_subsidiaries = [s for s in STANDARD_CIL_SUBSIDIARIES if s.code != settings.subsidiary.code]
                return settings
            except Exception as exc:
                logger.warning("Failed to parse existing settings from %s: %s. Reverting to factory defaults.", self.config_path, exc)

        defaults = ApplicationSettings(
            subsidiary=STANDARD_CIL_SUBSIDIARIES[0],
            custom_subsidiaries=STANDARD_CIL_SUBSIDIARIES[1:],
        )
        self._save_to_disk(defaults)
        return defaults

    def _save_to_disk(self, settings: ApplicationSettings) -> None:
        """Atomically writes settings to disk via a temporary file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.config_path.with_suffix(".tmp")
        try:
            serialized = settings.model_dump_json(indent=2)
            temp_file.write_text(serialized, encoding="utf-8")
            temp_file.replace(self.config_path)
            logger.info("Successfully persisted application settings to %s", self.config_path)
        except Exception as exc:
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)
            logger.error("Failed to persist settings to %s: %s", self.config_path, exc)
            raise

    def get_settings(self) -> ApplicationSettings:
        """Returns the current application settings."""
        with self._lock:
            return self._settings.model_copy(deep=True)

    def update_settings(self, updates: Dict[str, Any] | ApplicationSettings) -> ApplicationSettings:
        """
        Validates and applies partial or full configuration updates atomically.
        """
        with self._lock:
            current_dict = self._settings.model_dump()
            if isinstance(updates, ApplicationSettings):
                update_dict = updates.model_dump(exclude_unset=True)
            else:
                update_dict = updates

            # Deep merge updates
            for key, val in update_dict.items():
                if isinstance(val, dict) and isinstance(current_dict.get(key), dict):
                    current_dict[key].update(val)
                else:
                    current_dict[key] = val

            new_settings = ApplicationSettings.model_validate(current_dict)
            self._save_to_disk(new_settings)
            self._settings = new_settings
            return self._settings.model_copy(deep=True)

    def reset_to_defaults(self) -> ApplicationSettings:
        """Restores factory default settings and persists to disk."""
        with self._lock:
            defaults = ApplicationSettings(
                subsidiary=STANDARD_CIL_SUBSIDIARIES[0],
                custom_subsidiaries=STANDARD_CIL_SUBSIDIARIES[1:],
            )
            self._save_to_disk(defaults)
            self._settings = defaults
            return self._settings.model_copy(deep=True)

    def get_available_subsidiaries(self) -> List[SubsidiaryProfile]:
        """Returns all recognized Coal India subsidiary profiles."""
        return list(STANDARD_CIL_SUBSIDIARIES)

    def select_active_subsidiary(self, code: str) -> ApplicationSettings:
        """Sets the active subsidiary profile by code."""
        with self._lock:
            target = next((s for s in STANDARD_CIL_SUBSIDIARIES if s.code.upper() == code.upper()), None)
            if not target:
                raise ValueError(f"Unknown subsidiary code: {code}. Available: {[s.code for s in STANDARD_CIL_SUBSIDIARIES]}")

            current_dict = self._settings.model_dump()
            current_dict["subsidiary"] = target.model_dump()
            new_settings = ApplicationSettings.model_validate(current_dict)
            self._save_to_disk(new_settings)
            self._settings = new_settings
            return self._settings.model_copy(deep=True)
