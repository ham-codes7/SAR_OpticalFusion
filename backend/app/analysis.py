"""End-to-end analysis for one area and two date windows."""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image

from . import data, detect, fusion, scenes

RUNS = scenes.CACHE / "runs"
RUNS.mkdir(parents=True, exist_ok=True)
COLORS = {"sar": (255, 138, 61), "optical": (45, 212, 191), "ihs": (255, 225, 77), "pca": (255, 225, 77),
          "wavelet": (255, 225, 77), "stack": (255, 225, 77), "reference": (255, 77, 141)}
ERROR_COLORS = {"correct": (74, 222, 128, 255), "false_alarm": (248, 81, 73, 255), "missed": (77, 166, 255, 255)}
MAX_SPAN_DEG = 0.3
REFERENCE_SOURCE = {"deforestation": "Hansen Global Forest Change (Landsat, 30 m)",
                    "urban": "Impact Observatory 10 m annual land cover"}


# ------------------------------------------------------------------ rendering
def _save(rgba: np.ndarray, path, inside: np.ndarray | None = None) -> None:
    if inside is not None:
        rgba = rgba.copy()
        rgba[~inside, 3] = 0
    Image.fromarray(rgba, "RGBA").save(path, optimize=True)


def _inside(polygon, grid) -> np.ndarray:
    """Pixels of the grid that fall inside a lon/lat polygon ring."""
    from rasterio.features import geometry_mask
    from rasterio.warp import transform_geom

    ring = [list(p) for p in polygon]
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    geom = transform_geom("EPSG:4326", grid.crs, {"type": "Polygon", "coordinates": [ring]})
    return geometry_mask([geom], out_shape=(grid.height, grid.width), transform=grid.transform, invert=True)


def _rgb(stack: np.ndarray, gap: np.ndarray | None = None) -> np.ndarray:
    """True-colour render from a blue/green/red/NIR stack; cloud gaps drawn as haze."""
    rgb = np.stack([stack[2], stack[1], stack[0]], axis=-1)
    missing = ~np.isfinite(rgb).all(axis=-1)
    img = np.clip(np.nan_to_num(rgb) / 0.28, 0, 1) ** (1 / 1.6)
    out = np.dstack([img * 255, np.full(img.shape[:2], 255.0)])
    haze = missing if gap is None else (missing | gap)
    out[haze] = (236, 238, 240, 235)
    return out.astype("uint8")


def _sar(sar_db: np.ndarray) -> np.ndarray:
    vv, vh = sar_db
    r = np.clip((vv + 20) / 20, 0, 1)
    g = np.clip((vh + 27) / 20, 0, 1)
    b = np.clip((vv - vh) / 14, 0, 1)
    img = np.nan_to_num(np.dstack([r, g, b])) ** (1 / 1.3)
    alpha = np.where(np.isfinite(vv), 255, 0)
    return np.dstack([img * 255, alpha]).astype("uint8")


def _mask(mask: np.ndarray, color) -> np.ndarray:
    out = np.zeros((*mask.shape, 4), "uint8")
    out[mask] = (*color, 255)
    return out


def _errors(mask: np.ndarray, ref: np.ndarray, known: np.ndarray) -> np.ndarray:
    """Detection checked against the reference: correct (green), false alarm (red), missed (blue)."""
    out = np.zeros((*mask.shape, 4), "uint8")
    out[mask & ref & known] = ERROR_COLORS["correct"]
    out[mask & ~ref & known] = ERROR_COLORS["false_alarm"]
    out[~mask & ref & known] = ERROR_COLORS["missed"]
    return out


def _blind(blind: np.ndarray) -> np.ndarray:
    out = np.zeros((*blind.shape, 4), "uint8")
    out[blind] = (236, 238, 240, 150)
    return out


# ------------------------------------------------------------------ analysis
def validate(bbox) -> None:
    w, s, e, n = bbox
    if not (-180 <= w < e <= 180 and -85 <= s < n <= 85):
        raise ValueError("Invalid bounding box.")
    if e - w > MAX_SPAN_DEG or n - s > MAX_SPAN_DEG:
        raise ValueError(f"Area too large - keep each side under about {MAX_SPAN_DEG * 111:.0f} km.")
    if e - w < 0.01 or n - s < 0.01:
        raise ValueError("Area too small - draw at least about 1 km on each side.")


