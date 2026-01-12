# RISKCORE Backend Configuration

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional
from pathlib import Path

# Get the backend directory (where this config.py lives)
BACKEND_DIR = Path(__file__).resolve().parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    IMPORTANT: RISKCORE is designed for ON-PREMISES deployment.
    All data stays on the client's local infrastructure.
    No cloud storage of positions, trades, or risk data.
    """

    # App
    app_name: str = "RISKCORE"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database (PostgreSQL - LOCAL/ON-PREMISES ONLY)
    # Format: postgresql://user:password@host:port/database
    database_url: str = "postgresql://postgres:postgres@127.0.0.1:5432/postgres"

    # Database pool settings
    db_pool_min: int = 2
    db_pool_max: int = 10

    # CORS (configure for your internal network)
    cors_origins: list[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # API
    api_v1_prefix: str = "/api/v1"

    # OpenFIGI (optional - for security master lookups)
    # Note: OpenFIGI queries don't send position data, only identifiers
    openfigi_api_key: Optional[str] = None

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
