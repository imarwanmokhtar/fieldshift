"""fieldshift CLI — Typer subcommands (Part 3 / Phase 0).

Phase 0 implements the scaffold: `fieldshift theme` (palette/badges/symbols
visual QA) and the global --plain / --ascii accessibility flags. Later phases
add init-data, crops, fetch, validate, climate, wizard, run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from . import __version__
from .data.crops import fields_for_crop, leftovers, load_crop_table, status_counts
from .data.crops import validate as validate_crops
from .data.init import init_data
from .data.power import download_power
from .data.validate import v_all
from .ui.prompter import ScriptedPrompter
from .ui.theme import ROLES, STATUS_SPEC, SYMBOLS_ASCII, SYMBOLS_UNICODE, UiStyle
from .ui.wizard import Wizard, non_tty_exit

app = typer.Typer(
    help="Field Shift — rotation exploration for the Egypt pilot (supports, "
    "does not replace, farmer judgment).",
    no_args_is_help=False,
    add_completion=False,
)


class Flags:
    plain: bool = False
    ascii_symbols: bool = False
    data_dir: str = "FieldShift_Data"


PALETTE_ROLE_ORDER = [
    "brand",
    "ok",
    "warn",
    "error",
    "muted",
    "nasa",
    "fao",
    "farmer",
    "estimate",
    "unknown",
]


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    plain: Annotated[
        bool, typer.Option("--plain", help="No colors (automatic under NO_COLOR).")
    ] = False,
    ascii_symbols: Annotated[
        bool, typer.Option("--ascii", help="ASCII symbols instead of unicode glyphs.")
    ] = False,
    data_dir: Annotated[
        str, typer.Option("--data-dir", help="Path to the FieldShift_Data folder.")
    ] = "FieldShift_Data",
    answers: Annotated[
        str | None, typer.Option("--answers", help="JSON file of scripted answers.")
    ] = None,
) -> None:
    """Global accessibility flags for limited terminals and CI."""
    Flags.plain = plain
    Flags.ascii_symbols = ascii_symbols
    Flags.data_dir = data_dir
    if ctx.invoked_subcommand is not None:
        return
    # default: run the wizard (or scripted run if --answers given)
    if answers:
        import json

        data = json.loads(Path(answers).read_text(encoding="utf-8"))
        try:
            _run_wizard_scripted(data)
        except (KeyError, ValueError, OSError, RuntimeError) as exc:
            typer.echo(f"fieldshift: {exc}", err=True)
            raise typer.Exit(code=2) from None
        return
    if non_tty_exit() != 0:
        raise typer.Exit(code=2)
    _run_wizard_interactive()


def _console(ui: UiStyle) -> Console:
    console = Console(theme=ui.rich_theme(), no_color=ui.plain)
    if console.width < 80:
        console.options.max_width = 80  # Part 3: minimum width 80 columns
    return console


@app.command()
def theme(
    export: Annotated[
        str | None,
        typer.Option("--export", help="Export the screen to an .svg/.html file."),
    ] = None,
) -> None:
    """Show the palette, status badges and symbols (visual QA, Part 10)."""
    ui = UiStyle(plain=Flags.plain, ascii_symbols=Flags.ascii_symbols)
    console = _console(ui)

    mode = (
        ("plain" if ui.plain else "color")
        + "+"
        + ("ascii" if ui.ascii_symbols else "unicode")
        + " symbols"
    )
    console.rule(f"[brand]Field Shift theme — v{__version__} — {mode}", style="brand")

    console.print("\n[bold]Palette[/bold]")
    t = Table("role", "color", "used for", box=None, header_style="muted")
    for role in PALETTE_ROLE_ORDER:
        sample = (
            Text("██████", style=ui.style(role))
            if not ui.plain
            else Text("(no color)", style="muted")
        )
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

    console.print(
        "\n[muted]NO_COLOR="
        + ("set" if ui.plain else "not set")
        + " — every status is carried by a word, never by color alone.[/muted]"
    )

    if export:
        console.save_text(export)
        console.print("[muted]screen saved to[/muted]", export)


@app.command("init-data")
def init_data_cmd() -> None:
    """Create the FieldShift_Data skeleton and write seed files (Phase 1)."""
    ui = UiStyle(plain=Flags.plain, ascii_symbols=Flags.ascii_symbols)
    console = _console(ui)
    result = init_data(Path(Flags.data_dir))
    console.print(f"[ok]initialised data dir:[/ok] {result['data_dir']}")
    if result["created"]:
        console.print("[muted]created:[/muted]")
        for p in result["created"]:
            console.print(f"  [brand]•[/brand] {p}")
    else:
        console.print("[muted]nothing to create — all seed files already present.[/muted]")


@app.command()
def crops(
    status: bool = typer.Option(False, "--status", help="Show crops x fields status table."),
) -> None:
    """Crop reference table with status badges (DATA.md §7.5)."""
    ui = UiStyle(plain=Flags.plain, ascii_symbols=Flags.ascii_symbols)
    console = _console(ui)
    path = Path(Flags.data_dir) / "cleaned" / "crop_reference.yaml"
    if not path.is_file():
        console.print(
            "[error]✖ missing[/error] crop_reference.yaml — run `fieldshift init-data` first."
        )
        raise typer.Exit(code=1)
    table = load_crop_table(path)
    errs, _ = validate_crops(table.doc)
    console.rule("[brand]Crop reference — status[/brand]", style="brand")
    console.print(f"[muted]source:[/muted] {path}  [muted]schema:[/muted] {table.schema_version}")
    if errs:
        console.print(f"[error]✖ {len(errs)} validation error(s)[/error]")
        for e in errs:
            console.print(f"  [error]•[/error] {e}")
    else:
        console.print("[ok]✔ validation: 0 errors[/ok]")

    # crops × fields badges
    t = Table("crop_id", "usual_slot", box=None, header_style="muted")
    field_names = [
        "sowing_window",
        "growth_duration_days",
        "stage_days",
        "kc",
        "water_requirement_mm_ref",
        "temperature_c",
        "drought_sensitivity",
        "salinity_threshold_ece_dsm",
        "soil_ph_range",
    ]
    for fn in field_names:
        t.add_column(fn, style="muted")
    for c in table.crops:
        cid = c.get("crop_id")
        fmap = {f: b for f, b in fields_for_crop(c)}
        row = [cid, c.get("usual_slot", "")]
        for fn in field_names:
            row.append(ui.badge(fmap.get(fn, "missing")))
        t.add_row(*row)
    console.print(t)

    # status counts
    sc = status_counts(table.doc)
    console.print("\n[bold]Status counts[/bold]")
    for k in sorted(sc):
        console.print(f"  {k}: {sc[k]}")

    # §7.5 leftovers
    left = leftovers(table.doc)
    console.print(f"\n[bold]§7.5 fill-in checklist ({len(left)} open)[/bold]")
    for x in left:
        console.print(f"  [warn]▲[/warn] {x}")


@app.command()
def version() -> None:
    """Print the engine version."""
    console = _console(UiStyle(plain=Flags.plain, ascii_symbols=Flags.ascii_symbols))
    console.print(f"fieldshift {__version__}")


@app.command()
def demo() -> None:
    """Pilot-point demo run (offline, scripted)."""
    ui, console, crop_ids, template_ids, dd = _wizard_context()
    pilot_answers = {
        "start": "new",
        "loc_mode": "pilot",
        "coords_real": False,
        "loc_name": None,
        "prev_crop": "wheat",
        "prev_season": "winter",
        "has_earlier": False,
        "irrigation": "canal",
        "water_avail": "moderate",
        "soil_test": False,
        "area": None,
        "prio_rank": [
            "reduce_water_use",
            "support_soil_health",
            "improve_climate_resilience",
            "maintain_productivity",
            "__stop__",
        ],
        "budget_market": "none",
        "data_mode": "offline",
        "period": "2020-2025",
        "horizon": 2,
        "strat_source": "templates",
        "existing_edit": True,
        "existing_other_crop": "maize",
        "templates": ["faba_maize", "wheat_sorghum"],
        "review": "run",
        "after_run": "exit",
    }
    prompter = ScriptedPrompter(pilot_answers)
    wiz = Wizard(prompter, crop_ids, template_ids, dd, ui, console)
    try:
        answers = wiz.run()
    except SystemExit:
        raise
    profile_path = _save_profile(dd, answers, wiz)
    result, out_dir = _execute_profile(profile_path, dd, period="2020-2025", fetch=False)
    _after_run(result, out_dir, prompter, ui, console)


def _wizard_context():
    ui = UiStyle(plain=Flags.plain, ascii_symbols=Flags.ascii_symbols)
    console = _console(ui)
    dd = Path(Flags.data_dir)
    ct_path = dd / "cleaned" / "crop_reference.yaml"
    crop_ids = []
    if ct_path.is_file():
        crop_ids = load_crop_table(ct_path).crop_ids
    # template ids
    tpl_path = dd / "references" / "rotation_templates.yaml"
    template_ids = []
    if tpl_path.is_file():
        import yaml

        d = yaml.safe_load(tpl_path.read_text(encoding="utf-8")) or {}
        template_ids = [t["id"] for t in d.get("templates", [])]
    return ui, console, crop_ids, template_ids, dd


def _run_wizard_interactive() -> None:
    ui, console, crop_ids, template_ids, dd = _wizard_context()
    from .ui.prompter import QuestionaryPrompter

    prompter = QuestionaryPrompter(ui)
    wiz = Wizard(prompter, crop_ids, template_ids, dd, ui, console)
    try:
        answers = wiz.run()
    except SystemExit:
        raise
    profile_path = _save_profile(dd, answers, wiz)
    if answers.get("review") == "run":
        try:
            result, out_dir = _execute_profile(
                profile_path, dd, fetch=answers.get("data_mode") in ("fetch", "auto")
            )
        except (ValueError, FileNotFoundError, OSError, RuntimeError) as exc:
            console.print(f"[error]✖ {exc}[/error]")
            raise typer.Exit(code=1) from None
        _after_run(result, out_dir, prompter, ui, console)


def _run_wizard_scripted(answers: dict) -> None:
    ui, console, crop_ids, template_ids, dd = _wizard_context()
    prompter = ScriptedPrompter(answers)
    wiz = Wizard(prompter, crop_ids, template_ids, dd, ui, console)
    try:
        answers_out = wiz.run()
    except SystemExit:
        raise
    profile_path = _save_profile(dd, answers_out, wiz)
    if answers_out.get("review") == "run":
        result, out_dir = _execute_profile(
            profile_path, dd, fetch=answers_out.get("data_mode") in ("fetch", "auto")
        )
        _after_run(result, out_dir, prompter, ui, console)


def _save_profile(dd: Path, answers: dict, wiz: Wizard) -> Path:
    import json
    from datetime import datetime

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = dd.parent / "runs" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "profile.json").write_text(
        json.dumps(
            {"answers": answers, "flags": wiz.flags, "chosen_priorities": wiz.chosen_priorities},
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )
    ui = UiStyle(plain=Flags.plain, ascii_symbols=Flags.ascii_symbols)
    console = _console(ui)
    console.print(f"[ok]Profile saved:[/ok] {out_dir / 'profile.json'}")
    return out_dir / "profile.json"


def _execute_profile(
    profile_path: Path,
    dd: Path,
    period: str | None = None,
    fetch: bool = False,
    offline: bool = False,
    out: Path | None = None,
    json_only: bool = False,
):
    from .export.json_export import write_json
    from .export.markdown_export import write_markdown
    from .run_service import build_result

    ui = UiStyle(plain=Flags.plain, ascii_symbols=Flags.ascii_symbols)
    console = _console(ui)
    run_id = profile_path.parent.name if profile_path.parent.name else None
    result = build_result(
        profile_path, dd, period=period, fetch=fetch, offline=offline, run_id=run_id
    )
    out_dir = out or profile_path.parent
    json_path = write_json(result, out_dir / "result.json")
    report_path = write_markdown(
        result,
        out_dir / "report.md",
        f"fieldshift run --profile {profile_path}"
        + (f" --period {period}" if period else "")
        + (" --fetch" if fetch else " --offline"),
    )
    (out_dir / "run.log").write_text(
        f"run_id={result.run_id}\ncreated_at={result.created_at}\nprofile={profile_path}\n"
        f"result={json_path}\nreport={report_path}\n",
        encoding="utf-8",
    )
    if json_only:
        import json

        typer.echo(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
    else:
        from .i18n import text
        from .ui.results import show_results

        show_results(result, console, ui)
        console.print(f"\n{result.profile.get('period')} · {result.run_id}")
        console.print(f"[ok]{text('result.report_saved')}:[/ok] {json_path} · {report_path}")
    return result, out_dir


def _after_run(result, out_dir: Path, prompter, ui, console) -> None:
    import json

    from .i18n import text

    options = [
        (text(f"result.action.{key}"), key) for key in ("save", "reprio", "add", "quality", "exit")
    ]
    while True:
        action = prompter.select(
            "after_run", text("result.after_run"), text("result.after_run"), options
        )
        if action == "quality":
            from .ui.results import show_data_quality

            show_data_quality(result, console, ui)
        elif action in ("save", "exit", None):
            console.print(
                f"[ok]{text('result.report_saved')}:[/ok] "
                f"{out_dir / 'result.json'} · {out_dir / 'report.md'}"
            )
            return
        elif action in ("reprio", "add"):
            profile_path = out_dir / "profile.json"
            if not profile_path.is_file():
                console.print(f"[warn]{text('result.profile_invalid')}[/warn]")
                return
            payload = json.loads(profile_path.read_text(encoding="utf-8"))
            answers = payload.setdefault("answers", {})
            if action == "reprio":
                choices = [
                    (value.replace("_", " ").title(), value)
                    for value in (
                        "reduce_water_use",
                        "support_soil_health",
                        "improve_climate_resilience",
                        "maintain_productivity",
                    )
                ]
                ranks = prompter.multi_select(
                    "reprioritize",
                    text("result.after_run"),
                    text("result.order_priorities"),
                    choices,
                    min_select=1,
                )
                if not ranks:
                    continue
                answers["prio_rank_list"] = ranks
                payload["chosen_priorities"] = ranks
            else:
                from .analysis.rotation import load_templates

                templates = load_templates(
                    Path(Flags.data_dir) / "references" / "rotation_templates.yaml"
                )
                selected = list(answers.get("templates", []))
                choices = [
                    ((tpl.get("name") or {}).get("en", tpl["id"]), tpl["id"])
                    for tpl in templates
                    if tpl.get("id") not in selected
                ]
                if not choices:
                    console.print("[muted]No additional templates are available.[/muted]")
                    continue
                template_id = prompter.select(
                    "add_template",
                    text("result.after_run"),
                    text("result.action.add"),
                    choices,
                )
                if not template_id:
                    continue
                answers["strat_source"] = "templates"
                answers["templates"] = [*selected, template_id]
            profile_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            result, _ = _execute_profile(
                profile_path,
                Path(Flags.data_dir),
                fetch=answers.get("data_mode") in ("fetch", "auto"),
            )


@app.command("run")
def run_profile(
    profile: Annotated[Path, typer.Option("--profile", exists=True, dir_okay=False)],
    period: str | None = typer.Option(None, "--period"),
    offline: bool = typer.Option(False, "--offline"),
    fetch: bool = typer.Option(False, "--fetch"),
    out: Annotated[Path | None, typer.Option("--out")] = None,
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Run a saved profile and write result.json and report.md."""
    if offline and fetch:
        raise typer.BadParameter("choose either --offline or --fetch")
    try:
        _execute_profile(
            profile,
            Path(Flags.data_dir),
            period=period,
            fetch=fetch,
            offline=offline,
            out=out,
            json_only=json_output,
        )
    except (ValueError, FileNotFoundError, OSError, RuntimeError) as exc:
        ui = UiStyle(plain=Flags.plain, ascii_symbols=Flags.ascii_symbols)
        _console(ui).print(f"[error]✖ {exc}[/error]")
        raise typer.Exit(code=1) from None


