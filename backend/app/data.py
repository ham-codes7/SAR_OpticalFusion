"""Sentinel-1 / Sentinel-2 ingestion from Microsoft Planetary Computer.

Everything is resampled onto one shared Web-Mercator grid (the co-registration
step), so the outputs drop straight onto a web map.
"""
from __future__ import annotations

import math
import threading
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import numpy as np
import planetary_computer
import rasterio
import requests
from pystac_client import Client
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from scipy.ndimage import uniform_filter

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
CROP_URL = "https://planetarycomputer.microsoft.com/api/data/v1/item/bbox"
HTTP = requests.Session()
CROP_SLOTS = threading.BoundedSemaphore(8)
S2_BANDS = ["B02", "B03", "B04", "B08", "B11", "B12"]  # blue, green, red, NIR, SWIR1, SWIR2
S2_BAD_SCL = [0, 1, 3, 8, 9, 10]  # nodata, saturated, shadow, cloud med/high, cirrus
R_EARTH = 6378137.0
POOL = ThreadPoolExecutor(max_workers=24)


@dataclass
class Grid:
    bbox: tuple[float, float, float, float]  # west, south, east, north (lon/lat)
    transform: rasterio.Affine
    width: int
    height: int
    pixel_m: float  # ground size of a pixel in metres
    crs: str = "EPSG:3857"

    @property
    def pixel_ha(self) -> float:
        return self.pixel_m**2 / 10_000


def _merc(lon: float, lat: float) -> tuple[float, float]:
    x = math.radians(lon) * R_EARTH
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * R_EARTH
    return x, y


def make_grid(bbox, max_px: int = 640) -> Grid:
    west, south, east, north = bbox
    x0, y0 = _merc(west, south)
    x1, y1 = _merc(east, north)
    scale = math.cos(math.radians((south + north) / 2))  # mercator stretch
    res = max(10.0 / scale, max(x1 - x0, y1 - y0) / max_px)
    width = max(8, round((x1 - x0) / res))
    height = max(8, round((y1 - y0) / res))
    return Grid(tuple(bbox), from_origin(x0, y1, res, res), width, height, res * scale)


def _client() -> Client:
    return Client.open(STAC_URL, modifier=planetary_computer.sign_inplace)


def _crop(item, assets: list[str], grid: Grid, resampling: str = "bilinear") -> np.ndarray:
    """Crop + reproject one scene onto the grid, server-side (one request per scene)."""
    w, s_, e, n = grid.bbox
    url = f"{CROP_URL}/{w},{s_},{e},{n}/{grid.width}x{grid.height}.tif"
    params = [("collection", item.collection_id), ("item", item.id), ("dst_crs", grid.crs), ("resampling", resampling)]
    params += [("assets", a) for a in assets]
    last = None
    for attempt in range(5):  # the crop service drops connections under load
        try:
            with CROP_SLOTS:
                r = HTTP.get(url, params=params, timeout=90)
            if r.status_code == 200:
                break
            last = RuntimeError(f"Imagery service returned {r.status_code} for {item.id}")
        except requests.RequestException as e:
            last = e
        time.sleep(1.5 * (attempt + 1))
    else:
        raise RuntimeError(f"Could not download imagery after several attempts: {last}")
    with MemoryFile(r.content) as mem, mem.open() as src:
        arr = src.read().astype("float32")
    bands, mask = arr[:-1], arr[-1]  # last band is the validity mask
    bands[:, mask == 0] = np.nan
    return bands


SEARCH_LOCK = threading.Lock()  # pystac's item parsing is not thread-safe


def _search(collection: str, grid: Grid, start: str, end: str, **kw):
    with SEARCH_LOCK:
        return _search_unlocked(collection, grid, start, end, **kw)


def _search_unlocked(collection: str, grid: Grid, start: str, end: str, **kw):
    return list(
        _client()
        .search(collections=[collection], bbox=grid.bbox, datetime=f"{start}/{end}", **kw)
        .items()
    )


def _covers(item, grid: Grid) -> float:
    """Fraction of the grid bbox covered by the item's bbox."""
    w, s, e, n = grid.bbox
    iw, is_, ie, in_ = item.bbox
    ox = max(0.0, min(e, ie) - max(w, iw))
    oy = max(0.0, min(n, in_) - max(s, is_))
    return (ox * oy) / ((e - w) * (n - s))


