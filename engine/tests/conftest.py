"""Shared test setup: tests never call a real LLM.

Every test starts with no LLM key configured, so the full analysis uses the template
text instead of calling Groq/OpenRouter/Gemini/Claude over the network. Tests that
check a provider replace `app.llm.settings` with their own stub (and a fake HTTP call),
which takes precedence over this default.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def no_real_llm(monkeypatch):
    import app.llm as llm
    monkeypatch.setattr(llm, "settings", type("NoLlmKeys", (), {
        "LLM_PROVIDER": "", "GROQ_API_KEY": "", "OPENROUTER_API_KEY": "", "GEMINI_API_KEY": "",
        "ANTHROPIC_API_KEY": "", "LLM_MODEL": ""})())