@app.command("fetch")
def fetch_power(
    pilot: bool = typer.Option(False, "--pilot", help="Use the illustrative pilot point."),
    lat: float | None = typer.Option(None, "--lat"),
    lon: float | None = typer.Option(None, "--lon"),
    start: str = typer.Option("2020-01-01", "--start"),
    end: str = typer.Option("2025-12-31", "--end"),
) -> None:
    """Download NASA POWER daily CSV (+ sidecar) and append to the retrieval log."""
    ui = UiStyle(plain=Flags.plain, ascii_symbols=Flags.ascii_symbols)
    console = _console(ui)
    dd = Path(Flags.data_dir)
    if pilot or (lat is None and lon is None):
        lat, lon = 31.04, 31.38
    if lat is None or lon is None:
        console.print("[error]✖ provide --lat and --lon, or --pilot[/error]")
        raise typer.Exit(code=2)
    out_dir = dd / "raw" / "power"
    try:
        raw_path, meta = download_power(lat, lon, start, end, out_dir)
    except Exception as exc:
        console.print(f"[error]✖ download failed: {exc}[/error]")
        raise typer.Exit(code=1) from None
    console.print(f"[ok]✔ saved[/ok] {raw_path}")
    console.print(
        f"[muted]HTTP {meta.get('http_status')} · {meta.get('bytes')} bytes · "
        f"{meta.get('attempts')} attempt(s)[/muted]"
    )
    # append retrieval log
    import hashlib

    from .data.provenance import append_retrieval_log

    sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    append_retrieval_log(
        dd / "metadata" / "retrieval_log.jsonl",
        source_id="NASA_POWER_DAILY",
        action="download",
        url=meta["url"],
        http_status=meta.get("http_status"),
        bytes_=meta.get("bytes"),
        file=str(raw_path.relative_to(dd)),
        sha256=sha,
        note=f"fetch power {lat},{lon} {start}..{end}",
    )


