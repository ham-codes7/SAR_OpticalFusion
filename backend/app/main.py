"""HTTP API for the SAR-optical fusion change-detection app."""
from __future__ import annotations

import json
import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from . import analysis, detect, regions

app = FastAPI(title="SAR-Optical Fusion API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class AnalyzeRequest(BaseModel):
    bbox: list[float] = Field(min_length=4, max_length=4)
    before: list[str] = Field(min_length=2, max_length=2)
    after: list[str] = Field(min_length=2, max_length=2)
    phenomenon: str
    cloud: float = 0.0
    polygon: list[list[float]] | None = None


@app.get("/api/config")
def config():
    card = json.loads((detect.MODEL_DIR / "model_card.json").read_text()) if detect.models_ready() else None
    return {
        "presets": regions.PRESETS,
        "defaults": {"before": regions.BEFORE, "after": regions.AFTER},
        "variants": detect.VARIANT_LABELS,
        "models_ready": detect.models_ready(),
        "model_card": card,
        "max_span_deg": analysis.MAX_SPAN_DEG,
    }


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    if not detect.models_ready():
        raise HTTPException(503, "Models are not trained yet - run `python train.py` in backend/.")
    try:
        return analysis.run(tuple(req.bbox), tuple(req.before), tuple(req.after), req.phenomenon, req.cloud, req.polygon)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:  # imagery service unavailable
        raise HTTPException(502, str(e))


@app.get("/api/availability")
def availability(west: float, south: float, east: float, north: float, year: int):
    try:
        return analysis.availability((west, south, east, north), year)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/runs/{run_id}/change.geojson")
def geojson(run_id: str, variant: str = "stack"):
    if not re.fullmatch(r"[0-9a-f]{16}", run_id) or variant not in detect.VARIANTS:
        raise HTTPException(404)
    if not (analysis.RUNS / run_id / "masks.npz").exists():
        raise HTTPException(404)
    return JSONResponse(analysis.change_geojson(run_id, variant), headers={"Content-Disposition": f'attachment; filename="change_{variant}.geojson"'})


@app.get("/api/runs/{run_id}/report.html")
def report(run_id: str, variant: str = "stack"):
    if not re.fullmatch(r"[0-9a-f]{16}", run_id) or variant not in detect.VARIANTS:
        raise HTTPException(404)
    if not (analysis.RUNS / run_id / "result.json").exists():
        raise HTTPException(404)
    return HTMLResponse(analysis.report_html(run_id, variant))


@app.get("/api/runs/{run_id}/{name}")
def run_file(run_id: str, name: str):
    if not re.fullmatch(r"[0-9a-f]{16}", run_id) or not re.fullmatch(r"[a-z_]+\.png", name):
        raise HTTPException(404)
    path = analysis.RUNS / run_id / name
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})
