"""analysis/seasons.py — slots, crop windows, cross-year handling (Part 7.1)."""

from __future__ import annotations

from datetime import date, timedelta

SLOTS = {
    "winter": [11, 12, 1, 2, 3, 4],
    "summer": [5, 6, 7, 8, 9, 10],
}

MISSING_COLS = ["t_mean_c", "t_max_c", "t_min_c", "rain_mm", "solar_mj_m2"]


def _to_doy(month: int, day: int, year: int) -> int:
    return (date(year, month, day) - date(year, 1, 1)).days + 1


def sowing_midpoint(window: dict, year: int) -> date:
    """Midpoint date of a sowing window (MM-DD) within `year`."""
    s = window["start"].split("-")
    e = window["end"].split("-")
    sm, sd = int(s[0]), int(s[1])
    em, ed = int(e[0]), int(e[1])
    start = date(year, sm, sd)
    end_year = year + (1 if (em, ed) < (sm, sd) else 0)
    end = date(end_year, em, ed)
    return start + timedelta(days=(end - start).days // 2)


def crop_window_dates(crop: dict, year: int, anchor: str = "mid") -> tuple[date, date] | None:
    """Return (start, end) dates for a crop sown in `year`, or None if no window.

    anchor: 'mid' (midpoint, default), 'start' (sowing window start), or 'end' (sowing window end).
    """
    win = (crop.get("sowing_window") or {}).get("v")
    if not win:
        return None
    dur = (crop.get("growth_duration_days") or {}).get("v")
    if not dur:
        return None
    if anchor == "start":
        s = win["start"].split("-")
        start = date(year, int(s[0]), int(s[1]))
    elif anchor == "end":
        s = win["start"].split("-")
        e = win["end"].split("-")
        sm, sd = int(s[0]), int(s[1])
        em, ed = int(e[0]), int(e[1])
        end_year = year + (1 if (em, ed) < (sm, sd) else 0)
        start = date(end_year, em, ed)
    else:
        start = sowing_midpoint(win, year)
    end = start + timedelta(days=int(dur) - 1)
    return start, end


def window_fully_inside(start: date, end: date, climate_start: date, climate_end: date) -> bool:
    return start >= climate_start and end <= climate_end


def window_has_no_missing(daily_df, start: date, end: date) -> bool:
    """True if every day in [start,end] exists in df and has no NaN in the 5 columns."""
    df = daily_df
    dcol = "date"
    if any(col not in df.columns for col in MISSING_COLS):
        return False
    parsed_dates = df[dcol].astype(str)
    sub = df[(parsed_dates >= str(start)) & (parsed_dates <= str(end))]
    if len(sub) != (end - start).days + 1:
        return False
    return all(not sub[col].isna().any() for col in MISSING_COLS)


def windows_for_crop(
    crop: dict, years: list[int], daily_df, climate_start: date, climate_end: date
) -> list[dict]:
    """Return list of valid windows: [{start, end, year}]. Drops invalid ones."""
    out = []
    if crop.get("crop_id") == "fallow":
        return out
    for y in years:
        wd = crop_window_dates(crop, y)
        if wd is None:
            continue
        start, end = wd
        if not window_fully_inside(start, end, climate_start, climate_end):
            continue
        if not window_has_no_missing(daily_df, start, end):
            continue
        out.append({"start": start, "end": end, "year": y})
    return out


def n_windows(windows: list) -> int:
    return len(windows)


def overlap_days(a_start: date, a_end: date, b_start: date, b_end: date) -> int:
    lo = max(a_start, b_start)
    hi = min(a_end, b_end)
    if hi < lo:
        return 0
    return (hi - lo).days + 1


def first_slot_after(previous_season: str | None) -> str:
    if previous_season == "summer":
        return "winter"
    return "winter" if previous_season in (None, "unknown") else "summer"


def build_existing_sequence(
    previous_crop: str, previous_season: str | None, other_slot_crop: str, horizon: int
) -> list[dict]:
    """Existing rotation = one-year cycle repeated over horizon."""
    previous_slot = previous_season if previous_season in ("winter", "summer") else "summer"
    other_slot = "summer" if previous_slot == "winter" else "winter"
    slot_crop = {previous_slot: previous_crop, other_slot: other_slot_crop}
    seq = []
    for y in range(1, horizon + 1):
        for slot in ("winter", "summer"):
            seq.append({"slot": slot, "year": y, "crop_id": slot_crop[slot]})
    return seq
