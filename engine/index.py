"""Entry point for Vercel's Python runtime (it looks for a top-level `app` here).
Locally and in Docker, run `uvicorn app.main:app` instead."""
from app.main import app  # noqa: F401