def run(bbox, before, after, phenomenon: str, cloud: float = 0.0, polygon=None) -> dict:
    """Analyse one area. `polygon` (lon/lat ring) clips everything to a drawn shape."""
    if polygon:
        if not 3 <= len(polygon) <= 200:
            raise ValueError("A drawn shape needs between 3 and 200 corners.")
        lons, lats = [p[0] for p in polygon], [p[1] for p in polygon]
        bbox = (min(lons), min(lats), max(lons), max(lats))
    validate(bbox)
    if phenomenon not in detect.PHENOMENA:
        raise ValueError("Unknown phenomenon.")
    cloud = float(np.clip(cloud, 0, 0.95))
    run_id = scenes._key([round(b, 5) for b in bbox], list(before), list(after), phenomenon, round(cloud, 2), polygon, "v7")
    out = RUNS / run_id
    if (out / "result.json").exists():
        return json.loads((out / "result.json").read_text())
    out.mkdir(exist_ok=True)

    yb, ya = detect.reference_year(*before), detect.reference_year(*after)
    with ThreadPoolExecutor(3) as ex:
        fb = ex.submit(scenes.load_scene, bbox, *before)
        fa = ex.submit(scenes.load_scene, bbox, *after)
        fr = ex.submit(scenes.load_reference, bbox, phenomenon, yb, ya)
        b, a, reference = fb.result(), fa.result(), fr.result()
    grid = a["grid"]
    if not np.isfinite(a["sar"]).any() or not np.isfinite(b["sar"]).any():
        raise ValueError("No Sentinel-1 radar coverage for this area in one of the date ranges. Try different dates.")

    opt_b, opt_a = b["opt"], a["opt"]
    sim = scenes.simulate_cloud(opt_a.shape[1:], cloud, seed=3)
    opt_a = scenes.apply_cloud(opt_a, sim)
    gap_b, gap_a = ~np.isfinite(opt_b).all(0), ~np.isfinite(opt_a).all(0)
    inside = _inside(polygon, grid) if polygon else np.ones(gap_a.shape, bool)
    if inside.sum() < 100:
        raise ValueError("That shape is too small to analyse - draw a larger one.")
    n_inside = int(inside.sum())

    # imagery layers
    layers = {"before": {}, "after": {}, "change": {}}
    for when, opt, sar, gap in (("before", opt_b, b["sar"], gap_b), ("after", opt_a, a["sar"], gap_a)):
        _save(_rgb(opt), out / f"{when}_optical.png", inside)
        _save(_sar(sar), out / f"{when}_sar.png", inside)
        layers[when] |= {"optical": f"{when}_optical.png", "sar": f"{when}_sar.png"}

    stacks, quality = {}, {}
    for v in detect.VARIANTS:
        stacks[v] = (detect.variant_stack(v, opt_b, b["sar"]), detect.variant_stack(v, opt_a, a["sar"]))
    for m in fusion.METHODS:
        for when, st in zip(("before", "after"), stacks[m]):
            _save(_rgb(st), out / f"{when}_{m}.png", inside)
            layers[when][m] = f"{when}_{m}.png"
        quality[m] = fusion.quality(np.where(inside[None], opt_a, np.nan), a["sar"], stacks[m][1][:len(data.S2_BANDS)])  # fused bands, not the indices

    # change detection: same detector, six inputs
    ref = known = None
    if reference is not None:
        ref, known = reference
        ref, known = ref & inside, known & inside
        _save(_mask(ref, COLORS["reference"]), out / "change_reference.png")
        layers["change"]["reference"] = "change_reference.png"

    card = json.loads((detect.MODEL_DIR / "model_card.json").read_text())["phenomena"][phenomenon]["variants"]
    variants, masks = {}, {}
    for v in detect.VARIANTS:
        prob, mask = detect.predict(phenomenon, v, *stacks[v])
        mask = mask & inside
        masks[v] = mask
        _save(_mask(mask, COLORS[v]), out / f"change_{v}.png")
        layers["change"][v] = f"change_{v}.png"
        if ref is not None:
            _save(_errors(mask, ref, known), out / f"errors_{v}.png")
            layers["change"][f"errors_{v}"] = f"errors_{v}.png"
        blind = float(np.isnan(prob)[inside].mean())
        variants[v] = {
            "label": detect.VARIANT_LABELS[v],
            "area_ha": round(float(mask.sum()) * grid.pixel_ha, 1),
            "share_pct": round(100 * float(mask.sum()) / n_inside, 2),
            "blind_pct": round(100 * blind, 1),
            "scores": detect.score(mask, ref, known) if ref is not None else None,
            "holdout": {k: card[v][k] for k in ("clear", "cloudy")},
        }
    if gap_a.any() or gap_b.any():
        _save(_blind((gap_a | gap_b) & inside), out / "optical_blind.png")
        layers["change"]["optical_blind"] = "optical_blind.png"
    np.savez_compressed(out / "masks.npz", **masks)

    fused = [v for v in detect.VARIANTS if v not in ("sar", "optical")]
    key = (lambda v: variants[v]["scores"]["f1"]) if ref is not None else (lambda v: card[v]["clear"]["f1"] + card[v]["cloudy"]["f1"])
    best = max(fused, key=key)
    w, s, e, n = bbox
    result = {
        "id": run_id,
        "phenomenon": phenomenon,
        "bbox": list(bbox),
        "polygon": polygon,
        "bounds": [[s, w], [n, e]],
        "before": b["meta"],
        "after": a["meta"],
        "grid": {"width": grid.width, "height": grid.height, "pixel_m": round(grid.pixel_m, 1),
                 "area_ha": round(n_inside * grid.pixel_ha)},
        "cloud": {"simulated_pct": round(100 * cloud), "before_gap_pct": round(100 * float(gap_b[inside].mean()), 1),
                  "after_gap_pct": round(100 * float(gap_a[inside].mean()), 1)},
        "layers": {k: {name: f"/api/runs/{run_id}/{f}" for name, f in v.items()} for k, v in layers.items()},
        "variants": variants,
        "best_fused": best,
        "quality": quality,
        "reference": {"available": ref is not None, "years": [yb, ya] if ref is not None else None,
                      "area_ha": round(float(ref.sum()) * grid.pixel_ha, 1) if ref is not None else None,
                      "source": REFERENCE_SOURCE[phenomenon]},
    }
    (out / "result.json").write_text(json.dumps(result))
    return result


