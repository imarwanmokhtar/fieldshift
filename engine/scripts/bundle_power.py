"""Download real NASA POWER daily data for the Nile Delta grid cells and save it in data/power/.

Offline helper (never imported by the engine at runtime). The engine uses these files only
when the live NASA POWER API cannot be reached: they are REAL NASA data for the same ~50 km
grid cell, not estimates.

NASA POWER meteorology comes from MERRA-2 on a 0.5 deg (lat) x 0.625 deg (lon) grid, so every
point inside one cell gets the same daily values. One request per cell centre covers every
pin in that cell. (Solar radiation is on a 1 deg grid; inside a cell it may differ slightly.)

Usage (from engine/):  .venv/bin/python scripts/bundle_power.py
Re-running skips cells that are already saved.
"""

from __future__ import annotations

import gzip
import json
import sys
import time
from datetime import date
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.data.power import PARAMS, URL  # noqa: E402
from app.settings import settings  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "data" / "power"
LATS = [30.0, 30.5, 31.0, 31.5]                     # Nile Delta, south to north
LNGS = [30.0, 30.625, 31.25, 31.875, 32.5]          # west to east


def cell_file(lat: float, lng: float) -> Path:
    return OUT / f"cell_{lat:.3f}_{lng:.3f}.json.gz"


def fetch(lat: float, lng: float) -> dict:
    params = {"parameters": PARAMS, "community": "AG", "latitude": lat, "longitude": lng,
              "start": settings.POWER_START, "end": settings.POWER_END, "format": "JSON"}
    for attempt in range(4):
        try:
            r = httpx.get(URL, params=params, timeout=180)
            r.raise_for_status()
            return {"meta": {"source": "NASA POWER daily point API", "url": URL, "community": "AG",
                             "parameters": PARAMS, "start": settings.POWER_START, "end": settings.POWER_END,
                             "cell_lat": lat, "cell_lng": lng, "grid": "MERRA-2 0.5 x 0.625 deg",
                             "retrieved": date.today().isoformat(), "missing_value": -999},
                    "parameter": r.json()["properties"]["parameter"]}
        except Exception as exc:                     # flaky network: wait and retry
            print(f"  attempt {attempt + 1} failed: {type(exc).__name__}", flush=True)
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"could not download cell {lat}, {lng}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for lat in LATS:
        for lng in LNGS:
            path = cell_file(lat, lng)
            if path.exists():
                print(f"skip {path.name}", flush=True)
                continue
            print(f"cell {lat}, {lng} ...", flush=True)
            data = fetch(lat, lng)
            path.write_bytes(gzip.compress(json.dumps(data, separators=(",", ":")).encode("utf-8")))
            print(f"  saved {path.name} ({path.stat().st_size // 1024} KB)", flush=True)


if __name__ == "__main__":
    main()
