"""Configuration settings for UK Wind Forecast Accuracy Analytics."""

import os
from pathlib import Path
from typing import Any, List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable override support."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "Wind Forecast Intelligence Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Elexon BMRS API Configuration
    ELEXON_API_BASE_URL: str = "https://data.elexon.co.uk/bmrs/api/v1"
    ELEXON_HTTP_TIMEOUT: float = 30.0
    ELEXON_MAX_RETRIES: int = 3
    ELEXON_RETRY_BACKOFF: float = 1.0

    # Default Analysis Parameters (January 2026 Purchase Decisions)
    DEFAULT_START_DATE: str = "2026-01-01"
    DEFAULT_END_DATE: str = "2026-01-31"
    DEFAULT_CUTOFF_TYPE: str = "day_ahead_fixed"
    DEFAULT_CUTOFF_TIME_UK: str = "11:00"

    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    CACHE_DIR: Path = BASE_DIR / "data" / "cache"
    FIXTURES_DIR: Path = BASE_DIR / "data" / "fixtures"

    # CORS Origins (supports comma-separated string or list)
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://wind-forecast-omega.vercel.app",
        "*"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            if "https://wind-forecast-omega.vercel.app" not in origins:
                origins.append("https://wind-forecast-omega.vercel.app")
            return origins
        return v


settings = Settings()

# Ensure runtime directories exist
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
settings.FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
