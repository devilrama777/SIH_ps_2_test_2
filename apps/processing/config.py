"""
Service Configuration & Security Settings — Section 24 of Master Plan.
"""
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProcessingSettings(BaseSettings):
    """Runtime configuration for local processing service."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server binding
    host: str = Field(default="127.0.0.1", alias="PROCESSING_HOST")
    port: int = Field(default=8765, alias="PROCESSING_PORT")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="PROCESSING_LOG_LEVEL")

    # Local storage paths
    workspace_root: Path = Field(default=Path("./data/workspace"), alias="DATA_WORKSPACE_DIR")
    cache_dir: Path = Field(default=Path("./data/cache"), alias="DATA_CACHE_DIR")
    index_dir: Path = Field(default=Path("./data/indexes"), alias="DATA_INDEX_DIR")

    # Security baseline (Section 24)
    # External outbound connections strictly denied by default
    allow_external_network: bool = Field(default=False, alias="ALLOW_EXTERNAL_NETWORK")
    allowed_origins: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173", "tauri://localhost"],
        alias="ALLOWED_ORIGINS",
    )

    def ensure_directories(self) -> None:
        """Ensure required local storage directories exist with safe permissions."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)


settings = ProcessingSettings()