@app.command("validate")
def validate_cmd(
    climate: bool = typer.Option(False, "--climate"),
    crops: bool = typer.Option(False, "--crops"),
    soil: bool = typer.Option(False, "--soil"),
    all_: bool = typer.Option(False, "--all"),
) -> None:
    """Run V-* checks; exit code 1 on errors."""
    ui = UiStyle(plain=Flags.plain, ascii_symbols=Flags.ascii_symbols)
    console = _console(ui)
    dd = Path(Flags.data_dir)
    if not (climate or crops or soil or all_):
        all_ = True
    results = v_all(dd)
    overall_errors = 0
    for key in ("climate", "crops", "soil"):
        if not (
            all_
            or (key == "climate" and climate)
            or (key == "crops" and crops)
            or (key == "soil" and soil)
        ):
            continue
        if key not in results:
            console.print(f"[muted]{key}: no file found, skipped[/muted]")
            continue
        errs, warns = results[key]
        overall_errors += len(errs)
        status = "[ok]✔[/ok]" if not errs else "[error]✖[/error]"
        console.print(f"{status} {key}: {len(errs)} error(s), {len(warns)} warning(s)")
        for e in errs:
            console.print(f"  [error]•[/error] {e}")
        for w in warns:
            console.print(f"  [warn]▲[/warn] {w}")
    if overall_errors:
        raise typer.Exit(code=1)


