#!/usr/bin/env python3
"""
Fetch NYC 311 noise complaints, aggregate to H3 hexagons over Hunts Point,
and save a local map so you can see the result.

Run from project root:
  python scripts/fetch_311_noise.py

Outputs:
  data/311_noise_complaints.json   - raw 311 records (cached)
  data/311_noise_by_hex.geojson    - H3 hexagons with complaint counts
  data/311_noise_map.html          - open in browser to view map locally
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import requests
from config import HUNTS_POINT_BOUNDS, NYC_311_URL, NYC_311_NOISE_LIMIT, CACHE_311_NOISE, DATA_DIR, H3_RESOLUTION


def normalize_latlon(rows):
    """Find lat/lon columns (NYC 311 can use different names)."""
    if not rows:
        return None, None
    first = rows[0]
    lat_col = None
    lon_col = None
    for k in first:
        klo = k.lower().replace(" ", "_")
        if "lat" in klo and "lon" not in klo:
            lat_col = k
        if "lon" in klo or ("lng" in klo and "lon" not in klo):
            lon_col = k
    if lat_col is None:
        for k in first:
            if k.lower() in ("latitude", "y", "incident_latitude"):
                lat_col = k
                break
    if lon_col is None:
        for k in first:
            if k.lower() in ("longitude", "x", "incident_longitude"):
                lon_col = k
                break
    return lat_col, lon_col


def fetch_311_noise(use_cache=True):
    """Fetch 311 service requests filtered to noise-related complaints."""
    cache_path = PROJECT_ROOT / CACHE_311_NOISE
    if use_cache and cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)

    # NYC SODA: filter by complaint_type containing "Noise"
    # Column names in 311: complaint_type, created_date, latitude, longitude (or with spaces)
    params = {
        "$limit": NYC_311_NOISE_LIMIT,
        "$where": "complaint_type like '%Noise%'",  # SoQL
    }
    try:
        r = requests.get(NYC_311_URL, params=params, timeout=60)
        r.raise_for_status()
        rows = r.json()
    except Exception as e:
        print(f"311 API error: {e}")
        # Try without $where (some portals use $q)
        try:
            r = requests.get(NYC_311_URL, params={"$limit": 1000}, timeout=30)
            r.raise_for_status()
            rows = r.json()
            if rows:
                # Filter in Python
                key = next((k for k in rows[0] if "complaint" in k.lower() and "type" in k.lower()), None)
                if key:
                    rows = [x for x in rows if x.get(key) and "Noise" in str(x.get(key, ""))]
                else:
                    rows = []
        except Exception as e2:
            print(f"Fallback failed: {e2}")
            rows = []

    PROJECT_ROOT.joinpath(DATA_DIR).mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(rows, f, indent=0)
    return rows


def filter_to_hunts_point(rows, lat_col, lon_col):
    b = HUNTS_POINT_BOUNDS
    out = []
    for r in rows:
        try:
            lat = float(r.get(lat_col))
            lon = float(r.get(lon_col))
        except (TypeError, ValueError):
            continue
        if b["min_lat"] <= lat <= b["max_lat"] and b["min_lon"] <= lon <= b["max_lon"]:
            out.append({"lat": lat, "lon": lon, **r})
    return out


def aggregate_to_h3(records):
    """Assign each complaint to H3 cell and count per cell."""
    try:
        import h3
    except ImportError:
        print("Install h3: pip install h3")
        return {}
    counts = {}
    for r in records:
        lat, lon = r.get("lat"), r.get("lon")
        if lat is None or lon is None:
            continue
        try:
            cell = h3.latlng_to_cell(lat, lon, H3_RESOLUTION)
            counts[cell] = counts.get(cell, 0) + 1
        except Exception:
            continue
    return counts


def build_hex_geojson(counts):
    """Build GeoJSON of H3 hexagons with complaint_count."""
    try:
        from backend.data.h3_utils import build_h3_gdf, get_h3_cells_in_bounds, h3_cell_to_polygon
        import geopandas as gpd
    except ImportError as e:
        print(f"Need geopandas/h3: {e}")
        return None

    cells = get_h3_cells_in_bounds()
    rows = []
    for c in cells:
        geom = h3_cell_to_polygon(c)
        if geom is not None:
            rows.append({
                "h3_cell": c,
                "complaint_count": counts.get(c, 0),
                "geometry": geom,
            })
    if not rows:
        return {"type": "FeatureCollection", "features": []}
    gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    return json.loads(gdf.to_json(na="drop", drop_id=True))


def write_local_map(geojson_path, html_path):
    """Write a minimal HTML file that loads the GeoJSON and shows it with Leaflet."""
    html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <title>311 Noise Complaints — Hunts Point (local)</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body>
  <div id="map" style="height:100vh;"></div>
  <script>
    const map = L.map('map').setView([40.808, -73.88], 15);
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { attribution: '© Esri' }).addTo(map);

    fetch('311_noise_by_hex.geojson')
      .then(r => r.json())
      .then(data => {
        const maxCount = Math.max(...data.features.map(f => f.properties.complaint_count || 0), 1);
        L.geoJSON(data, {
          style: f => {
            const c = f.properties.complaint_count || 0;
            const ratio = c / maxCount;
            const r = Math.round(255 - 90 * ratio), g = Math.round(165 - 165 * ratio), b = 38;
            const color = '#' + [r,g,b].map(x => x.toString(16).padStart(2,'0')).join('');
            return { fillColor: color, color: color, weight: 1, fillOpacity: 0.5 + 0.4 * ratio };
          }
        })
        .bindPopup(f => '<b>311 noise complaints</b><br/>' + (f.properties.complaint_count || 0) + ' in this hexagon')
        .addTo(map);
      })
      .catch(e => document.body.innerHTML = '<p>Load 311_noise_by_hex.geojson in same folder as this HTML. ' + e.message + '</p>');
  </script>
</body>
</html>"""
    html_path = Path(html_path)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")


