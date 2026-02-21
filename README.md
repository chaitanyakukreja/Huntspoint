# Hunts Point Geospatial Intelligence Platform

High-resolution, interactive GIS platform for **Hunts Point Peninsula, Bronx, NYC** — air pollution (PM2.5), with optional noise proxy, traffic congestion, and truck/freight network. The goal is to put local environmental data in people’s hands so residents, planners, and advocates can see neighborhood-level air quality and take action.

## Quick start

```bash
# Create venv (recommended)
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install
pip install -r requirements.txt

# 1) Ingest data (NYC Open Data + OSMnx; first run may take a few minutes)
python scripts/ingest_data.py

# 2) Build spatial layers (grid, exposure, noise, congestion)
python scripts/build_layers.py

# 3) Start backend
uvicorn backend.main:app --reload

# 4) Open map
# Browser: http://127.0.0.1:8000
# Map: http://127.0.0.1:8000/map
```

## Features

- **Interactive map**: Pollution heatmap, truck routes, congestion, noise proxy; layer toggles, tooltips, zoom/pan.
- **Time series**: Hourly / time-of-day variation (pollution, congestion, truck density); peak logistics 4–9 AM.
- **Spatiotemporal indices**: Pollution exposure, noise proxy, congestion (OSMnx/centrality).
- **Truck network**: Freight-relevant roads, high-density corridors, overlay with pollution hotspots.

## Data

- **NYC Open Data** — Air quality (PM2.5 proxy where available).
- **OpenStreetMap (OSMnx)** — Roads, truck routes, network centrality.
- **Proxies** — Noise (traffic + road type), congestion (edge density/centrality); simulated components clearly labeled.

## Docs

- [How to run](docs/HOW_TO_RUN.md) — Prerequisites, step-by-step setup, verification, data flow
- [Data flow](docs/DATA_FLOW.md) — From NYC Open Data / OSM to the map
- [Data per hexagon](docs/DATA_PER_HEXAGON.md) — How each H3 cell gets its values; why air and noise can look similar
- [Overview & data sources](docs/OVERVIEW.md)
- [Spatial processing & models](docs/MODELS.md)
- [System architecture](docs/ARCHITECTURE.md)
- [AI & governance](docs/GOVERNANCE.md)

## Tech stack

- **Backend**: Python, FastAPI, GeoPandas, Shapely, OSMnx.
- **Frontend**: Leaflet (vanilla JS).
- **Optional**: Google Earth Engine (see docs).

## License

Code: MIT. Data: respective NYC Open Data / OSM licenses.
