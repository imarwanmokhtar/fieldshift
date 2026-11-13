"""Sample precomputed rasters (GAEZ suitability, SMAP soil moisture, IMERG rainfall) at the pin.

Put small GeoTIFFs in engine/data/ with these names (see engine/README.md):
  gaez_<crop>.tif         e.g. gaez_wheat.tif   (suitability index, irrigated)
  smap_anomaly.tif        recent soil-moisture anomaly (m3/m3)
  imerg_trend.tif         rainfall trend (mm/year per year)

Until those files exist, each function returns None (layer "unavailable"), or
a clearly labelled mock value when USE_MOCK_LAYERS=true. GAEZ falls back to the
hand-entered approximations in crops.json, labelled as such.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..settings import settings

log = logging.getLogger(__name__)


def sample(path: Path, lat: float, lng: float) -> float | None:
    try:
        import rasterio  # imported lazily: optional dependency
    except ImportError:
        log.warning("rasterio not installed; cannot sample %s", path.name)
        return None
    with rasterio.open(path) as src:
        val = next(src.sample([(lng, lat)]))[0]
        if src.nodata is not None and val == src.nodata:
            return None
        return float(val)


def _sample_named(name: str, lat: float, lng: float) -> float | None:
    path = settings.DATA_DIR / name
    if not path.exists():
        return None
    try:
        return sample(path, lat, lng)
    except Exception as exc:
        log.warning("raster sample failed for %s: %s", name, exc)
        return None


def gaez_suitability(crop: str, lat: float, lng: float) -> float | None:
    """0-1 suitability from a GAEZ raster, or None if no raster for this crop."""
    v = _sample_named(f"gaez_{crop}.tif", lat, lng)
    if v is None:
        return None
    # GAEZ suitability index is 0-10000; normalise to 0-1.
    return max(0.0, min(1.0, v / 10000.0 if v > 1.0 else v))


def smap_anomaly(lat: float, lng: float) -> tuple[float | None, str]:
    v = _sample_named("smap_anomaly.tif", lat, lng)
    if v is not None:
        return v, "smap"
    return (-0.02, "mock") if settings.USE_MOCK_LAYERS else (None, "unavailable")


def imerg_trend(lat: float, lng: float) -> tuple[float | None, str]:
    v = _sample_named("imerg_trend.tif", lat, lng)
    if v is not None:
        return v, "imerg"
    return (-0.4, "mock") if settings.USE_MOCK_LAYERS else (None, "unavailable")