def change_geojson(run_id: str, variant: str) -> dict:
    """Detected change as polygons (lon/lat), for download into GIS tools."""
    from rasterio.features import shapes
    from rasterio.warp import transform_geom

    res = json.loads((RUNS / run_id / "result.json").read_text())
    mask = np.load(RUNS / run_id / "masks.npz")[variant]
    grid = data.make_grid(res["bbox"])
    feats = []
    for geom, val in shapes(mask.astype("uint8"), mask=mask, transform=grid.transform):
        g = transform_geom(grid.crs, "EPSG:4326", geom, precision=6)
        feats.append({"type": "Feature", "geometry": g, "properties": {"variant": variant, "phenomenon": res["phenomenon"]}})
    return {"type": "FeatureCollection", "features": feats}


def availability(bbox, year: int) -> dict:
    """Per-month count of usable optical vs radar acquisitions - the cloud calendar."""
    validate(bbox)
    grid = data.make_grid(bbox)
    with ThreadPoolExecutor(2) as ex:
        f2 = ex.submit(data._search, "sentinel-2-l2a", grid, f"{year}-01-01", f"{year}-12-31")
        f1 = ex.submit(data._search, "sentinel-1-rtc", grid, f"{year}-01-01", f"{year}-12-31")
        s2, s1 = f2.result(), f1.result()
    best: dict[str, float] = {}
    for it in s2:  # one entry per acquisition day, keeping the clearest tile
        d = it.datetime.date().isoformat()
        best[d] = min(best.get(d, 100.0), float(it.properties.get("eo:cloud_cover", 100)))
    months = []
    for m in range(1, 13):
        days = [c for d, c in best.items() if int(d[5:7]) == m]
        months.append({
            "month": m,
            "optical_total": len(days),
            "optical_clear": sum(c < 20 for c in days),
            "optical_partial": sum(20 <= c < 60 for c in days),
            "sar": len({it.datetime.date() for it in s1 if it.datetime.month == m}),
        })
    return {"year": year, "months": months}