def load_optical(grid: Grid, start: str, end: str, max_scenes: int = 4) -> dict:
    """Cloud-masked median composite of Sentinel-2 L2A surface reflectance."""
    items = _search("sentinel-2-l2a", grid, start, end)
    scene_clouds = [float(i.properties.get("eo:cloud_cover", 100)) for i in items]
    ranked = sorted(items, key=lambda i: (-round(_covers(i, grid), 1), i.properties.get("eo:cloud_cover", 100)))
    chosen = ranked[:max_scenes]

    def one(item):
        offset = 1000.0 if float(item.properties.get("s2:processing_baseline", "0")) >= 4.0 else 0.0
        fut = POOL.submit(_crop, item, S2_BANDS, grid)
        scl = _crop(item, ["SCL"], grid, "nearest")[0]
        stack = fut.result()
        bad = np.isin(scl, S2_BAD_SCL) | ~np.isfinite(stack[0]) | (stack[0] == 0)
        stack = np.clip((stack - offset) / 10000.0, 0, 1)
        stack[:, bad] = np.nan
        return stack

    with ThreadPoolExecutor(max_workers=max_scenes) as ex:
        stacks = list(ex.map(one, chosen))
    if stacks:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            comp = np.nanmedian(np.stack(stacks), axis=0)
    else:
        comp = np.full((len(S2_BANDS), grid.height, grid.width), np.nan, "float32")
    return {
        "data": comp.astype("float32"),
        "bands": S2_BANDS,
        "scenes_found": len(items),
        "scenes_used": [i.id for i in chosen],
        "dates_used": sorted(i.datetime.date().isoformat() for i in chosen),
        "scene_cloud_pct": scene_clouds,
        "valid_fraction": float(np.isfinite(comp[0]).mean()),
    }


def lee_filter(img: np.ndarray, size: int = 5) -> np.ndarray:
    """Lee adaptive speckle filter on linear-power backscatter."""
    valid = np.isfinite(img)
    x = np.where(valid, img, 0.0)
    w = uniform_filter(valid.astype("float32"), size) + 1e-6
    mean = uniform_filter(x, size) / w
    var = np.maximum(uniform_filter(x * x, size) / w - mean**2, 0)
    noise = np.nanmean(var[valid]) if valid.any() else 0.0
    k = var / (var + noise + 1e-12)
    out = mean + k * (x - mean)
    out[~valid] = np.nan
    return out


def load_sar(grid: Grid, start: str, end: str, max_scenes: int = 6) -> dict:
    """Speckle-filtered temporal-mean Sentinel-1 RTC backscatter, in dB (VV, VH)."""
    items = _search("sentinel-1-rtc", grid, start, end)
    usable = [i for i in items if "vv" in i.assets and "vh" in i.assets]
    chosen = sorted(usable, key=lambda i: -_covers(i, grid))[:max_scenes]

    def one(item):
        st = _crop(item, ["vv", "vh"], grid)
        st[~np.isfinite(st) | (st <= 0)] = np.nan
        return st

    with ThreadPoolExecutor(max_workers=max_scenes) as ex:
        stacks = list(ex.map(one, chosen))
    if stacks:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lin = np.nanmean(np.stack(stacks), axis=0)
        lin = np.stack([lee_filter(b) for b in lin])
        db = 10 * np.log10(np.maximum(lin, 1e-6))
        db[~np.isfinite(lin)] = np.nan
    else:
        db = np.full((2, grid.height, grid.width), np.nan, "float32")
    return {
        "data": db.astype("float32"),
        "bands": ["VV", "VH"],
        "scenes_found": len(items),
        "scenes_used": [i.id for i in chosen],
        "dates_used": sorted(i.datetime.date().isoformat() for i in chosen),
        "valid_fraction": float(np.isfinite(db[0]).mean()),
    }


LULC_CLASSES = {1: "water", 2: "trees", 4: "flooded vegetation", 5: "crops", 7: "built", 8: "bare", 9: "snow", 10: "clouds", 11: "rangeland"}


def load_landcover(grid: Grid, year: int) -> np.ndarray | None:
    """Impact Observatory 10 m annual land cover (2017-2023) - reference labels."""
    items = _search("io-lulc-annual-v02", grid, f"{year}-01-01", f"{year}-12-31")
    if not items:
        return None
    out = np.zeros((grid.height, grid.width), "float32")
    for it in items:
        tile = np.nan_to_num(_crop(it, ["data"], grid, "nearest")[0])
        out = np.where(out == 0, tile, out)
    return out.astype("uint8")
