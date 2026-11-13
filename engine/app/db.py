"""Minimal Supabase (PostgREST) client using the service role / secret key. Server only.

Uses plain HTTPS calls instead of the supabase-py SDK: fewer dependencies and it
works with both the legacy service_role JWT and the new `sb_secret_...` keys.
"""

from __future__ import annotations

from typing import Any

import httpx

from .settings import settings


class DbError(RuntimeError):
    pass


def _headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    if not key or not settings.SUPABASE_URL:
        raise DbError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are not set")
    h = {"apikey": key, "Content-Type": "application/json"}
    # New-style secret keys are not JWTs: send them only as `apikey`.
    if not key.startswith("sb_secret_"):
        h["Authorization"] = f"Bearer {key}"
    if extra:
        h.update(extra)
    return h


def _url(table: str) -> str:
    return f"{settings.SUPABASE_URL}/rest/v1/{table}"


def get_profile(user_id: str) -> dict[str, Any] | None:
    r = httpx.get(_url("field_profiles"), params={"user_id": f"eq.{user_id}", "select": "*"},
                  headers=_headers(), timeout=20)
    if r.status_code >= 400:
        raise DbError(f"field_profiles read failed: {r.status_code} {r.text[:200]}")
    rows = r.json()
    return rows[0] if rows else None


def get_analysis(analysis_id: str) -> dict[str, Any] | None:
    r = httpx.get(_url("analyses"), params={"id": f"eq.{analysis_id}", "select": "*"},
                  headers=_headers(), timeout=20)
    if r.status_code >= 400:
        raise DbError(f"analyses read failed: {r.status_code} {r.text[:200]}")
    rows = r.json()
    return rows[0] if rows else None


def update_analysis(analysis_id: str, **fields: Any) -> None:
    r = httpx.patch(_url("analyses"), params={"id": f"eq.{analysis_id}"}, json=fields,
                    headers=_headers({"Prefer": "return=minimal"}), timeout=30)
    if r.status_code >= 400:
        raise DbError(f"analyses update failed: {r.status_code} {r.text[:200]}")
