"""fieldshift CLI — Typer subcommands (Part 3 / Phase 0).

Phase 0 implements the scaffold: `fieldshift theme` (palette/badges/symbols
visual QA) and the global --plain / --ascii accessibility flags. Later phases
add init-data, crops, fetch, validate, climate, wizard, run.
"""
from __future__ import annotations

from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .ui.theme import ROLES, SYMBOLS_ASCII, SYMBOLS_UNICODE, STATUS_SPEC, UiStyle

app = typer.Typer(
    help="Field Shift — rotation exploration for the Egypt pilot (supports, does not replace, farmer judgment).",
    no_args_is_help=True,
    add_completion=False,
)


class Flags:
    plain: bool = False
    ascii_symbols: bool = False


PALETTE_ROLE_ORDER = ["brand", "ok", "warn", "error", "muted", "nasa", "fao", "farmer", "estimate", "unknown"]


@app.callback()
def main(
    plain: Annotated[bool, typer.Option("--plain", help="No colors (automatic under NO_COLOR).")] = False,
    ascii_symbols: Annotated[bool, typer.Option("--ascii", help="ASCII symbols instead of unicode glyphs.")] = False,
) -> None:
    """Global accessibility flags for limited terminals and CI."""
    Flags.plain = plain
    Flags.ascii_symbols = ascii_symbols


def _console(ui: UiStyle) -> Console:
    console = Console(theme=ui.rich_theme(), no_color=ui.plain)
    if console.width < 80:
        console.options.max_width = 80  # Part 3: minimum width 80 columns
    return console


@app.command()
def theme(
    export: Annotated[Optional[str], typer.Option("--export", help="Export the screen to an .svg/.html file for visual QA.")] = None,
) -> None:
    """Show the palette, status badges and symbols (visual QA, Part 10)."""
    ui = UiStyle(plain=Flags.plain, ascii_symbols=Flags.ascii_symbols)
    console = _console(ui)

    mode = ("plain" if ui.plain else "color") + "+" + ("ascii" if ui.ascii_symbols else "unicode") + " symbols"
    console.rule(f"[brand]Field Shift theme — v{__version__} — {mode}", style="brand")

    console.print("\n[bold]Palette[/bold]")
    t = Table("role", "color", "used for", box=None, header_style="muted")
    for role in PALETTE_ROLE_ORDER:
        sample = Text("██████", style=ui.style(role)) if not ui.plain else Text("(no color)", style="muted")
        t.add_row(role, sample, ROLES[role])
    console.print(t)

    console.print("\n[bold]Status badges[/bold] (DATA.md §0.2)")
    t = Table("status", "rendered", box=None, header_style="muted")
    for status in STATUS_SPEC:
        t.add_row(status, ui.badge(status))
    console.print(t)

    console.print("\n[bold]Symbols[/bold]")
    t = Table("name", "unicode", "ascii fallback", box=None, header_style="muted")
    for key in SYMBOLS_UNICODE:
        t.add_row(key, SYMBOLS_UNICODE[key], SYMBOLS_ASCII[key])
    console.print(t)

    console.print(f"\n[muted]NO_COLOR={'set' if ui.plain else 'not set'} — every status is carried by a word, never by color alone.[/muted]")

    if export:
        console.save_text(export)
        console.print("[muted]screen saved to[/muted]", export)


@app.command()
def version() -> None:
    """Print the engine version."""
    console = _console(UiStyle(plain=Flags.plain, ascii_symbols=Flags.ascii_symbols))
    console.print(f"fieldshift {__version__}")


@app.command()
def demo() -> None:
    """Pilot-point demo run (implemented in a later phase)."""
    console = _console(UiStyle(plain=Flags.plain, ascii_symbols=Flags.ascii_symbols))
    console.print("[warn]▲ The demo is not built yet — it arrives with the wizard phase.[/warn]")
    raise typer.Exit(code=1)


def run() -> None:
    app()


if __name__ == "__main__":
    app()