@app.command()
def climate(
    pilot: bool = typer.Option(False, "--pilot"),
    lat: float | None = typer.Option(None, "--lat"),
    lon: float | None = typer.Option(None, "--lon"),
) -> None:
    """Print the seasonal climate summary from cleaned files."""
    ui = UiStyle(plain=Flags.plain, ascii_symbols=Flags.ascii_symbols)
    console = _console(ui)
    dd = Path(Flags.data_dir)
    if pilot or (lat is None and lon is None):
        lat, lon = 31.04, 31.38
    locid = f"{lat:.2f}_{lon:.2f}"
    path = dd / "cleaned" / f"climate_seasonal_{locid}.csv"
    if not path.is_file():
        console.print(
            f"[error]✖ no seasonal file for {locid} — run `fieldshift fetch power` first[/error]"
        )
        raise typer.Exit(code=1)
    import pandas as pd

    df = pd.read_csv(path)
    console.rule(f"[brand]Climate summary — {locid}[/brand]", style="brand")
    console.print(df.to_string(index=False))


@app.command()
def explain(indicator: str) -> None:
    """Print the definition of an analysis indicator."""
    from .i18n import load_strings

    key = indicator if indicator.startswith("ind.") else f"ind.{indicator}"
    definition = load_strings().get(key)
    console = _console(UiStyle(plain=Flags.plain, ascii_symbols=Flags.ascii_symbols))
    if definition is None:
        console.print(f"[error]✖ No definition for indicator '{indicator}'.[/error]")
        raise typer.Exit(code=1)
    console.print(f"[bold]{indicator}[/bold]")
    console.print(definition)


def run() -> None:
    app()


if __name__ == "__main__":
    app()
