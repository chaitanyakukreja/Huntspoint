# Model Explanation

## How pollution is estimated

- **Primary**: NYC Open Data air quality dataset (`c3uy-2p5r`). Points with lat/lon are spatially joined to the high-resolution grid; each cell gets the **mean PM2.5** of points inside it.
- **Fallback**: If the API fails or returns no data in Hunts Point bounds, a **proxy** grid is used: PM2.5 values vary by distance from the industrial core (center of peninsula), in a plausible range (e.g. 10–18 µg/m³), and are **labeled as proxy** in `data_type`.
- **Assumptions**: Monitors are representative of the area; interpolation is simple (cell mean). No atmospheric dispersion model.
- **Limitations**: Sparse monitors may leave many cells with borough/city average; proxy is not calibrated to measurements.

## How the noise proxy is built

- **Formula**: Noise proxy = f(traffic volume, road type). Implemented as a function of **road density** (km of road per grid cell from OSMnx edges).
- **If OSMnx available**: `noise_proxy` = normalized road length per cell, scaled to (0.3, 0.8) for display.
- **If not**: Derived from congestion proxy (distance from center), same scaling.
- **Assumptions**: More road length ⇒ more traffic ⇒ higher noise. No actual decibel data; road type not yet weighted (e.g. highway vs residential).
- **Limitations**: Proxy only; no building canyon or barrier effects; not validated against noise measurements.

## How congestion is modeled

- **With OSMnx**: **Road density** per cell (sum of edge lengths intersecting each cell). Normalized to [0, 1] as congestion intensity.
- **Without OSMnx**: **Distance from center** of peninsula as proxy (closer to core ⇒ higher congestion).
- **Alternative (optional)**: Centrality (e.g. betweenness) or edge density from NetworkX; current MVP uses length-based density.
- **Assumptions**: Denser road network ⇒ more traffic/congestion. No real-time speed or count data.
- **Limitations**: Static network; no time-of-day variation in the spatial layer (time variation is in the time-series charts only).

## Pollution exposure index

- **Formula**: Exposure = f(pollution, traffic density, proximity to roads).
- **Use**: Single metric per cell for “highest exposure” areas; combines air quality and traffic/road proximity.
- **Limitations**: Weights are illustrative; not from a health study.

**Calculation pseudocode** (aligned with NYC Climate Resilience–style priority scores):

```
FUNCTION compute_exposure_index(grid_cells):
    FOR each cell IN grid_cells:
        // Normalize PM2.5 to 0-1 (min-max over study area)
        pm_norm = (cell.pm25_mean - pm_min) / (pm_max - pm_min)

        // Congestion and noise_proxy already in [0, 1] from road density
        congestion = cell.congestion
        noise_proxy = cell.noise_proxy

        // Weighted combination (weights are illustrative)
        exposure_index = 0.5 * pm_norm + 0.3 * congestion + 0.2 * noise_proxy
        exposure_index = clip(exposure_index, 0, 1)

        cell.exposure_index = exposure_index
    RETURN grid_cells
```

## Truck network

- **Source**: OSMnx `drive` network within Hunts Point bbox. All driveable edges are treated as **truck-capable** (no OSM filter on `truck=yes` in MVP).
- **Refinement**: Can be restricted to highway types (primary, secondary, trunk, motorway) or OSM tags for trucks in a future version.
- **Overlay**: Truck routes layer can be toggled with pollution/congestion to show corridors and hotspots.

## Time-of-day variation

- **Pattern**: Simulated to match Hunts Point logistics (peak 4–9 AM).
  - **PM2.5**: Slight morning peak; lower at night.
  - **Truck density**: Peak around 6–7 AM; moderate midday; lower evening.
  - **Congestion**: Follows truck density.
- **Delivery**: API endpoint `/api/timeseries/hourly` and optional static chart from `scripts/timeseries_analysis.py`.
- **Limitation**: Simulated; replace with observed counts/sensors when available.
