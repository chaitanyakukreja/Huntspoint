"""
Data ingestion: NYC Open Data (air quality), OSMnx (road/truck network).
Hunts Point peninsula bounds applied where relevant.
"""

import json
import os
from pathlib import Path

import requests
import pandas as pd

try:
    import osmnx as ox
except ImportError:
    ox = None

# Allow running from project root or from backend
PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(PROJECT_ROOT))
from config import (
    HUNTS_POINT_BOUNDS,
    NYC_AIR_QUALITY_URL,
    NYC_AIR_QUALITY_LIMIT,
    DATA_DIR,
    CACHE_AIR,
    CACHE_GRAPH,
)


def ensure_data_dir():
    path = PROJECT_ROOT / DATA_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def fetch_nyc_air_quality(use_cache=True) -> pd.DataFrame:
    """
    Fetch NYC air quality from NYC Open Data (Environment / DOHMH-related).
    Returns DataFrame with geometry or lat/lon if available; else borough-level.
    """
    cache_path = PROJECT_ROOT / CACHE_AIR
    if use_cache and cache_path.exists():
        with open(cache_path) as f:
            rows = json.load(f)
        return pd.DataFrame(rows)

    try:
        r = requests.get(
            NYC_AIR_QUALITY_URL,
            params={"$limit": NYC_AIR_QUALITY_LIMIT},
            timeout=30,
        )
        r.raise_for_status()
        rows = r.json()
        # Normalize NYC Open Data column names (dataset-dependent)
        rows = _normalize_air_columns(rows)
    except Exception as e:
        # Fallback: minimal proxy data for Hunts Point (clearly labeled)
        print(f"NYC Open Data fetch failed: {e}. Using proxy data (labeled).")
        rows = _proxy_air_quality()
        if not rows:
            return pd.DataFrame()

    ensure_data_dir()
    with open(cache_path, "w") as f:
        json.dump(rows, f, indent=0)

    return pd.DataFrame(rows)


def _normalize_air_columns(rows):
    """Map NYC API columns to lat, lon, pm25 where possible."""
    if not rows:
        return rows
    first = rows[0]
    mapping = {}
    for k in first:
        lk = k.lower()
        if "lat" in lk or "latitude" in lk:
            mapping[k] = "lat"
        elif "lon" in lk or "lng" in lk or "longitude" in lk:
            mapping[k] = "lon"
        elif "pm" in lk or "pm2" in lk or "value" in lk or "data_value" in lk:
            mapping[k] = "pm25"
        elif "geo" in lk or "name" in lk:
            mapping[k] = "geo_place_name"
    out = []
    for r in rows:
        nr = {}
        for k, v in r.items():
            nr[mapping.get(k, k)] = v
        out.append(nr)
    return out


def _proxy_air_quality():
    """Generate proxy PM2.5 for Hunts Point grid when live data unavailable."""
    # 5x5 grid over Hunts Point, labeled as proxy
    base_lat, base_lon = 40.798, -73.895
    step_lat, step_lon = 0.004, 0.006
    rows = []
    for i in range(5):
        for j in range(5):
            lat = base_lat + i * step_lat
            lon = base_lon + j * step_lon
            # Slightly higher near industrial core (center)
            dist_center = ((lat - 0.808) ** 2 + (lon + 73.88) ** 2) ** 0.5
            pm25 = 10 + 8 * (1 - min(dist_center / 0.02, 1))  # 10–18 µg/m³
            rows.append({
                "lat": lat,
                "lon": lon,
                "pm25": round(pm25, 1),
                "data_type": "proxy",
                "geo_place_name": "Hunts Point (proxy)",
            })
    return rows


def fetch_osmnx_network(use_cache=True):
    """
    Extract road network for Hunts Point via OSMnx.
    Returns (G, nodes_gdf, edges_gdf) or (None, None, None) if OSMnx missing.
    """
    if ox is None:
        return None, None, None

    bbox = HUNTS_POINT_BOUNDS
    # OSMnx 2.x bbox = (left, bottom, right, top) = (min_lon, min_lat, max_lon, max_lat)
    bbox_tuple = (bbox["min_lon"], bbox["min_lat"], bbox["max_lon"], bbox["max_lat"])

    cache_path = PROJECT_ROOT / CACHE_GRAPH
    if use_cache and cache_path.exists():
        try:
            G = ox.load_graphml(str(cache_path.with_suffix(".graphml")))
            nodes_gdf, edges_gdf = ox.graph_to_gdfs(G)
            return G, nodes_gdf, edges_gdf
        except Exception:
            pass

    try:
        G = ox.graph_from_bbox(bbox_tuple, network_type="drive", simplify=True)
        ensure_data_dir()
        ox.save_graphml(G, str(cache_path.with_suffix(".graphml")))
        nodes_gdf, edges_gdf = ox.graph_to_gdfs(G)
        return G, nodes_gdf, edges_gdf
    except Exception as e:
        print(f"OSMnx fetch failed: {e}. Truck/congestion will use proxy.")
        return None, None, None


def get_truck_edges(edges_gdf):
    """
    Filter edges to freight-relevant (truck) routes from OSM tags.
    highway in (primary, secondary, trunk, motorway, motorway_link, etc.) or
    surface/access tags that allow trucks.
    """
    if edges_gdf is None or edges_gdf.empty:
        return None
    highway = edges_gdf.get("highway")
    if highway is None:
        return edges_gdf
    # Include all driveable; in production could filter by truck=yes or similar
    return edges_gdf
