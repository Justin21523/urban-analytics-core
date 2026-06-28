"""
Base settings and configuration loader.

Provides:
- Pydantic-based typed settings with defaults
- YAML config file loading + deep merge
- Environment variable override support
- .env auto-loading
- TDX credential helpers (reused across all 5 projects)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


def project_root() -> Path:
    """Resolve the project root (2 levels above this file = src/)."""
    return Path(__file__).resolve().parents[2]


def _resolve_path(root: Path, value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else root / p


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dicts. Override wins on conflict."""
    result = base.copy()
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_yaml(path: str | Path) -> dict:
    """Load a YAML file, returning empty dict if missing."""
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ─── TDX Section (shared across ALL 5 projects) ───


class TdxSettings(BaseModel):
    """TDX API configuration — shared by all urban analytics projects."""

    base_url: str = "https://tdx.transportdata.tw/api/basic/v2"
    base_url_v1: str = "https://tdx.transportdata.tw/api/basic/v1"
    historical_url: str = "https://tdx.transportdata.tw/api/historical"
    token_url: str = (
        "https://tdx.transportdata.tw/auth/realms/"
        "TDXConnect/protocol/openid-connect/token"
    )
    client_id: str = ""
    client_secret: str = ""
    request_timeout: float = 30.0
    max_retries: int = 3
    retry_backoff: float = 1.0
    backoff_multiplier: float = 2.0
    max_backoff: float = 60.0
    jitter: float = 0.25
    respect_retry_after: bool = True
    min_interval: float = 0.0


# ─── Path Section ───


class PathSettings(BaseModel):
    raw_dir: Path = Path("data/raw")
    processed_dir: Path = Path("data/processed")
    cache_dir: Path = Path("data/cache")
    outputs_dir: Path = Path("outputs")
    logs_dir: Path = Path("logs")


# ─── API Section ───


class CorsSettings(BaseModel):
    allow_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:8003",
            "http://127.0.0.1:8003",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )


class ApiCacheSettings(BaseModel):
    enabled: bool = True
    ttl_seconds: int = 60


class ApiRateLimitSettings(BaseModel):
    enabled: bool = True
    window_seconds: int = 60
    max_requests: int = 60


class ApiSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors: CorsSettings = Field(default_factory=CorsSettings)
    cache: ApiCacheSettings = Field(default_factory=ApiCacheSettings)
    rate_limit: ApiRateLimitSettings = Field(
        default_factory=ApiRateLimitSettings
    )


# ─── Logging Section ───


class LoggingSettings(BaseModel):
    level: str = "INFO"
    fmt: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    file_path: str = ""


# ─── Cache Section ───


class CacheSettings(BaseModel):
    enabled: bool = True
    ttl_seconds: int = 3600


# ─── Base App Settings (subclass per project) ───


class BaseAppSettings(BaseModel):
    """Base settings all urban analytics projects inherit from."""

    app_name: str = "urban-analytics"
    timezone: str = "Asia/Taipei"
    paths: PathSettings = Field(default_factory=PathSettings)
    tdx: TdxSettings = Field(default_factory=TdxSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)

    def resolve_paths(self, root: Path | None = None) -> None:
        """Resolve relative paths against project root."""
        r = root or Path.cwd()
        p = self.paths
        p.raw_dir = _resolve_path(r, p.raw_dir)
        p.processed_dir = _resolve_path(r, p.processed_dir)
        p.cache_dir = _resolve_path(r, p.cache_dir)
        p.outputs_dir = _resolve_path(r, p.outputs_dir)
        p.logs_dir = _resolve_path(r, p.logs_dir)

    def ensure_dirs(self) -> None:
        """Create all configured directories."""
        for p in [
            self.paths.raw_dir,
            self.paths.processed_dir,
            self.paths.cache_dir,
            self.paths.outputs_dir,
            self.paths.logs_dir,
        ]:
            p.mkdir(parents=True, exist_ok=True)

    def load_from_yaml(
        self, config_path: str | Path, scenario: str = ""
    ) -> "BaseAppSettings":
        """
        Load settings from YAML file + optional scenario override.
        Returns a new settings instance merged with file values.
        """
        path = Path(config_path).resolve()
        root = path.parent

        # Load .env
        from urban_analytics_core.utils.dotenv import load_dotenv

        load_dotenv(root / ".env")

        # Load base + scenario YAML
        base = load_yaml(path)
        scenario_path = root / "config" / "scenarios" / f"{scenario}.yaml"
        override = load_yaml(scenario_path)
        merged = deep_merge(base, override)

        # Merge into current settings
        return self.model_validate(merged)

    class Config:
        extra = "allow"
