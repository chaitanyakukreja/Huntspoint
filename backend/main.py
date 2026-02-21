"""
FastAPI backend for Hunts Point Geospatial Intelligence Platform.
Serves map layers (GeoJSON), time-series data, and static frontend.
"""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAYERS_DIR = PROJECT_ROOT / "data" / "layers"


app = FastAPI(
    title="Hunts Point Geospatial Intelligence",
    description="High-resolution GIS: air pollution, noise proxy, congestion, truck network.",
    version="0.1.0",
)


def _load_geojson(name: str):
    p = LAYERS_DIR / name
    if not p.exists():
        return {"type": "FeatureCollection", "features": []}
    with open(p) as f:
        return json.load(f)


@app.get("/")
async def root():
    return FileResponse(PROJECT_ROOT / "frontend" / "index.html")


@app.get("/api/layers/grid")
async def get_grid_layers():
    """GeoJSON for pollution, congestion, noise, exposure (combined grid)."""
    return _load_geojson("grid_layers.geojson")


@app.get("/api/layers/truck_routes")
async def get_truck_routes():
    """GeoJSON for truck/freight routes."""
    data = _load_geojson("truck_routes.geojson")
    return data


@app.get("/api/timeseries/hourly")
async def get_timeseries_hourly():
    """
    Hourly / time-of-day variation: pollution, congestion, truck density.
    Simulated pattern: peak logistics 4–9 AM, moderate midday, lower evening.
    """
    # Realistic pattern for Hunts Point (food distribution peak early AM)
    hours = list(range(24))
    # PM2.5: slight morning peak (trucks + cold start), lower at night
    pm25 = [10 + 3 * (1 + (h - 6) ** 2 / 36) for h in hours]
    pm25 = [min(18, max(8, p)) for p in pm25]
    # Congestion / truck density: peak 4–9 AM
    truck_density = [
        0.3 + 0.7 * (1 - min(abs(h - 6.5) / 6, 1)) for h in hours
    ]
    congestion = [0.4 + 0.5 * d for d in truck_density]
    return {
        "hours": hours,
        "pm25": [round(x, 1) for x in pm25],
        "truck_density": [round(x, 2) for x in truck_density],
        "congestion": [round(x, 2) for x in congestion],
        "note": "Simulated time-of-day pattern; peak logistics 4–9 AM.",
    }


@app.get("/api/bounds")
async def get_bounds():
    """Hunts Point peninsula bounds for map init."""
    return {
        "min_lat": 40.798,
        "max_lat": 40.818,
        "min_lon": -73.895,
        "max_lon": -73.865,
        "center": [40.808, -73.88],
    }


# Serve frontend assets if present
frontend_path = PROJECT_ROOT / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
