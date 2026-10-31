"""Phase 7 result screens (Rich only; no analysis or file I/O)."""

from __future__ import annotations

from rich.table import Table

from ..i18n import text


def _band(console, band: str) -> str:
    style = {
        "Good": "ok",
        "Moderate": "warn",
        "Poor": "error",
        "Unknown": "muted",
        "Similar": "muted",
    }.get(band, "muted")
    return f"[{style}]{band}[/{style}]"


def _bar(band: str) -> str:
    count = {"Good": 4, "Moderate": 3, "Poor": 1, "Unknown": 0, "Similar": 2}.get(band, 0)
    return "●" * count + "○" * (4 - count)


def _sequence(strategy, crop_names: dict[str, str]) -> str:
    parts = []
    current_year = None
    year_parts = []
    for step in strategy.sequence:
        if current_year is not None and step.year != current_year:
            parts.append(f"Y{current_year}: " + " / ".join(year_parts))
            year_parts = []
        current_year = step.year
        crop = crop_names.get(step.crop_id, step.crop_id.replace("_", " "))
        year_parts.append(f"{step.slot} {crop}")
    if current_year is not None:
        parts.append(f"Y{current_year}: " + " / ".join(year_parts))
    return "; ".join(parts)


def _value(value, low=None, high=None) -> str:
    if value is None:
        return text("result.no_data")
    if low is None or high is None:
        return f"{value:.1f}" if isinstance(value, float) else str(value)
    if low == high:
        return f"{value:.1f}"
    return f"{low:.1f}–{high:.1f}"


def show_data_quality(result, console, ui) -> None:
    console.rule(f"[brand]{text('result.data_quality')}[/brand]", style="brand")
    table = Table("Dataset", "Type", "Resolution", "Period", "Retrieved", "Status", box=None)
    for source in result.data_sources:
        row = dict(source)
        status = row.get("status", "missing")
        table.add_row(
            row.get("name", row.get("id", "")),
            row.get("spatial_type") or "reference",
            row.get("resolution") or "—",
            row.get("period") or "—",
            row.get("retrieved") or text("result.retrieval_unknown"),
            ui.badge(status),
        )
    console.print(table)
    if result.quality_flags:
        console.print("\n[bold]Quality flags[/bold]")
        for flag in result.quality_flags:
            console.print(f"  [warn]▲[/warn] {text(flag.text_key, flag=flag.code)}")
    else:
        console.print("[ok]No active data-quality flags.[/ok]")


def show_climate_summary(result, console) -> None:
    console.rule(f"[brand]{text('result.climate_summary')}[/brand]", style="brand")
    table = Table(
        "Season",
        "Mean T (°C)",
        "Min / max T (°C)",
        "Rain (mm)",
        "Hot / cold / frost days",
        "Complete windows",
        box=None,
    )
    for season in ("winter", "summer"):
        values = result.climate_summary.get(season, {})
        temp_min, temp_max = values.get("t_min_c"), values.get("t_max_c")
        bounds = "—" if temp_min is None or temp_max is None else f"{temp_min:.1f} / {temp_max:.1f}"
        table.add_row(
            season.title(),
            _value(values.get("t_mean_c")),
            bounds,
            _value(values.get("rain_total_mm")),
            " / ".join(
                str(values.get(key, "—")) for key in ("heat_days", "cold_days", "frost_days")
            ),
            str(values.get("n_complete_windows", 0)),
        )
    console.print(table)
    console.print(
        "[muted]NASA POWER grid values are regional context, not field measurements.[/muted]"
    )