def main():
    print("Fetching NYC 311 noise complaints...")
    rows = fetch_311_noise(use_cache=True)
    print(f"  Total noise records from API: {len(rows)}")

    lat_col, lon_col = normalize_latlon(rows)
    if not lat_col or not lon_col:
        print("  Could not find latitude/longitude columns. Column names:", list(rows[0].keys()) if rows else "no rows")
        return

    # Normalize to lat/lon for filtering
    records = []
    for r in rows:
        try:
            lat = float(r.get(lat_col))
            lon = float(r.get(lon_col))
        except (TypeError, ValueError):
            continue
        records.append({"lat": lat, "lon": lon, **r})

    in_bounds = filter_to_hunts_point(records, "lat", "lon")
    print(f"  In Hunts Point bounds: {len(in_bounds)}")

    if not in_bounds:
        print("  No 311 noise complaints in Hunts Point bounds. Try increasing area or check API filters.")
        # Still build hex map with zeros so user sees the grid
        counts = {}
    else:
        counts = aggregate_to_h3(in_bounds)
        print(f"  H3 cells with at least one complaint: {len(counts)}")
        if counts:
            print(f"  Max complaints in one hex: {max(counts.values())}")

    out_dir = PROJECT_ROOT / DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    geojson = build_hex_geojson(counts)
    if geojson:
        geojson_path = out_dir / "311_noise_by_hex.geojson"
        with open(geojson_path, "w") as f:
            json.dump(geojson, f)
        print(f"  Wrote {geojson_path}")

        html_path = out_dir / "311_noise_map.html"
        write_local_map(geojson_path, html_path)
        print(f"  Wrote {html_path}")
        print()
        print("To view locally: open this file in your browser:")
        print(f"  file://{html_path.resolve()}")
        print("  (Or: open data/311_noise_map.html)")
    else:
        print("  Could not build GeoJSON (missing h3/geopandas?).")


if __name__ == "__main__":
    main()