def report_html(run_id: str, variant: str) -> str:
    """Self-contained one-page summary of a run (open in a browser, print to PDF)."""
    import base64
    import io

    out = RUNS / run_id
    res = json.loads((out / "result.json").read_text())
    v = res["variants"][variant]
    noun = "forest loss" if res["phenomenon"] == "deforestation" else "new built-up area"

    def b64(img: Image.Image) -> str:
        buf = io.BytesIO()
        bg = Image.new("RGBA", img.size, (20, 24, 31, 255))
        Image.alpha_composite(bg, img).convert("RGB").save(buf, "JPEG", quality=88)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

    before = Image.open(out / "before_optical.png").convert("RGBA")
    after = Image.open(out / "after_optical.png").convert("RGBA")
    change = Image.alpha_composite(after, Image.open(out / f"change_{variant}.png").convert("RGBA"))
    rows = ""
    for key in ("sar", "optical", variant):
        d = res["variants"][key]
        sc = d["scores"]
        cells = f"<td>{sc['precision']:.2f}</td><td>{sc['recall']:.2f}</td><td><b>{sc['f1']:.2f}</b></td>" if sc else "<td colspan=3>no reference for these dates</td>"
        rows += f"<tr><td>{d['label']}</td><td>{d['area_ha']:,.1f} ha</td>{cells}<td>{d['blind_pct']}%</td></tr>"
    w, s, e, n = res["bbox"]
    ref = res["reference"]
    ref_line = (f"Scored against {ref['source']} ({ref['years'][0]} to {ref['years'][1]}), which records {ref['area_ha']:,.1f} ha of {noun}."
                if ref["available"] else "No reference land cover is available for these dates, so no accuracy scores are shown.")
    cloud = res["cloud"]
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Change report</title><style>
body{{font:14px/1.5 -apple-system,Segoe UI,sans-serif;color:#1c1f24;max-width:900px;margin:32px auto;padding:0 24px}}
h1{{font:400 30px Georgia,serif;margin:0}} .sub{{color:#666;margin:4px 0 20px}} .big{{font:400 44px Georgia,serif}}
.imgs{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:18px 0}} .imgs img{{width:100%;border-radius:6px}}
.imgs span{{font-size:12px;color:#666}} table{{border-collapse:collapse;width:100%;margin:10px 0}}
td,th{{border-bottom:1px solid #ddd;padding:6px 8px;text-align:left;font-size:13px}} th{{color:#666;font-weight:500}}
.foot{{color:#777;font-size:12px;margin-top:20px}} @media print{{body{{margin:0 auto}}}}
</style></head><body>
<h1>{noun.capitalize()} report</h1>
<p class="sub">Area {w:.4f}, {s:.4f} to {e:.4f}, {n:.4f} &middot; {res['grid']['area_ha']:,} ha &middot; {res['grid']['pixel_m']} m per pixel<br>
Before: {res['before']['window'][0]} to {res['before']['window'][1]} &middot; After: {res['after']['window'][0]} to {res['after']['window'][1]}</p>
<div class="big">{v['area_ha']:,.1f} ha</div>
<p>of {noun} detected using <b>{v['label']}</b> &mdash; {v['share_pct']}% of the area analysed.</p>
<div class="imgs">
<div><img src="{b64(before)}"><span>Before (optical)</span></div>
<div><img src="{b64(after)}"><span>After (optical)</span></div>
<div><img src="{b64(change)}"><span>Detected change</span></div></div>
<table><tr><th>Input</th><th>Detected</th><th>Precision</th><th>Recall</th><th>F1</th><th>Blind area</th></tr>{rows}</table>
<p>{ref_line}</p>
<p>Optical cloud gaps: {cloud['before_gap_pct']}% before, {cloud['after_gap_pct']}% after{f" (includes {cloud['simulated_pct']}% synthetic cloud)" if cloud['simulated_pct'] else ""}.
Imagery: {len(res['after']['optical']['dates_used'])} Sentinel-2 and {len(res['after']['sar']['dates_used'])} Sentinel-1 scenes in the after window.</p>
<p class="foot">Sentinel-1 and Sentinel-2 data: Copernicus, via Microsoft Planetary Computer. Automated detection; verify on the ground before acting on it.</p>
</body></html>"""
