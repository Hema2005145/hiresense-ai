"""
Application configuration.

All runtime configuration is centralized here using Pydantic Settings.
Every other module reads configuration through the `get_settings()`
dependency instead of calling `os.environ` directly. This keeps
configuration testable (you can override `Settings` in tests) and
makes every tunable value discoverable in one place.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Strongly typed application settings.

    Values are loaded, in order of precedence, from:
    1. Actual environment variables
    2. A `.env` file in the backend/ directory
    3. The defaults declared below

    Never hardcode secrets in code. Never commit a real `.env` file —
    only `.env.example` is checked into version control.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App metadata ---
    app_name: str = "HireSense AI"
    app_version: str = "0.1.0"
    environment: Literal["local", "development", "production", "test"] = "local"
    debug: bool = True

    # --- API ---
    api_v1_prefix: str = "/api/v1"
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])

    # --- Database ---
    # SQLite for local dev by default; overridden with a Postgres URL in
    # production via the DATABASE_URL environment variable.
    database_url: str = "sqlite:///./hiresense.db"

    # --- Logging ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # --- LLM Provider ---
    # `llm_provider` selects which concrete implementation the
    # LLMProviderFactory returns. Switching providers is a one-line
    # config change — no code changes required elsewhere in the app.
    llm_provider: Literal["gemini", "openai", "claude"] = "gemini"

    gemini_api_key: str = ""
    gemini_model_name: str = "gemini-1.5-flash"

    openai_api_key: str = ""
    openai_model_name: str = "gpt-4o-mini"

    anthropic_api_key: str = ""
    anthropic_model_name: str = "claude-sonnet-4-6"

    # --- Embeddings / Vector store (used starting Module 6/8, declared
    # now so config stays centralized from the start) ---
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    faiss_index_path: str = "./data/faiss_index"

    # --- File storage ---
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 10


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    `lru_cache` ensures the .env file and environment are parsed only
    once per process, and lets FastAPI's dependency injection hand out
    the same Settings object everywhere via `Depends(get_settings)`.
    """
    return Settings()
