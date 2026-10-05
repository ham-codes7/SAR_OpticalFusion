# Overcast — land-change monitoring that keeps working under cloud

Interactive web app that fuses Sentinel-1 radar with Sentinel-2 optical imagery to
detect **forest loss** and **urban growth**, and shows — side by side — what radar
alone, optical alone and the fused input each manage to find.

Innovative Design Project · guide: Prof. Velu M

## What you can do in the app

- Pick a preset region or **draw your own area** on the map.
- Choose a "before" and an "after" date range.
- Swipe between before and after in optical, radar or fused view.
- See detected change, its area in hectares, and precision / recall / F1 for each input.
- Run a **cloud stress test**: hide part of the optical image and watch which inputs still work.
- See the **cloud calendar**: clear optical days against radar days, month by month.
- Download the detected change as GeoJSON.

## How it works

| Step | What happens |
|---|---|
| Ingest | Sentinel-1 RTC (VV, VH) and Sentinel-2 L2A (B2, B3, B4, B8) from Microsoft Planetary Computer. No account needed. |
| Preprocess | Cloud masking from the Sentinel-2 scene classification; Lee speckle filter on radar; radar is already terrain-corrected. |
| Co-register | Both sensors resampled onto one shared grid. |
| Fuse | IHS substitution, PCA and wavelet fusion (pixel level), plus a six-band stack (feature level). |
| Detect | One gradient-boosted-tree recipe, trained once per input. Same features, settings and clean-up for every input. |
| Evaluate | Scored against Impact Observatory annual land cover (2017–2023), plus SAM / ERGAS / SSIM / entropy for the fused images. |

The models are trained on six regions per phenomenon. The preset regions in the app
are **not** in the training set.

## Run it

Backend (Python 3.11+):

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --port 8000
```

Frontend (Node 20+), in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173.

Trained models are committed in `backend/models/`. To retrain them:

```bash
cd backend
.venv/bin/python train.py
```

## Layout

```
backend/app/data.py       imagery download, cloud masking, speckle filter
backend/app/fusion.py     IHS, PCA, wavelet fusion + image-quality metrics
backend/app/detect.py     features, model, reference labels, scoring
backend/app/analysis.py   one full analysis run; map layers; exports
backend/app/main.py       HTTP API
backend/train.py          trains the models and writes models/model_card.json
frontend/src/             React app (App.jsx, MapView.jsx)
```
