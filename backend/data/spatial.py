"""
Spatial processing: high-resolution grid, pollution exposure index,
noise proxy, congestion proxy. All for Hunts Point bounds.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import geopandas as gpd
    from shapely.geometry import box, Point
    from shapely.ops import unary_union
except ImportError:
    gpd = None
    box = Point = unary_union = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(PROJECT_ROOT))
from config import (
    HUNTS_POINT_BOUNDS,
    GRID_ROWS,
    GRID_COLS,
    DATA_DIR,
    CACHE_GRID,
    CACHE_LAYERS,
)


def get_bounds_box():
    b = HUNTS_POINT_BOUNDS
    if gpd is None:
        return None
    return box(b["min_lon"], b["min_lat"], b["max_lon"], b["max_lat"])


def build_grid_gdf():
    """Build high-resolution grid (cells) over Hunts Point."""
    b = HUNTS_POINT_BOUNDS
    xmin, ymin = b["min_lon"], b["min_lat"]
    xmax, ymax = b["max_lon"], b["max_lat"]
    xs = np.linspace(xmin, xmax, GRID_COLS + 1)
    ys = np.linspace(ymin, ymax, GRID_ROWS + 1)

    cells = []
    for i in range(GRID_ROWS):
        for j in range(GRID_COLS):
            geom = box(xs[j], ys[i], xs[j + 1], ys[i + 1])
            cells.append({"cell_id": i * GRID_COLS + j, "geometry": geom})
    if gpd is None:
        return None
    gdf = gpd.GeoDataFrame(cells, crs="EPSG:4326")
    return gdf


def point_in_bounds(lat, lon):
    b = HUNTS_POINT_BOUNDS
    return b["min_lat"] <= lat <= b["max_lat"] and b["min_lon"] <= lon <= b["max_lon"]


def aggregate_air_to_grid(air_df, grid_gdf):
    """
    Aggregate air quality (PM2.5) to grid. If air_df has lat/lon, spatial join;
    else assign borough average to all cells (with label).
    """
    if grid_gdf is None or air_df is None or air_df.empty:
        return grid_gdf

    if "lat" in air_df.columns and "lon" in air_df.columns:
        pm_col = "pm25" if "pm25" in air_df.columns else next(
            (c for c in air_df.columns if "pm" in c.lower() or "value" in c.lower()), None
        )
        if pm_col is None:
            pm_col = air_df.columns[-1]
        pts = gpd.GeoDataFrame(
            air_df,
            geometry=[Point(x, y) for x, y in zip(air_df["lon"], air_df["lat"])],
            crs="EPSG:4326",
        )
        id_col = _grid_id_col(grid_gdf)
        joined = gpd.sjoin(pts, grid_gdf, how="inner", predicate="within")
        agg = joined.groupby(id_col)[pm_col].agg(["mean", "count"]).reset_index()
        agg = agg.rename(columns={"mean": "pm25_mean", "count": "pm25_count"})
        grid_gdf = grid_gdf.merge(agg, on=id_col, how="left")
        grid_gdf["pm25_mean"] = grid_gdf["pm25_mean"].fillna(air_df[pm_col].mean() if pm_col in air_df.columns else 12)
        grid_gdf["data_type"] = joined["data_type"].iloc[0] if "data_type" in joined.columns else "observed"
    else:
        # Borough or city-level: constant with label
        pm_val = 12.0
        if "geo_place_name" in air_df.columns:
            pm_val = float(air_df.get("data_value", pd.Series([12])).iloc[0]) if "data_value" in air_df.columns else 12
        grid_gdf["pm25_mean"] = pm_val
        grid_gdf["data_type"] = "proxy (borough/city level)"
    return grid_gdf


def _grid_id_col(grid_gdf):
    """Column to use as cell id (cell_id or h3_cell)."""
    if grid_gdf is None:
        return "cell_id"
    return "h3_cell" if "h3_cell" in grid_gdf.columns else "cell_id"


def add_congestion_proxy(grid_gdf, edges_gdf=None):
    """
    Congestion proxy: road density / centrality per cell.
    If edges_gdf provided (OSMnx), use edge length per cell; else distance from center.
    """
    if grid_gdf is None:
        return grid_gdf
    if gpd is None:
        grid_gdf["congestion"] = 0.5
        grid_gdf["congestion_note"] = "proxy (no GeoPandas)"
        return grid_gdf

    id_col = _grid_id_col(grid_gdf)
    geom_cols = [id_col, "geometry"]

    if edges_gdf is not None and not edges_gdf.empty and "geometry" in edges_gdf.columns:
        edges = edges_gdf.copy()
        edges = edges.set_crs("EPSG:4326", allow_override=True)
        edges_proj = edges.to_crs("EPSG:32618")  # UTM 18N for NYC area
        edges["length_km"] = edges_proj.geometry.length / 1000.0
        joined = gpd.sjoin(edges, grid_gdf[geom_cols], how="inner", predicate="intersects")
        density = joined.groupby(id_col)["length_km"].sum().reset_index()
        density = density.rename(columns={"length_km": "road_km"})
        grid_gdf = grid_gdf.merge(density, on=id_col, how="left")
        grid_gdf["road_km"] = grid_gdf["road_km"].fillna(0)
        max_km = grid_gdf["road_km"].max() or 1
        grid_gdf["congestion"] = (grid_gdf["road_km"] / max_km).clip(0, 1)
        grid_gdf["congestion_note"] = "road density (OSMnx)"
    else:
        # Distance from peninsula center as proxy
        cx, cy = 40.808, -73.88
        grid_gdf["congestion"] = 1 - grid_gdf.geometry.centroid.distance(Point(cy, cx)) / 0.015
        grid_gdf["congestion"] = grid_gdf["congestion"].clip(0, 1)
        grid_gdf["congestion_note"] = "proxy (distance from center)"
    return grid_gdf


def add_pollution_proxy_when_flat(grid_gdf):
    """
    When PM2.5 has no spatial variation (e.g. borough-level), replace with a
    proxy that varies by road density and noise so the map gives insight.
    """
    if grid_gdf is None or "pm25_mean" not in grid_gdf.columns:
        return grid_gdf
    pm = grid_gdf["pm25_mean"]
    if pm.std() >= 0.5:
        return grid_gdf
    base = float(pm.mean()) if len(pm) else 12.0
    base = max(8, min(14, base))
    if "road_km" in grid_gdf.columns:
        rk = grid_gdf["road_km"].fillna(0)
        rk_n = (rk - rk.min()) / (rk.max() - rk.min() or 1)
    else:
        rk_n = 0.5
    if "noise_proxy" in grid_gdf.columns:
        n = grid_gdf["noise_proxy"].fillna(0.5)
    else:
        n = 0.5
    # 10–18 µg/m³ range: higher near roads and noisier areas
    grid_gdf["pm25_mean"] = base + 6.0 * (0.6 * rk_n + 0.4 * n).clip(0, 1)
    grid_gdf["data_type"] = "proxy (spatially adjusted from roads & truck routes)"
    return grid_gdf


def add_noise_proxy(grid_gdf, edges_gdf=None):
    """
    Noise proxy: f(traffic volume, road type). Uses road_km if already in grid else congestion.
    """
    if grid_gdf is None:
        return grid_gdf
    if "road_km" in grid_gdf.columns:
        max_km = grid_gdf["road_km"].max() or 1
        grid_gdf["noise_proxy"] = (grid_gdf["road_km"] / max_km).clip(0, 1) * 0.5 + 0.3
    else:
        grid_gdf["noise_proxy"] = (grid_gdf.get("congestion", 0.5)).clip(0, 1) * 0.5 + 0.3
    grid_gdf["noise_note"] = "proxy (traffic/road density)"
    return grid_gdf


def pollution_exposure_index(grid_gdf):
    """
    Exposure = f(pollution, traffic density, proximity to roads).
    Simple: weighted average of normalized pm25, congestion, noise.
    """
    if grid_gdf is None:
        return grid_gdf
    pm = grid_gdf["pm25_mean"].fillna(12)
    pm_n = (pm - pm.min()) / (pm.max() - pm.min() or 1)
    c = grid_gdf.get("congestion", 0.5).fillna(0.5)
    n = grid_gdf.get("noise_proxy", 0.5).fillna(0.5)
    grid_gdf["exposure_index"] = 0.5 * pm_n + 0.3 * c + 0.2 * n
    grid_gdf["exposure_index"] = grid_gdf["exposure_index"].clip(0, 1)
    return grid_gdf


def grid_to_geojson(gdf, props=None):
    """Convert grid GeoDataFrame to GeoJSON dict."""
    if gdf is None:
        return {"type": "FeatureCollection", "features": []}
    if props is None:
        props = [c for c in gdf.columns if c != "geometry"]
    return json.loads(gpd.GeoDataFrame(gdf).to_json(na="drop", drop_id=True))


def edges_to_geojson(edges_gdf):
    """Convert edges to GeoJSON FeatureCollection."""
    if edges_gdf is None or edges_gdf.empty or gpd is None:
        return {"type": "FeatureCollection", "features": []}
    return json.loads(gpd.GeoDataFrame(edges_gdf).to_json(na="drop", drop_id=True))
