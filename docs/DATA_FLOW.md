# Data Flow

This document describes how data moves from sources to the map, similar to the NYC Climate Resilience project's data flow.

## Initial data preparation

```
NYC Open Data (Air Quality API)
         +
OpenStreetMap (OSMnx)
         │
         ▼
  scripts/ingest_data.py
         │
  Raw fetch & cache:
  - data/air_quality.json
  - data/*.graphml (road network)
         │
         ▼
  scripts/build_layers.py
         │
  Spatial aggregation:
  - Build grid over Hunts Point bounds
  - Spatial join: air points → grid cells (mean PM2.5)
  - Road density per cell (OSMnx edges) → congestion, noise proxy
  - Exposure index = 0.5*pm_norm + 0.3*congestion + 0.2*noise
         │
         ▼
  Output:
  - data/layers/grid_layers.geojson (all metrics per cell)
  - data/layers/truck_routes.geojson (line layer)
```

## Runtime data access

```
User opens map (GET /)
         │
         ▼
  Frontend: GET /api/layers/grid, GET /api/layers/truck_routes (if needed)
         │
         ▼
  Backend: Read GeoJSON from data/layers/
         │
         ▼
  Frontend: Draw heatmap layer + legend; attach click → popup + sidebar
```

No database or auth in the current MVP; all layer data is file-based and served by FastAPI.

## Comparison with NYC Climate Resilience

| Aspect            | NYC Climate Resilience     | Hunts Point (this project)        |
|------------------|----------------------------|------------------------------------|
| Spatial indexing | H3 hexagonal grid          | Rectangular grid (configurable)    |
| Data format      | Parquet + JSON + GeoJSON   | JSON + GeoJSON                     |
| Backend cache    | In-memory H3 features      | File-based GeoJSON                 |
| Frontend         | React + Mapbox GL          | Vanilla Leaflet                    |
| Community data   | Supabase (reviews, etc.)   | Not yet                            |

We could adopt H3 for Hunts Point in a future iteration to align with NYC-wide tools and enable hexagonal visualization.
