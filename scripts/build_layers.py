#!/usr/bin/env python3
"""
Build spatial layers: H3 hexagons (or fallback grid), pollution, congestion, noise, exposure.
Writes GeoJSON to data/layers/ for the map and API.
Run from project root: python scripts/build_layers.py
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.data.ingest import fetch_nyc_air_quality, fetch_osmnx_network, get_truck_edges
from backend.data.spatial import (
    build_grid_gdf,
    aggregate_air_to_grid,
    add_congestion_proxy,
    add_noise_proxy,
    add_pollution_proxy_when_flat,
    pollution_exposure_index,
    grid_to_geojson,
    edges_to_geojson,
)


def main():
    layers_dir = PROJECT_ROOT / "data" / "layers"
    layers_dir.mkdir(parents=True, exist_ok=True)

    air_df = fetch_nyc_air_quality(use_cache=True)
    G, nodes_gdf, edges_gdf = fetch_osmnx_network(use_cache=True)
    truck_edges = get_truck_edges(edges_gdf) if edges_gdf is not None else None

    try:
        from backend.data.h3_utils import build_h3_gdf
        grid_gdf = build_h3_gdf()
        if grid_gdf is not None:
            grid_gdf["cell_id"] = grid_gdf["h3_cell"]
            print("Using H3 hexagonal grid.")
    except Exception as e:
        print(f"H3 not used: {e}. Using rectangular grid.")
        grid_gdf = None

    if grid_gdf is None:
        grid_gdf = build_grid_gdf()

    if grid_gdf is None:
        print("GeoPandas required for grid. Install geopandas.")
        return

    grid_gdf = aggregate_air_to_grid(air_df, grid_gdf)
    grid_gdf = add_congestion_proxy(grid_gdf, edges_gdf)
    grid_gdf = add_noise_proxy(grid_gdf, edges_gdf)
    grid_gdf = add_pollution_proxy_when_flat(grid_gdf)
    grid_gdf = pollution_exposure_index(grid_gdf)

    # Remove corner/water hexagons where there are no roads (index would be 0 or meaningless)
    if "road_km" in grid_gdf.columns:
        grid_gdf = grid_gdf[grid_gdf["road_km"].fillna(0) > 0].copy()
        print(f"  Kept {len(grid_gdf)} hexagons with road data (dropped water/corners).")

    props = ["h3_cell", "cell_id", "pm25_mean", "congestion", "noise_proxy", "exposure_index", "data_type", "congestion_note", "noise_note", "road_km"]
    props = [c for c in props if c in grid_gdf.columns]
    geoj = grid_to_geojson(grid_gdf, props=props)
    with open(layers_dir / "grid_layers.geojson", "w") as f:
        json.dump(geoj, f)

    truck_geoj = edges_to_geojson(truck_edges)
    with open(layers_dir / "truck_routes.geojson", "w") as f:
        json.dump(truck_geoj, f)

    print("Layers written to data/layers/")
    print("  grid_layers.geojson (H3 hexagons: pollution, noise, congestion, exposure)")
    print("  truck_routes.geojson")


if __name__ == "__main__":
    main()
