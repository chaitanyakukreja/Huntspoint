# System Architecture

## High-level

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Leaflet)                                              │
│  • Interactive map (pollution, congestion, noise, exposure)      │
│  • Truck routes overlay                                          │
│  • Layer toggles, tooltips, time-series chart                    │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP (GeoJSON, JSON)
┌────────────────────────────▼────────────────────────────────────┐
│  Backend (FastAPI)                                               │
│  • GET /api/layers/grid   → GeoJSON grid (all layer attributes)  │
│  • GET /api/layers/truck_routes → GeoJSON lines                 │
│  • GET /api/timeseries/hourly → hourly PM2.5, congestion, trucks│
│  • GET /api/bounds        → Hunts Point bbox                     │
│  • GET /                  → index.html (map UI)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  Processing layer (Python)                                       │
│  • backend/data/ingest.py  – NYC API, OSMnx                      │
│  • backend/data/spatial.py – grid, exposure, noise, congestion   │
│  • scripts/ingest_data.py  – fetch and cache raw data            │
│  • scripts/build_layers.py – build and write GeoJSON to disk     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  Data pipeline                                                   │
│  • NYC Open Data (air quality) → data/air_quality.json           │
│  • OSMnx (bbox)            → data/*.graphml                      │
│  • Grid + joins            → data/layers/grid_layers.geojson     │
│  • Truck edges             → data/layers/truck_routes.geojson   │
└─────────────────────────────────────────────────────────────────┘
```

## Data pipeline

1. **Ingest** (`scripts/ingest_data.py`):  
   Fetch NYC air quality (and normalize columns); fetch OSMnx graph for Hunts Point; cache to `data/`.

2. **Build layers** (`scripts/build_layers.py`):  
   Build grid over bounds; aggregate air to grid; add congestion (road density) and noise proxy; compute exposure index; write `grid_layers.geojson` and `truck_routes.geojson` to `data/layers/`.

3. **Serve** (FastAPI):  
   Read pre-built GeoJSON from `data/layers/`; serve to frontend; no heavy computation on request.

## Processing layer

- **Grid**: Regular cells (e.g. 24×24) in WGS84 over Hunts Point.
- **Pollution**: Spatial join of air-quality points to grid; cell mean PM2.5; fallback proxy if no data.
- **Congestion**: Sum of OSMnx edge lengths per cell; normalize to [0,1].
- **Noise**: Same road density (or congestion) as proxy.
- **Exposure**: Weighted combination of normalized PM2.5, congestion, noise.
- **Truck routes**: OSMnx edges (drive network) as GeoJSON lines.

## Visualization layer

- **Map**: Leaflet; tile layer (CartoDB dark); GeoJSON layers for grid (colored by field) and truck routes; popups on click; layer toggles.
- **Time series**: In-page SVG or optional Plotly/matplotlib from `scripts/timeseries_analysis.py`; API provides hourly series for in-browser chart.

## Optional extensions

- **Google Earth Engine**: Add a script to pull NO2/aerosol rasters; clip to Hunts Point; aggregate to grid; document auth and fallback.
- **React + Mapbox**: Replace static HTML with React app and Mapbox GL for advanced styling.
- **Real-time traffic**: Integrate NYC traffic APIs if available; update congestion layer by time of day.
