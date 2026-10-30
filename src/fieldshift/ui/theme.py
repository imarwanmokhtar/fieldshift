"""ui/theme.py — palette, symbols and status badges (CLAUDE.md Part 6.3).

Defined once and reused everywhere:
  * PALETTE  — role → Rich style string (used for a rich Theme and by hand)
  * SYMBOLS  — unicode glyphs with an ASCII fallback for limited terminals
  * UiBadge  — rendered by one function badge(status), DATA.md §0.2; never
               convey a status by color alone (always symbol + word)

Modes are orthogonal booleans, not a mode enum:
  plain         no colors (--plain or NO_COLOR)
  ascii_symbols ASCII fallback glyphs (--ascii)
"""
from __future__ import annotations

import os

import questionary
from rich.text import Text
from rich.theme import Theme as RichTheme

# ---------------------------------------------------------------- palette
PALETTE: dict[str, str] = {
    "brand": "#00D7FF bold",        # title, question mark, section rules, header chips
    "ok": "#5FD75F",                # pointer, chosen answer, ✔, "Good" band
    "selected": "#5FD75F bold",     # chosen answer
    "warn": "#FFD75F",              # ▲ placeholder, warnings, "Moderate" band
    "error": "#FF5F5F",             # ✖, validation errors, "Poor" band, missing
    "muted": "#808080",             # hints, definitions, instructions
    "nasa": "#5F87FF",              # NASA POWER badges
    "fao": "#00AF87",               # FAO / crop-table badges
    "farmer": "#D75FD7",            # values typed by the user
    "estimate": "#FF8700",          # engine estimates
    "unknown": "italic #808080",    # "unknown" band
}
ROLES = {  # role -> used for (shown in `fieldshift theme`)
    "brand": "title, question mark, section rules, header chips",
    "ok": "pointer, chosen answer, good band",
    "warn": "placeholder badge, warnings, moderate band",
    "error": "errors, poor band, missing badge",
    "muted": "hints, definitions, instructions",
    "nasa": "NASA POWER badges",
    "fao": "FAO / crop-table badges",
    "farmer": "values typed by the user",
    "estimate": "engine estimates",
    "unknown": "unknown band",
}

SYMBOLS_UNICODE: dict[str, str] = {
    "ok": "✔",
    "error": "✖",
    "warning": "▲",
    "extracted": "●",
    "general": "○",
    "farmer": "◆",
    "pointer": "❯",
    "back": "←",
    "other": "✎",
    "progress": "━",
}
SYMBOLS_ASCII: dict[str, str] = {
    "ok": "+",
    "error": "x",
    "warning": "!",
    "extracted": "*",
    "general": "o",
    "farmer": "@",
    "pointer": ">",
    "back": "<",
    "other": "~",
    "progress": "-",
}

# DATA.md §0.2 — status -> (word, symbol key, palette role)
STATUS_SPEC: dict[str, tuple[str, str, str]] = {
    "verified": ("verified", "ok", "ok"),
    "extracted": ("extracted", "extracted", "brand"),
    "general_fact": ("general", "general", "muted"),
    "placeholder": ("placeholder", "warning", "warn"),
    "missing": ("missing", "error", "error"),
    "farmer": ("farmer", "farmer", "farmer"),
}
DATASET_BADGES = {  # dataset provenance chips (DATA.md §4 roles)
    "NASA POWER": "nasa",
    "FAO": "fao",
}
BAND_STYLE = {"Good": "ok", "Moderate": "warn", "Poor": "error", "Unknown": "unknown"}


class UiStyle:
    """Resolve styles + symbols for the current terminal mode."""

    def __init__(self, *, plain: bool = False, ascii_symbols: bool = False) -> None:
        # NO_COLOR wins over anything else (see https://no-color.org)
        env_plain = os.environ.get("NO_COLOR") is not None
        self.plain = plain or env_plain
        self.ascii_symbols = ascii_symbols

    # -- symbols ------------------------------------------------------------
    def symbol(self, key: str) -> str:
        if self.ascii_symbols:
            return SYMBOLS_ASCII.get(key, "?")
        return SYMBOLS_UNICODE.get(key, "?")

    # -- styles ---------------------------------------------------------------
    def style(self, role: str) -> str:
        return "" if self.plain else PALETTE.get(role, "")

    def rich_theme(self) -> RichTheme:
        styles = {name: PALETTE[name] for name in PALETTE if not self.plain}
        return RichTheme(styles)

    def questionary_style(self) -> "questionary.Style":
        if self.plain:
            return questionary.Style([])  # fall back to no custom colors
        return questionary.Style(
            [
                ("qmark", "fg:#00d7ff bold"),
                ("question", "bold"),
                ("answer", "fg:#5fd75f bold"),
                ("pointer", "fg:#5fd75f bold"),
                ("highlighted", "fg:#5fd75f bold"),
                ("selected", "fg:#5fd75f"),
                ("instruction", "fg:#808080 italic"),
                ("disabled", "fg:#808080 italic"),
                ("separator", "fg:#808080"),
            ]
        )

    # -- badges ----------------------------------------------------------------
    def badge(self, status: str) -> Text:
        """One function for every status badge, reused everywhere (Part 6.3)."""
        if status in STATUS_SPEC:
            word, sym_key, role = STATUS_SPEC[status]
            style = self.style(role)
        else:  # defensive: an unlisted status must still print a word
            word, sym_key, style = status, "error", self.style("muted")
        return Text(f"{self.symbol(sym_key)} {word}", style=style)

    def band(self, name: str) -> Text:
        style = self.style(BAND_STYLE.get(name, "unknown"))
        return Text(name, style=style)

    def chip(self, dataset: str) -> Text:
        style = self.style(DATASET_BADGES.get(dataset, "muted"))
        return Text(dataset, style=style)


UI_STYLE = UiStyle()  # default instance; prompter/UI modules may create their own
