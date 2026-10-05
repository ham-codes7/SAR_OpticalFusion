# Overcast — build plan

Status key: **done** = written and tested · **draft** = written, not yet tested end to end · **todo** = not started

## 1. Who uses it and why

| User | What they need | What the app gives them |
|---|---|---|
| Forest officer / conservation NGO | Know where forest was cleared, even in monsoon months | Forest-loss map, area in hectares, polygons to take into GIS |
| Town planner / urban researcher | See where a city is expanding | Urban-growth map between any two dates |
| Reviewer / faculty | Proof that fusion actually helps | Side-by-side scores for radar, optical and fused on the same area |

## 2. How the user moves through the app

1. **What** — choose Forest loss or Urban growth.
2. **Where** — pick a preset region, or draw an area on the map.
3. **When** — choose a "before" and an "after" date range.
4. **Analyse** — about 30–60 s for a new area; instant on repeat.
5. **Explore** — swipe before/after; switch Optical / Radar / Fused view; toggle detected change.
6. **Compare** — click Radar only / Optical only / Fused to see what each found, with precision, recall and F1.
7. **Stress test** — add synthetic cloud and re-run to see which inputs survive.
8. **Take away** — download change polygons; read the cloud calendar.

## 3. Architecture

```
Browser (React + Leaflet)
   │  POST /api/analyze {bbox, before, after, phenomenon, cloud}
   ▼
API (FastAPI) ─────────────► run cache (PNG layers + result.json)
   │
   ▼
Analysis pipeline
   1 ingest        Sentinel-1 RTC + Sentinel-2 L2A  (Planetary Computer, no account)
   2 preprocess    cloud mask · Lee speckle filter · temporal composite
   3 co-register   both sensors onto one shared grid
   4 fuse          IHS · PCA · wavelet · six-band stack
   5 detect        one trained model per input, same recipe for all
   6 evaluate      F1 vs reference land cover · image-quality metrics
   7 render        map layers, statistics, GeoJSON
```

Offline, run once: `train.py` downloads training regions, builds features, trains
the models and writes `models/model_card.json`.

## 4. How the models process data

- **Inputs compared:** radar only (2 bands) · optical only (4 bands) · fused IHS / PCA / wavelet (4 bands each) · band stack (6 bands).
- **Features per pixel:** before values, after values, difference, 5×5-smoothed difference. Identical recipe for every input.
- **Model:** gradient-boosted trees (scikit-learn). Same settings for every input. No deep learning.
- **Labels:** Impact Observatory 10 m annual land cover, 2017 → 2023. Forest loss = trees → crops / built / bare / rangeland. Urban growth = not built → built.
- **Training data:** six regions per phenomenon; a quarter of each region held out in blocks; each region used once clear and once with synthetic cloud.
- **Honesty rule:** app presets are never in the training set. Scores are shown whichever way they come out.

## 5. File layout

```
backend/app/data.py       ingest, cloud mask, speckle filter
backend/app/scenes.py     caching, synthetic cloud
backend/app/fusion.py     fusion methods, quality metrics
backend/app/detect.py     features, model, labels, scoring
backend/app/analysis.py   full run, map layers, exports
backend/app/regions.py    presets and training regions
backend/app/main.py       HTTP API
backend/train.py          model training
frontend/src/App.jsx      panels, controls, results
frontend/src/MapView.jsx  map, swipe, drawing
```

## 6. Chunks, in order

| # | Chunk | Status | Done when |
|---|---|---|---|
| 1 | Data ingestion and co-registration | done | One area and date range returns aligned optical + radar in about 20 s |
| 2 | Fusion methods and quality metrics | draft | Three fused images render and metrics compute on a preset |
| 3 | Training pipeline and models | running | Twelve models saved, held-out scores in the model card |
| 4 | Analysis API | draft | `/api/analyze` returns layers and scores for all four presets |
| 5 | Front end: map, swipe, controls, results | draft | Full flow works in the browser on a preset |
| 6 | Draw-your-own-area | draft | A hand-drawn rectangle analyses correctly |
| 7 | Accuracy pass | todo | Detection quality reviewed on presets; features or labels tuned if weak |
| 8 | Free-shape drawing (polygon) | todo | User draws any shape; results clipped to it |
| 9 | Timeline: more than two dates | todo | User scrubs through several dates and sees change accumulate |
| 10 | Report export and demo polish | todo | One-click PDF/PNG summary; presets pre-cached for the demo |
| 11 | Push to GitHub | todo | Repo has code, models, README; teammates can run it |

## 7. Known risks

- **Detection accuracy may be modest.** The reference land cover is itself noisy, and radar alone is weak on hill forest. An early run scored F1 of 0.13 (radar) and 0.36 (optical) on forest loss before a label-year fix; retraining is in progress.
- **Reference data is not fully independent.** Impact Observatory's map is derived from Sentinel-2. Global Forest Watch (Landsat-based) would be a stronger check for forest loss.
- **Imagery service can drop connections** under heavy use. Retries are in place; presets should be pre-cached before a demo.
- **Earth Engine is no longer needed.** The deck names it as the platform, so the review slides need updating.
