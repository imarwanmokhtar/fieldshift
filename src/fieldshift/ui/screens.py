"""ui/screens.py — banner, section headers, summary tables, progress stages (Phase 3)."""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .theme import UiStyle


def banner(console: Console, ui: UiStyle, version: str = "0.1.0") -> None:
    body = (
        f"NASA Space Apps 2026 · Egypt pilot (Dakahlia)\n"
        f"engine v{version}\n\n"
        "This tool supports your decisions. It does not replace your own\n"
        "experience or local agricultural experts."
    )
    console.print(Panel(body, title="[brand]FIELD SHIFT · Rotation Explorer[/brand]",
                        border_style="brand", padding=(1, 2)))


def step_header(console: Console, ui: UiStyle, header: str, step: int, total: int) -> None:
    width = 24
    filled = int(width * step / max(total, 1))
    bar = "━" * filled + "─" * (width - filled)
    if ui.ascii_symbols:
        bar = "-" * filled + "." * (width - filled)
    console.print(f"[brand][ {header} ][/brand]  Step {step} of {total}  {bar}")


def summary_table(console: Console, ui: UiStyle, rows: list[tuple[str, str, str]]) -> None:
    """rows: (field, answer, source/status)."""
    t = Table("Field", "Your answer", "Source / status", box=None, header_style="muted")
    for field, answer, src in rows:
        t.add_row(field, answer, src)
    console.print(t)


def flags_list(console: Console, ui: UiStyle, flags: list[str]) -> None:
    if not flags:
        console.print("[muted]No active quality flags.[/muted]")
        return
    console.print("[bold]Flags[/bold]")
    for f in flags:
        console.print(f"  [warn]▲[/warn] {f}")
