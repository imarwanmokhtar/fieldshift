"""Engine settings, read from environment variables (and engine/.env if present)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ENGINE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ENGINE_DIR / ".env")


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class Settings:
    ENGINE_API_KEY: str = field(default_factory=lambda: _env("ENGINE_API_KEY"))
    SUPABASE_URL: str = field(default_factory=lambda: _env("SUPABASE_URL").rstrip("/"))
    SUPABASE_SERVICE_ROLE_KEY: str = field(default_factory=lambda: _env("SUPABASE_SERVICE_ROLE_KEY"))
    # LLM provider: "openrouter", "gemini" or "anthropic". Empty = picked automatically from whichever key is set.
    LLM_PROVIDER: str = field(default_factory=lambda: _env("LLM_PROVIDER").lower())
    OPENROUTER_API_KEY: str = field(default_factory=lambda: _env("OPENROUTER_API_KEY"))
    GEMINI_API_KEY: str = field(default_factory=lambda: _env("GEMINI_API_KEY"))
    ANTHROPIC_API_KEY: str = field(default_factory=lambda: _env("ANTHROPIC_API_KEY"))
    # Empty = default for the provider (see llm.DEFAULT_MODELS).
    LLM_MODEL: str = field(default_factory=lambda: _env("LLM_MODEL"))
    COPERNICUS_CLIENT_ID: str = field(default_factory=lambda: _env("COPERNICUS_CLIENT_ID"))
    COPERNICUS_CLIENT_SECRET: str = field(default_factory=lambda: _env("COPERNICUS_CLIENT_SECRET"))
    # Return realistic mock values for the stubbed layers (NDVI, SMAP, IMERG).
    # Mocked layers are always labelled "mock" in the evidence pack.
    USE_MOCK_LAYERS: bool = field(default_factory=lambda: _env("USE_MOCK_LAYERS", "false").lower() in ("1", "true", "yes"))
    # On Vercel only /tmp is writable.
    CACHE_DIR: Path = field(default_factory=lambda: Path(_env("CACHE_DIR", "/tmp/fieldshift-cache" if os.getenv("VERCEL") else str(ENGINE_DIR / ".cache"))))
    # Sync mode: /analyze finishes the whole analysis before replying (needed on serverless hosts
    # like Vercel, where work after the reply may be stopped). On by default when running on Vercel.
    ENGINE_SYNC: bool = field(default_factory=lambda: _env("ENGINE_SYNC", "true" if os.getenv("VERCEL") else "false").lower() in ("1", "true", "yes"))
    DATA_DIR: Path = ENGINE_DIR / "data"
    # Years of NASA POWER history to analyse.
    POWER_START: str = field(default_factory=lambda: _env("POWER_START", "20150101"))
    POWER_END: str = field(default_factory=lambda: _env("POWER_END", "20251231"))


settings = Settings()