def show_optional_context(result, console) -> None:
    if not result.optional_context:
        return
    console.rule(f"[brand]{text('result.optional_context')}[/brand]", style="brand")
    for key in ("smap", "modis"):
        panel = result.optional_context.get(key)
        if not panel:
            continue
        console.print(f"\n[bold]{panel.get('dataset', key.upper())}[/bold]")
        status = panel.get("status", "not_provided")
        status_text = text(f"context.status.{status}")
        console.print(
            f"{status_text} · {text('result.data_period')}: {panel.get('period') or '—'} · "
            f"{text('result.context.resolution')}: "
            f"{panel.get('spatial_resolution_km', panel.get('spatial_resolution_m', '—'))} "
            f"{'km' if key == 'smap' else 'm'} · "
            f"{text('result.context.unit')}: {panel.get('unit', '—')} · "
            f"{text('result.context.observations')}: {panel.get('valid_observations', 0)} "
            f"{text('result.context.excluded')}: {panel.get('excluded_observations', 0)}"
        )
        monthly = panel.get("monthly", [])
        if key == "smap":
            table = Table("Month", "Median surface moisture (m³/m³)", "Observations", box=None)
            for row in monthly:
                table.add_row(row["month"], str(row["median"]), str(row["n_observations"]))
        else:
            table = Table("Month", "Median NDVI", "Median EVI", "Observations", box=None)
            for row in monthly:
                table.add_row(
                    str(row["month"]),
                    str(row["ndvi_median"]),
                    str(row["evi_median"]),
                    str(row["n_observations"]),
                )
        if monthly:
            console.print(table)
        else:
            console.print(f"[muted]{text('result.context.no_observations')}[/muted]")
        if panel.get("quality_flags"):
            console.print(f"{text('result.context.quality')}: {panel['quality_flags']}")
        console.print(f"[muted]{panel.get('caveat', '')}[/muted]")
    console.print(f"[muted]{text('result.context.not_scored')}[/muted]")


def _strategy_indicator(strategy, indicator_id: str) -> str:
    indicator = next((item for item in strategy.indicators if item.id == indicator_id), None)
    return indicator.band if indicator else "Unknown"


def show_comparison(result, console, crop_names: dict[str, str]) -> None:
    console.rule(f"[brand]{text('result.comparison')}[/brand]", style="brand")
    table = Table(
        "Strategy",
        text("result.sequence"),
        text("result.water_demand"),
        text("result.climate_exposure"),
        text("result.soil"),
        text("result.overall"),
        box=None,
    )
    for strategy in result.strategies:
        water = _strategy_indicator(strategy, "water_demand_rel")
        climate = strategy.priority_results.get("improve_climate_resilience")
        soil = strategy.priority_results.get("support_soil_health")
        table.add_row(
            strategy.name,
            _sequence(strategy, crop_names),
            f"{_band(console, water)} {_bar(water)}",
            f"{_band(console, climate.band if climate else 'Unknown')} "
            f"{_bar(climate.band if climate else 'Unknown')}",
            f"{_band(console, soil.band if soil else 'Unknown')} "
            f"{_bar(soil.band if soil else 'Unknown')}",
            _band(console, strategy.overall.band),
        )
    console.print(table)
    comparison = result.comparison
    console.print(f"\n{text('result.order_priorities')}: {' → '.join(comparison.order) or '—'}")
    console.print(
        f"{text('result.order_equal')}: {' → '.join(comparison.order_equal_weights) or '—'}"
    )
    console.print(
        f"{text('result.ranking_stable')}: {'yes' if comparison.ranking_stable else 'no'}"
    )
    for pair in comparison.too_close:
        console.print(f"[warn]{text('result.too_close')}: {' / '.join(pair)}[/warn]")
    if comparison.priority_sensitivity:
        summary_text = comparison.priority_sensitivity["summary"]
        console.print(f"[muted]Priority sensitivity: {summary_text}[/muted]")
    console.print(f"[muted]{text('result.relative_note')}[/muted]")


def _block(console, title: str, lines: list[str]) -> None:
    console.print(f"\n[bold]{title}[/bold]")
    if not lines:
        console.print("  —")
    for line in lines:
        console.print(f"  • {line}")


