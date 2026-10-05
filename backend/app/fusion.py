"""Classical pixel-level SAR-optical fusion: IHS substitution, PCA, wavelet.

All three take the same aligned stack: `opt` (bands, H, W) reflectance with
blue/green/red first (NaN where cloud-masked) and `pan` (H, W), a single
SAR intensity channel in 0..1. Where optical is missing, the fused image falls
back to SAR - that is the all-weather behaviour.
"""
from __future__ import annotations

import numpy as np
import pywt
from skimage.metrics import structural_similarity

METHODS = ("ihs", "pca", "wavelet")


def sar_intensity(sar_db: np.ndarray) -> np.ndarray:
    """Collapse VV/VH (dB) into one 0..1 intensity channel."""
    vv = np.clip((sar_db[0] + 22) / 22, 0, 1)
    vh = np.clip((sar_db[1] + 28) / 22, 0, 1)
    return 0.5 * (vv + vh)


def _match(src: np.ndarray, ref: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Mean/std match `src` to `ref` using the valid pixels."""
    if valid.sum() < 16:
        return src
    s_mu, s_sd = np.nanmean(src[valid]), np.nanstd(src[valid]) + 1e-6
    return (src - s_mu) / s_sd * np.nanstd(ref[valid]) + np.nanmean(ref[valid])


def fill_gaps(opt: np.ndarray, pan: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Fill cloud gaps in optical with SAR intensity matched to each band."""
    gap = ~np.isfinite(opt).all(axis=0)
    ok = ~gap & np.isfinite(pan)
    pan = np.where(np.isfinite(pan), pan, np.nanmean(pan) if np.isfinite(pan).any() else 0.0)
    out = opt.copy()
    for k in range(opt.shape[0]):
        if ok.sum() >= 16:
            out[k][gap] = _match(pan, opt[k], ok)[gap]
        else:  # no clear optical at all: plausible grey reflectance from SAR
            out[k][gap] = 0.05 + 0.25 * pan[gap]
    return out, gap


def fuse_ihs(opt, pan):
    opt, gap = fill_gaps(opt, pan)
    intensity = opt.mean(axis=0)
    pan_m = _match(pan, intensity, ~gap)
    return opt + (pan_m - intensity)[None]


def fuse_pca(opt, pan):
    opt, gap = fill_gaps(opt, pan)
    c, h, w = opt.shape
    x = opt.reshape(c, -1).T
    mu = x.mean(axis=0)
    vals, vecs = np.linalg.eigh(np.cov((x - mu).T))
    vecs = vecs[:, np.argsort(vals)[::-1]]
    if vecs[:, 0].sum() < 0:
        vecs[:, 0] *= -1
    pcs = (x - mu) @ vecs
    pc1 = pcs[:, 0].reshape(h, w)
    pcs[:, 0] = _match(pan, pc1, ~gap).ravel()
    return (pcs @ vecs.T + mu).T.reshape(c, h, w)


def fuse_wavelet(opt, pan, wavelet: str = "db2", level: int = 2):
    """Low frequencies from optical; each detail coefficient from whichever source is stronger."""
    opt, gap = fill_gaps(opt, pan)
    h, w = pan.shape
    out = np.empty_like(opt)
    for k in range(opt.shape[0]):
        co = pywt.wavedec2(opt[k], wavelet, level=level, mode="symmetric")
        cp = pywt.wavedec2(_match(pan, opt[k], ~gap), wavelet, level=level, mode="symmetric")
        fused = [co[0]] + [
            tuple(np.where(np.abs(dp) > np.abs(do), dp, do) for do, dp in zip(lo, lp))
            for lo, lp in zip(co[1:], cp[1:])
        ]
        out[k] = pywt.waverec2(fused, wavelet, mode="symmetric")[:h, :w]
    return out


FUSERS = {"ihs": fuse_ihs, "pca": fuse_pca, "wavelet": fuse_wavelet}


def fuse(method: str, opt: np.ndarray, sar_db: np.ndarray) -> np.ndarray:
    return FUSERS[method](opt, sar_intensity(sar_db)).astype("float32")


# ---------------------------------------------------------------- quality metrics
def _entropy(img: np.ndarray) -> float:
    hist, _ = np.histogram(np.clip(img, 0, 1), bins=256, range=(0, 1))
    p = hist[hist > 0] / hist.sum()
    return float(-(p * np.log2(p)).sum())


def _mutual_info(a: np.ndarray, b: np.ndarray) -> float:
    h, _, _ = np.histogram2d(a.ravel(), b.ravel(), bins=64)
    p = h / h.sum()
    px, py = p.sum(axis=1, keepdims=True), p.sum(axis=0, keepdims=True)
    nz = p > 0
    return float((p[nz] * np.log2(p[nz] / (px @ py)[nz])).sum())


def _norm(x):
    lo, hi = np.nanpercentile(x, [1, 99])
    return np.clip((x - lo) / (hi - lo + 1e-6), 0, 1)


def quality(opt: np.ndarray, sar_db: np.ndarray, fused: np.ndarray) -> dict:
    """Image-quality scores of a fused image, measured on cloud-free pixels only."""
    clear = np.isfinite(opt).all(axis=0) & np.isfinite(sar_db).all(axis=0)
    if clear.sum() < 500:
        return {}
    o = np.where(clear[None], opt, 0.0)
    f = np.where(clear[None], fused, 0.0)
    ov, fv = o[:, clear], f[:, clear]
    cos = (ov * fv).sum(0) / (np.linalg.norm(ov, axis=0) * np.linalg.norm(fv, axis=0) + 1e-9)
    sam = float(np.degrees(np.arccos(np.clip(cos, -1, 1))).mean())
    rmse2 = ((ov - fv) ** 2).mean(axis=1)
    ergas = float(100 * np.sqrt((rmse2 / (ov.mean(axis=1) ** 2 + 1e-9)).mean()))
    oi, fi, pi = _norm(o.mean(0)), _norm(f.mean(0)), _norm(np.where(clear, sar_intensity(sar_db), 0.0))
    return {
        "sam_deg": round(sam, 2),
        "ergas": round(ergas, 2),
        "ssim_optical": round(float(structural_similarity(oi, fi, data_range=1.0)), 3),
        "ssim_sar": round(float(structural_similarity(pi, fi, data_range=1.0)), 3),
        "entropy": round(_entropy(fi), 2),
        "mi_optical": round(_mutual_info(oi[clear], fi[clear]), 3),
        "mi_sar": round(_mutual_info(pi[clear], fi[clear]), 3),
    }
