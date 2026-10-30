"""analysis/et0.py — extraterrestrial radiation + Hargreaves-Samani ET0 (Part 7.2)."""
from __future__ import annotations

import math


def ra_mj(lat_deg: float, j: int) -> float:
    """Extraterrestrial radiation Ra in MJ m^-2 d^-1 (FAO-56 Eq. 21)."""
    phi = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * j / 365)
    delta = 0.409 * math.sin(2 * math.pi * j / 365 - 1.39)
    # omega_s
    tan_phi_tan_delta = math.tan(phi) * math.tan(delta)
    # clamp for arccos
    x = -tan_phi_tan_delta
    x = max(-1.0, min(1.0, x))
    omega_s = math.acos(x)
    ra = (24 * 60 / math.pi) * 0.0820 * dr * (
        omega_s * math.sin(phi) * math.sin(delta)
        + math.cos(phi) * math.cos(delta) * math.sin(omega_s)
    )
    return ra


def ra_mm(lat_deg: float, j: int) -> float:
    """Ra in mm d^-1 (0.408 * MJ)."""
    return 0.408 * ra_mj(lat_deg, j)


def et0_hs(tmax: float, tmin: float, lat_deg: float, j: int) -> float:
    """Hargreaves-Samani ET0 (FAO-56 Eq. 52). NaN if inputs missing or Tmax<Tmin."""
    import math as _m
    if tmax is None or tmin is None:
        return float("nan")
    if tmax < tmin:
        return float("nan")
    try:
        tmax = float(tmax)
        tmin = float(tmin)
    except (TypeError, ValueError):
        return float("nan")
    if _m.isnan(tmax) or _m.isnan(tmin):
        return float("nan")
    tmean = (tmax + tmin) / 2.0
    ra = ra_mm(lat_deg, j)
    return 0.0023 * (tmean + 17.8) * math.sqrt(tmax - tmin) * ra