def show_strategy_detail(result, console, strategy, crop_names: dict[str, str]) -> None:
    console.rule(f"[brand]{text('result.detail')}: {strategy.name}[/brand]", style="brand")
    console.print(f"{text('result.sequence')}: {_sequence(strategy, crop_names)}")
    _block(console, text("result.why"), strategy.why_suggested)
    evidence_rows = []
    for item in strategy.evidence:
        val = item.get("value_range")
        if isinstance(val, (int, float)):
            val = f"{val:.1f}"
        evidence_rows.append(
            (
                item.get("indicator"),
                val,
                item.get("unit"),
                item.get("dataset"),
                item.get("period"),
                str(item.get("n_windows", "—")),
                item.get("status"),
            )
        )
    evidence_table = Table(
        "Indicator", "Value / band", "Unit", "Dataset", "Period", "Windows", "Status", box=None
    )
    for row in evidence_rows:
        evidence_table.add_row(*[str(value or "—") for value in row])
    console.print(f"\n[bold]{text('result.evidence')}[/bold]")
    console.print(evidence_table)
    _block(console, text("result.benefits"), strategy.benefits)
    _block(console, text("result.gaps"), strategy.information_gaps)
    _block(console, text("result.risks"), strategy.risks_for_local_review)

    indicators = Table(
        text("result.indicators"),
        "Definition",
        "Value (range)",
        "Unit",
        "Band",
        "Source",
        "Windows",
        box=None,
    )
    for item in strategy.indicators:
        val = _value(item.median, item.min, item.max)
        item.definition_key = item.definition_key or f"ind.{item.id}"
        indicators.add_row(
            item.label,
            text(item.definition_key),
            val,
            item.unit,
            _band(console, item.band),
            item.dataset or "—",
            str(item.n_windows or 0),
        )
    console.print("\n[bold]Indicators[/bold]")
    console.print(indicators)
    if strategy.sowing_sensitivity:
        console.print(
            f"[muted]{text('result.context.data_period')}: "
            f"{strategy.sowing_sensitivity[0].get('period') or '—'} · "
            f"{text('result.context.source')}: "
            f"{strategy.sowing_sensitivity[0].get('dataset', '—')}[/muted]"
        )
        sens_table = Table(
            "Crop",
            "Sowing window",
            "Indicator",
            "Unit",
            "Start",
            "Midpoint",
            "End",
            "Spread",
            "Windows (start/mid/end)",
            box=None,
        )
        for crop_sens in strategy.sowing_sensitivity:
            cid = crop_sens.get("crop_id", "")
            cname = crop_names.get(cid, cid.replace("_", " ").title())
            swin = crop_sens.get("sowing_window", "—")
            for ind_name, data in crop_sens.get("indicators", {}).items():
                sens_table.add_row(
                    cname,
                    swin,
                    ind_name.replace("_", " "),
                    crop_sens.get("units", {}).get(ind_name, "—"),
                    _value(data.get("start")),
                    _value(data.get("mid")),
                    _value(data.get("end")),
                    _value(data.get("spread")),
                    "/".join(
                        str(crop_sens.get("windows", {}).get(anchor, 0))
                        for anchor in ("start", "mid", "end")
                    ),
                )
        console.print("\n[bold]Sowing-date sensitivity[/bold]")
        console.print(sens_table)


def show_crops_used(result, console, ui) -> None:
    console.rule(f"[brand]{text('result.crops_used')}[/brand]", style="brand")
    table = Table("Crop", "Field", "Value", "Unit", "Status", "Source", box=None)
    for crop in result.crops_used:
        for field, obj in crop.get("fields", {}).items():
            value = obj.get("v")
            if isinstance(value, dict):
                value = ", ".join(f"{key}: {val}" for key, val in value.items())
            table.add_row(
                crop.get("name", crop["crop_id"]),
                field,
                str(value if value is not None else "unknown"),
                str(obj.get("unit") or "—"),
                ui.badge(obj.get("status", "missing")),
                str(obj.get("src") or "—"),
            )
    console.print(table)


def show_limits(result, console) -> None:
    console.rule(f"[brand]{text('result.limits')}[/brand]", style="brand")
    for i in range(1, 6):
        console.print(f"  • {text(f'result.methodology.{i}')}")
    console.print("\n[bold]Check locally[/bold]")
    for i in range(1, 4):
        console.print(f"  • {text(f'result.local_review.{i}')}")


def show_results(result, console, ui) -> None:
    crop_names = {crop["crop_id"]: crop.get("name", crop["crop_id"]) for crop in result.crops_used}
    console.rule(f"[brand]{text('result.title')}[/brand]", style="brand")
    console.print(text("result.disclaimer"))
    show_data_quality(result, console, ui)
    show_climate_summary(result, console)
    show_optional_context(result, console)
    show_comparison(result, console, crop_names)
    for strategy in result.strategies:
        show_strategy_detail(result, console, strategy, crop_names)
    show_crops_used(result, console, ui)
    show_limits(result, console)
    console.print(f"\n[ok]{text('result.check_locally')}[/ok]")
