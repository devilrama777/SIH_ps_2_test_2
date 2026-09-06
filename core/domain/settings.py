"""
Domain models for Application Settings and Configuration — Section 24 & Section 33.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class SubsidiaryProfile(BaseModel):
    """Configuration profile for the active Coal India subsidiary or headquarters."""
    code: str = Field(default="CCL", description="Subsidiary code (e.g. CCL, BCCL, ECL, SECL, WCL, NCL, MCL, CMPDIL, CIL_HQ)")
    full_name: str = Field(default="Central Coalfields Limited", description="Official corporate name")
    headquarters: str = Field(default="Darbhanga House, Ranchi, Jharkhand", description="Registered headquarters address")
    default_financial_year: str = Field(default="FY 2024-25", description="Primary reporting period")
    currency_unit: str = Field(default="INR Crores", description="Financial reporting denomination")
    statutory_mandate_csr_percent: float = Field(default=2.0, description="Statutory CSR mandate percentage of 3-year avg net profits")


class AISettings(BaseModel):
    """Local AI inference runtime and hardware allocation settings."""
    active_backend: str = Field(default="rule_based", description="Selected local engine: 'rule_based', 'llama_cpp', or 'local_server'")
    model_name: str = Field(default="Gemma-2-9B-It-Q4_K_M", description="Active model identifier")
    model_path: Optional[str] = Field(default=None, description="Absolute filesystem path to GGUF model weights")
    context_window_tokens: int = Field(default=8192, ge=2048, le=32768, description="Active context window size")
    max_output_tokens: int = Field(default=2048, ge=256, le=8192, description="Maximum tokens per generation pass")
    temperature: float = Field(default=0.2, ge=0.0, le=1.0, description="Sampling temperature (lower for deterministic factual fidelity)")
    cpu_threads: int = Field(default=8, ge=1, le=64, description="Allocated CPU execution threads")
    gpu_offload_layers: int = Field(default=0, ge=0, le=99, description="Layers offloaded to local GPU (0 for CPU-first)")


class StorageSettings(BaseModel):
    """Storage lifecycle management and cache pruning configuration."""
    cache_retention_days: int = Field(default=30, ge=1, le=365, description="Retention lifespan for parsed canonical document caches")
    temp_auto_prune_interval_hours: int = Field(default=24, ge=1, le=168, description="Background interval to clear scratch buffers")
    auto_cleanup_enabled: bool = Field(default=True, description="Automatically prune expired scratch buffers")
    dry_run_safety_lock: bool = Field(default=False, description="When true, simulate deletions without removing files")


class SecuritySettings(BaseModel):
    """Air-gapped security, loopback, and access controls."""
    strict_local_loopback: bool = Field(default=True, description="Strictly restrict service bindings to 127.0.0.1")
    allow_external_network: bool = Field(default=False, description="Default-deny outbound internet access")
    audit_log_retention_days: int = Field(default=365, ge=30, le=3650, description="Cryptographic audit trail retention period")
    require_dual_authorization_export: bool = Field(default=True, description="Require formal human sign-off before report export/upload")
    cryptographic_digest_algo: str = Field(default="SHA-256", description="Digest algorithm for audit logs and artifact manifests")


class TemplateSettings(BaseModel):
    """Report styling, layout, and visual presentation preferences."""
    default_visual_mode: str = Field(default="modern", description="Default report template: 'classic' or 'modern'")
    brand_primary_color: str = Field(default="#0B3C5D", description="Corporate primary accent hex color (CIL Navy Blue)")
    brand_secondary_color: str = Field(default="#D97706", description="Secondary accent hex color (CIL Amber Gold)")
    font_family_heading: str = Field(default="Outfit, sans-serif", description="Primary heading typography")
    font_family_body: str = Field(default="Inter, sans-serif", description="Primary body typography")
    include_cover_imagery: bool = Field(default=True, description="Include corporate hero imagery on report title page")


class ApplicationSettings(BaseModel):
    """Unified application settings encompassing all functional areas."""
    version: str = Field(default="0.1.0", description="Schema version of configuration")
    subsidiary: SubsidiaryProfile = Field(default_factory=SubsidiaryProfile)
    ai: AISettings = Field(default_factory=AISettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    template: TemplateSettings = Field(default_factory=TemplateSettings)
    custom_subsidiaries: List[SubsidiaryProfile] = Field(default_factory=list)
