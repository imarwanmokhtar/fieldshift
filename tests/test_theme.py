"""Theme unit tests (Phase 0 acceptance: badges + symbols render in all modes)."""

import pytest
from rich.text import Text

from fieldshift.ui.theme import (
    STATUS_SPEC,
    SYMBOLS_ASCII,
    SYMBOLS_UNICODE,
    UiStyle,
)


def test_all_statuses_have_badge_words():
    assert set(STATUS_SPEC) == {
        "verified", "extracted", "general_fact", "placeholder",
        "missing", "farmer",
    }
    for word, _, _ in STATUS_SPEC.values():
        assert word  # every status is conveyed by a word, never by color alone


@pytest.mark.parametrize(
    "status", ["verified", "extracted", "general_fact", "placeholder", "missing", "farmer"]
)
def test_badge_contains_word_in_every_mode(status):
    expected_word = STATUS_SPEC[status][0]
    for ui in (
        UiStyle(plain=False), UiStyle(plain=True),
        UiStyle(ascii_symbols=True), UiStyle(plain=True, ascii_symbols=True),
    ):
        t = ui.badge(status)
        assert isinstance(t, Text) and expected_word in t.plain


def test_badge_unknown_status_prints_a_word():
    t = UiStyle().badge("my_custom_status")
    assert "my_custom_status" in t.plain  # never crashes, never color-only


def test_ascii_fallback_covers_every_symbol():
    assert set(SYMBOLS_ASCII) == set(SYMBOLS_UNICODE)
    uni = UiStyle(ascii_symbols=False).symbol("error")
    asc = UiStyle(ascii_symbols=True).symbol("error")
    assert uni == "✖" and asc == "x"


def test_plain_mode_styles_are_empty_and_colored_mode_matches_palette(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    ui = UiStyle(plain=True)
    assert ui.style("error") == "" and ui.style("brand") == ""
    assert UiStyle().style("error") == "#FF5F5F"


def test_no_color_env(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert UiStyle().plain is False          # unset -> colors allowed

    monkeypatch.setenv("NO_COLOR", "1")
    assert UiStyle().plain is True           # set -> plain wins (https://no-color.org)

