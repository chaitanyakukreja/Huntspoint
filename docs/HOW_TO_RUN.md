# How to Run the Hunts Point Geospatial Intelligence Platform

This guide follows a step-by-step flow similar to the NYC Climate Resilience project: prerequisites, install, data preparation, run services, and verification.

## Introduction: Putting Data in People's Hands

Meaningful change happens when communities have access to clear, local environmental data. This platform turns NYC air quality and spatial data into an interactive map so residents, planners, and advocates can see air pollution (PM2.5) at the neighborhood level and take action—whether that's advocating for cleaner freight routes, supporting green infrastructure, or reporting concerns.

## Prerequisites

1. **Python 3.10+** with pip
2. **Web browser** (Chrome, Firefox, Safari, Edge)
3. **Optional**: Node.js 18+ if you later add a separate frontend build

No Mapbox or Supabase account is required; the app uses Leaflet and Esri satellite tiles with no API keys.

## Step 1: Clone or Download the Project

Ensure you have the project folder (e.g. `hunt point test`) on your machine.

## Step 2: Install Dependencies

Create a virtual environment and install Python dependencies:

```bash
cd "hunt point test"
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Key packages:** FastAPI, uvicorn, geopandas, shapely, osmnx, requests, pandas.

## Step 3: Prepare Data

Run the data pipeline so the map has layers to display.

### 3a. Ingest raw data

```bash
python scripts/ingest_data.py
```

This step:

- Fetches **NYC Open Data** air quality (PM2.5) and caches to `data/air_quality.json`
- Fetches **OpenStreetMap** road network for Hunts Point via OSMnx and caches to `data/*.graphml`
- **Duration:** about 1–2 minutes (network dependent)

### 3b. Build spatial layers

```bash
python scripts/build_layers.py
```

This step:

- Builds a high-resolution grid over Hunts Point
- Aggregates air quality to grid cells
- Computes congestion (road density) and noise proxy
- Computes exposure index
- Writes `data/layers/grid_layers.geojson` and `data/layers/truck_routes.geojson`

**Duration:** under a minute.

## Step 4: Start the Backend

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Server starts at **http://127.0.0.1:8000**. The same process serves the API and the frontend (single-page map).

## Step 5: Open the Map

In your browser go to:

**http://127.0.0.1:8000**

You should see:

- Satellite base map centered on Hunts Point
- Air pollution (PM2.5) heatmap (yellow = lower, red = higher)
- Legend and “About this data”
- Clicking a cell opens a popup and a **sidebar** with neighborhood details and “What you can do” links

## Step 6: Verification

1. **Backend health:**  
   `curl http://127.0.0.1:8000/api/bounds`  
   Should return JSON with `min_lat`, `max_lat`, `center`, etc.

2. **Layers:**  
   `curl http://127.0.0.1:8000/api/layers/grid`  
   Should return GeoJSON with `features` array.

3. **Frontend:**  
   Map loads; clicking a grid cell shows PM2.5 value and sidebar content.

## Data Flow (High Level)

```
NYC Open Data (Air Quality API)
         +
OpenStreetMap (OSMnx)
         │
         ▼
  scripts/ingest_data.py
         │
         ▼
  data/air_quality.json, data/*.graphml
         │
         ▼
  scripts/build_layers.py
         │
         ▼
  data/layers/grid_layers.geojson, truck_routes.geojson
         │
         ▼
  FastAPI backend (GET /api/layers/grid, etc.)
         │
         ▼
  Frontend (Leaflet map + heatmap layer)
```

## Updating Data

To refresh with the latest NYC Open Data and OSM:

1. Run `python scripts/ingest_data.py` again (overwrites cache).
2. Run `python scripts/build_layers.py` again.
3. Reload the browser; no need to restart the server if it’s already running.

## Optional: Time-Series Chart and Other Layers

The current UI focuses on **air pollution (PM2.5)**. The backend still exposes:

- `/api/layers/truck_routes` — truck/freight network
- `/api/timeseries/hourly` — simulated hourly PM2.5 / congestion

To add more layers or the time-series chart back into the frontend, extend `frontend/index.html` (or a future React app) to call these endpoints and add layers/controls.

## Troubleshooting

- **Empty map:** Ensure `data/layers/grid_layers.geojson` exists after running `build_layers.py`.
- **Port in use:** Start with another port, e.g. `uvicorn backend.main:app --port 8001`.
- **OSMnx errors:** If OSMnx fails, the pipeline still builds the grid and uses proxy values for congestion/noise; the air layer may still show NYC data if the API returned points.
