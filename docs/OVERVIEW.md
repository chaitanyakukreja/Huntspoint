# Overview & Data Sources

## Platform goal

High-resolution, interactive geospatial intelligence for **Hunts Point Peninsula, Bronx, NYC**: air pollution, noise proxy, traffic congestion, and truck/freight network with time-based analysis. Spatial resolution is **finer than borough level** (custom grid over the peninsula).

## Data sources

### Core

| Source | Use | Notes |
|--------|-----|--------|
| **NYC Open Data – Air Quality** | PM2.5 (or proxy) | Dataset `c3uy-2p5r` (Environment). SODA API: `https://data.cityofnewyork.us/resource/c3uy-2p5r.json`. Column names normalized in code (lat/lon, value). |
| **OpenStreetMap (OSMnx)** | Road network, truck routes | Bbox: Hunts Point bounds. `drive` network; freight-relevant edges used for truck layer and congestion/road density. |
| **Traffic counts** | Congestion / volume | Not always available at peninsula scale; **congestion** is modeled via OSMnx (road density / centrality) and labeled as such. |
| **Noise** | Noise proxy | No direct fine-grained noise dataset; **noise proxy** = f(traffic volume, road type) from OSMnx road density; clearly labeled as proxy. |

### Optional / enhancement

- **NYC flood / infrastructure layers**: Optional; not required for MVP.
- **Google Earth Engine**: Optional for NO2/aerosol or land surface; if used, document auth and provide fallback to local/proxy data.

### When data is missing

- **Air quality**: If NYC API fails or returns no points in bounds, the pipeline uses **proxy** PM2.5 grid (labeled `data_type: "proxy"`).
- **OSMnx**: If fetch fails, congestion and noise use distance-from-center or similar **proxies** (noted in layer metadata).
- All simulated or proxy components are **clearly labeled** in the UI and in GeoJSON properties (`data_type`, `*_note`).

## Hunts Point bounds

- **Bounding box**: min_lat 40.798, max_lat 40.818, min_lon -73.895, max_lon -73.865.
- **Center** (map default): 40.808, -73.88.
- Resolution: **24×24 grid** over the peninsula (configurable in `config.py`).

## Outputs

- **Map**: 3+ layers (pollution, congestion, noise, exposure index) + truck routes; layer toggles; hover tooltips; zoom/pan.
- **Time series**: Hourly variation (pollution, congestion, truck density); charts and API endpoint; peak 4–9 AM reflected.
- **Spatiotemporal**: Pollution exposure index, noise proxy, congestion (see [MODELS.md](MODELS.md)).
