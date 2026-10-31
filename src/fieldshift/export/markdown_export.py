"""Human-readable, provenance-aware Markdown report writer."""

from __future__ import annotations

from pathlib import Path

from ..i18n import text


def _cell(value) -> str:
    return str(value if value is not None else "—").replace("|", "\\|").replace("\n", " ")


def render_report(result, command: str = "fieldshift run") -> str:
    lines = [
        f"# {text('result.title')}",
        "",
        result.disclaimer,
        "",
        "## Inputs",
        "",
        "| Input | Value |",
        "|---|---|",
    ]
    for key, value in result.profile.items():
        if key.startswith("_"):
            continue
        lines.append(f"| {_cell(key)} | {_cell(value)} |")
    lines.extend(
        [
            "",
            "## Data sources",
            "",
            "| Source | Version | Retrieved | Period | Resolution | Type | Units | "
            "Missing values | Status | URL |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for source in result.data_sources:
        lines.append(
            "| "
            + " | ".join(
                _cell(source.get(k))
                for k in (
                    "name",
                    "version",
                    "retrieved",
                    "period",
                    "resolution",
                    "spatial_type",
                    "units",
                    "missing_value_rule",
                    "status",
                    "url",
                )
            )
            + " |"
        )
    lines.extend(["", "## Data quality", ""])
    if result.quality_flags:
        lines.extend(f"- {text(flag.text_key, flag=flag.code)}" for flag in result.quality_flags)
    else:
        lines.append("No active data-quality flags.")
    lines.extend(
        [
            "",
            "## Climate summary",
            "",
            "| Season | Mean T °C | Min T °C | Max T °C | Rain mm | Complete windows |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for season in ("winter", "summer"):
        d = result.climate_summary.get(season, {})
        lines.append(
            "| "
            + " | ".join(
                _cell(d.get(k))
                for k in (
                    "label",
                    "t_mean_c",
                    "t_min_c",
                    "t_max_c",
                    "rain_total_mm",
                    "n_complete_windows",
                )
            )
            + " |"
        )
    if result.optional_context:
        lines.extend(["", "## Optional satellite context", ""])
        lines.append(
            "These products are regional pixel context and are not used in strategy scores."
        )
        for key in ("smap", "modis"):
            panel = result.optional_context.get(key)
            if not panel:
                continue
            resolution = panel.get("spatial_resolution_km", panel.get("spatial_resolution_m"))
            lines.extend(
                [
                    "",
                    f"### {_cell(panel.get('dataset', key.upper()))}",
                    "",
                    f"- Status: {_cell(panel.get('status'))}",
                    f"- Period: {_cell(panel.get('period'))}",
                    f"- Spatial resolution: {_cell(resolution)} {'km' if key == 'smap' else 'm'}",
                    f"- Valid observations: {_cell(panel.get('valid_observations', 0))}; "
                    f"excluded: {_cell(panel.get('excluded_observations', 0))}",
                    f"- Quality flags: {_cell(panel.get('quality_flags'))}",
                    f"- Limit: {_cell(panel.get('caveat'))}",
                ]
            )
            if key == "smap":
                lines.extend(
                    [
                        "",
                        "| Month | Median soil moisture (m³/m³) | Observations |",
                        "|---|---:|---:|",
                    ]
                )
                for row in panel.get("monthly", []):
                    lines.append(
                        f"| {_cell(row.get('month'))} | {_cell(row.get('median'))} | "
                        f"{_cell(row.get('n_observations'))} |"
                    )
            else:
                lines.extend(
                    [
                        "",
                        "| Month | Median NDVI | Median EVI | Observations |",
                        "|---|---:|---:|---:|",
                    ]
                )
                for row in panel.get("monthly", []):
                    lines.append(
                        f"| {_cell(row.get('month'))} | {_cell(row.get('ndvi_median'))} | "
                        f"{_cell(row.get('evi_median'))} | {_cell(row.get('n_observations'))} |"
                    )
    lines.extend(
        [
            "",
            "## Crop reference rows used",
            "",
            "| Crop | Field | Value | Unit | Status | Source |",
            "|---|---|---|---|---|---|",
        ]
    )
    for crop in result.crops_used:
        for field, item in crop.get("fields", {}).items():
            lines.append(
                "| "
                + " | ".join(
                    _cell(v)
                    for v in (
                        crop.get("name", crop["crop_id"]),
                        field,
                        item.get("v"),
                        item.get("unit"),
                        item.get("status"),
                        item.get("src"),
                    )
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Strategy comparison",
            "",
            "| Strategy | Overall | Water demand | Confidence |",
            "|---|---|---|---|",
        ]
    )
    for strategy in result.strategies:
        bands = {i.id: i.band for i in strategy.indicators}
        lines.append(
            f"| {_cell(strategy.name)} | {_cell(strategy.overall.band)} | "
            f"{_cell(bands.get('water_demand_rel'))} | {_cell(strategy.confidence)} |"
        )
    if result.comparison.priority_sensitivity:
        lines.extend(
            [
                "",
                "### Priority sensitivity",
                "",
                f"- {result.comparison.priority_sensitivity.get('summary', '')}",
            ]
        )
    for strategy in result.strategies:
        lines.extend(
            [
                "",
                f"## {strategy.name}",
                "",
                "### Sequence",
                "",
                "; ".join(f"Y{s.year} {s.slot}: {s.crop_id}" for s in strategy.sequence),
                "",
                "### Why it was listed",
                "",
            ]
        )
        lines.extend(f"- {item}" for item in strategy.why_suggested)
        lines.extend(
            [
                "",
                "### Evidence",
                "",
                "| Indicator | Value | Unit | Dataset | Period | Windows | Status |",
                "|---|---|---|---|---|---:|---|",
            ]
        )
        for item in strategy.evidence:
            lines.append(
                "| "
                + " | ".join(
                    _cell(item.get(k))
                    for k in (
                        "indicator",
                        "value_range",
                        "unit",
                        "dataset",
                        "period",
                        "n_windows",
                        "status",
                    )
                )
                + " |"
            )
        for title, values in (
            ("Possible benefits", strategy.benefits),
            ("Information gaps", strategy.information_gaps),
            ("Risks needing local review", strategy.risks_for_local_review),
        ):
            lines.extend(["", f"### {title}", ""])
            lines.extend(f"- {value}" for value in values) if values else lines.append(
                "- None listed."
            )
        lines.extend(
            [
                "",
                "### Indicators",
                "",
                "| Indicator | Value / range | Unit | Band | Dataset | Windows |",
                "|---|---:|---|---|---|---:|",
            ]
        )
        for item in strategy.indicators:
            val = (
                "—"
                if item.median is None
                else (
                    f"{item.min:.1f}–{item.max:.1f}"
                    if item.min is not None and item.max is not None and item.min != item.max
                    else f"{item.median:.1f}"
                )
            )
            lines.append(
                "| "
                + " | ".join(
                    _cell(v)
                    for v in (item.label, val, item.unit, item.band, item.dataset, item.n_windows)
                )
                + " |"
            )
        if strategy.sowing_sensitivity:
            first = strategy.sowing_sensitivity[0]
            lines.extend(
                [
                    "",
                    f"- Dataset: {_cell(first.get('dataset'))}; "
                    f"period: {_cell(first.get('period'))}.",
                ]
            )
            header = (
                "| Crop | Sowing window | Indicator | Unit | Sowing start "
                "| Midpoint | Sowing end | Spread | Windows (start/mid/end) |"
            )
            lines.extend(
                [
                    "",
                    "### Sowing-date sensitivity",
                    "",
                    header,
                    "|---|---|---|---|---:|---:|---:|---:|---|",
                ]
            )
            for cs in strategy.sowing_sensitivity:
                cid = cs.get("crop_id", "")
                swin = cs.get("sowing_window", "—")
                for ind_name, data in cs.get("indicators", {}).items():
                    lines.append(
                        f"| {_cell(cid)} | {_cell(swin)} | {_cell(ind_name.replace('_', ' '))} | "
                        f"{_cell(cs.get('units', {}).get(ind_name))} | "
                        f"{_cell(data.get('start'))} | {_cell(data.get('mid'))} | "
                        f"{_cell(data.get('end'))} | {_cell(data.get('spread'))} | "
                        + "/".join(
                            str(cs.get("windows", {}).get(anchor, 0))
                            for anchor in ("start", "mid", "end")
                        )
                        + " |"
                    )
    lines.extend(["", "## Limits and methodology", ""])
    lines.extend(f"- {item}" for item in result.limitations)
    lines.extend(["", "## Check locally", ""])
    lines.extend(f"- {item}" for item in result.local_review)
    lines.extend(
        [
            "",
            text("result.check_locally"),
            "",
            "## Reproduction",
            "",
            f"- {text('result.report.version')}: {result.engine_version}",
            f"- {text('result.report.created')}: {result.created_at}",
            f"- {text('result.report.command')}: `{command}`",
            f"- {text('result.report.sha')}: {_cell(result.profile.get('raw_sha256'))}",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(result, path: Path | str, command: str = "fieldshift run") -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_report(result, command), encoding="utf-8")
    return target
