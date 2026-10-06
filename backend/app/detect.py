"""Change detector: one gradient-boosted-tree recipe, trained once per input variant.

The classifier, its hyper-parameters, the feature recipe and the
post-processing are identical for every variant. Only the band stack fed in
changes, so differences in score are attributable to the input.
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from scipy.ndimage import binary_opening, gaussian_filter, label, uniform_filter
from sklearn.ensemble import HistGradientBoostingClassifier

from . import fusion

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
PHENOMENA = ("deforestation", "urban")
VARIANTS = ("sar", "optical", "ihs", "pca", "wavelet", "stack")
VARIANT_LABELS = {
    "sar": "SAR only",
    "optical": "Optical only",
    "ihs": "Fused · IHS",
    "pca": "Fused · PCA",
    "wavelet": "Fused · Wavelet",
    "stack": "Fused · Band stack",
}
MODEL_PARAMS = dict(max_iter=150, learning_rate=0.08, max_leaf_nodes=31, min_samples_leaf=40, l2_regularization=1.0, class_weight="balanced", random_state=7)
GAP_FILL = -1.0
FOREST_YEARS = (2000, 2024)  # Hansen Global Forest Change v1.12
LANDCOVER_YEARS = (2017, 2023)  # Impact Observatory annual land cover


def _nd(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (a - b) / (a + b + 1e-6)


def optical_indices(opt: np.ndarray) -> np.ndarray:
    """NDVI (vegetation), NDBI (built-up), MNDWI (water), NBR (clearing / burn) from B2 B3 B4 B8 B11 B12."""
    _, g, r, nir, swir1, swir2 = opt[:6]
    return np.stack([_nd(nir, r), _nd(swir1, nir), _nd(g, swir1), _nd(nir, swir2)])


def sar_indices(sar_db: np.ndarray) -> np.ndarray:
    """VV - VH in dB: the cross-pol ratio, high for bare / built surfaces, low for vegetation volume."""
    return (sar_db[0] - sar_db[1])[None]


def variant_stack(variant: str, opt: np.ndarray, sar_db: np.ndarray) -> np.ndarray:
    """Band stack for one date, plus the standard indices of its bands. NaN means the variant cannot see that pixel."""
    if variant == "sar":
        return np.concatenate([sar_db, sar_indices(sar_db)])
    if variant == "stack":  # feature-level fusion: all bands side by side, optical gaps filled
        o = np.concatenate([opt, optical_indices(opt)])
        return np.concatenate([np.where(np.isfinite(o), o, GAP_FILL), sar_db, sar_indices(sar_db)])
    bands = opt if variant == "optical" else fusion.fuse(variant, opt, sar_db)
    return np.concatenate([bands, optical_indices(bands)])


def _local_std(x: np.ndarray, size: int = 5) -> np.ndarray:
    mean = uniform_filter(x, size)
    return np.sqrt(np.maximum(uniform_filter(x * x, size) - mean * mean, 0))


def features(before: np.ndarray, after: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-pixel features, the same recipe for any band stack.

    before, after, difference, the difference smoothed at two scales, and the
    local texture of each date.
    """
    valid = np.isfinite(before).all(axis=0) & np.isfinite(after).all(axis=0)
    b, a = np.nan_to_num(before), np.nan_to_num(after)
    d = a - b
    parts = [b, a, d]
    parts.append(np.stack([uniform_filter(x, 5) for x in d]))
    parts.append(np.stack([uniform_filter(x, 11) for x in d]))
    parts.append(np.stack([_local_std(x) for x in b]))
    parts.append(np.stack([_local_std(x) for x in a]))
    x = np.concatenate(parts).astype("float32")
    return x.reshape(x.shape[0], -1).T, valid.ravel()


def forest_reference(loss_year: np.ndarray, yb: int, ya: int) -> tuple[np.ndarray, np.ndarray]:
    """Forest loss recorded by Hansen Global Forest Change in the years after `yb` up to and including `ya`."""
    known = loss_year != 255
    change = (loss_year >= yb + 1 - 2000) & (loss_year <= ya - 2000) & known
    return change, known


def urban_reference(lc_before: np.ndarray, lc_after: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """New built-up area between two Impact Observatory annual land-cover maps (water excluded)."""
    known = (lc_before > 0) & (lc_after > 0) & (lc_before != 10) & (lc_after != 10)
    change = (lc_before != 7) & (lc_before != 1) & (lc_after == 7)
    return change & known, known


def new_model() -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(**MODEL_PARAMS)


_cache: dict[str, dict] = {}


def load_model(phenomenon: str, variant: str) -> dict:
    """Returns {"model": fitted classifier, "threshold": tuned cut-off}."""
    key = f"{phenomenon}_{variant}"
    if key not in _cache:
        _cache[key] = joblib.load(MODEL_DIR / f"{key}.joblib")
    return _cache[key]


def models_ready() -> bool:
    return all((MODEL_DIR / f"{p}_{v}.joblib").exists() for p in PHENOMENA for v in VARIANTS)


def to_mask(prob: np.ndarray, threshold: float) -> np.ndarray:
    """Smooth the probability map slightly, threshold it, drop specks."""
    return clean(gaussian_filter(np.nan_to_num(prob), 1.0) >= threshold)


def clean(mask: np.ndarray, min_px: int = 6) -> np.ndarray:
    mask = binary_opening(mask, structure=np.ones((2, 2), bool))
    lab, n = label(mask)
    if n:
        sizes = np.bincount(lab.ravel())
        mask = (sizes >= min_px)[lab] & (lab > 0)
    return mask


def predict(phenomenon: str, variant: str, before: np.ndarray, after: np.ndarray):
    """Returns (probability map with NaN where unseen, cleaned boolean change mask)."""
    h, w = before.shape[1:]
    x, valid = features(before, after)
    bundle = load_model(phenomenon, variant)
    prob = np.full(h * w, np.nan, "float32")
    if valid.any():
        prob[valid] = bundle["model"].predict_proba(x[valid])[:, 1]
    prob = prob.reshape(h, w)
    return prob, to_mask(prob, bundle["threshold"])


def reference_year(start: str, end: str) -> int:
    """Annual land-cover map that best describes a date window.

    A window centred early in a year (e.g. Dec-Feb) shows the land as it stood
    at the end of the previous year, so it is matched to that year's map.
    """
    from datetime import date, timedelta

    a, b = date.fromisoformat(start), date.fromisoformat(end)
    return (a + (b - a) / 2 - timedelta(days=90)).year


def score(mask: np.ndarray, ref: np.ndarray, known: np.ndarray) -> dict:
    tp = int((mask & ref & known).sum())
    fp = int((mask & ~ref & known).sum())
    fn = int((~mask & ref & known).sum())
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3)}
