"""Cached loading of co-registered scene pairs and reference land cover."""
from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from . import data

CACHE = Path(__file__).resolve().parent.parent / "cache"
RAW = CACHE / "raw"
RAW.mkdir(parents=True, exist_ok=True)


def _key(*parts) -> str:
    return hashlib.sha1(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:16]


def load_scene(bbox, start: str, end: str, max_px: int = 640) -> dict:
    """Optical + SAR composites for one date window, on the shared grid."""
    grid = data.make_grid(bbox, max_px)
    path = RAW / f"scene_{_key([round(b, 5) for b in bbox], start, end, max_px, data.S2_BANDS)}.npz"
    if path.exists():
        z = np.load(path, allow_pickle=False)
        return {"grid": grid, "opt": z["opt"], "sar": z["sar"], "meta": json.loads(str(z["meta"]))}
    with ThreadPoolExecutor(2) as ex:
        fo = ex.submit(data.load_optical, grid, start, end)
        fs = ex.submit(data.load_sar, grid, start, end)
        o, s = fo.result(), fs.result()
    meta = {
        "window": [start, end],
        "optical": {k: o[k] for k in ("scenes_found", "dates_used", "scene_cloud_pct", "valid_fraction")},
        "sar": {k: s[k] for k in ("scenes_found", "dates_used", "valid_fraction")},
    }
    np.savez_compressed(path, opt=o["data"], sar=s["data"], meta=json.dumps(meta))
    return {"grid": grid, "opt": o["data"], "sar": s["data"], "meta": meta}


def load_landcover(bbox, year: int, max_px: int = 640):
    grid = data.make_grid(bbox, max_px)
    path = RAW / f"lulc_{_key([round(b, 5) for b in bbox], year, max_px)}.npy"
    if path.exists():
        return np.load(path)
    lc = data.load_landcover(grid, year)
    if lc is not None:
        np.save(path, lc)
    return lc


def simulate_cloud(shape, fraction: float, seed: int = 0) -> np.ndarray:
    """Blobby synthetic cloud mask covering roughly `fraction` of the image."""
    if fraction <= 0:
        return np.zeros(shape, bool)
    rng = np.random.default_rng(seed)
    noise = gaussian_filter(rng.standard_normal(shape), sigma=max(shape) / 14)
    return noise > np.quantile(noise, 1 - min(fraction, 0.98))


def apply_cloud(opt: np.ndarray, cloud: np.ndarray) -> np.ndarray:
    out = opt.copy()
    out[:, cloud] = np.nan
    return out
