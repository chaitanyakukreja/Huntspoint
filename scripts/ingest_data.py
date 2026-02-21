#!/usr/bin/env python3
"""
Ingest NYC air quality and OSMnx network for Hunts Point.
Run from project root: python scripts/ingest_data.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.data.ingest import fetch_nyc_air_quality, fetch_osmnx_network, ensure_data_dir


def main():
    ensure_data_dir()
    print("Fetching NYC air quality...")
    df = fetch_nyc_air_quality(use_cache=False)
    print(f"  Rows: {len(df)}")
    if not df.empty and "data_type" in df.columns:
        print(f"  Data type: {df['data_type'].iloc[0]}")
    print("Fetching OSMnx network (Hunts Point)...")
    G, nodes, edges = fetch_osmnx_network(use_cache=False)
    if G is not None:
        print(f"  Nodes: {len(nodes)}, Edges: {len(edges)}")
    else:
        print("  OSMnx not available or failed; proxy will be used for layers.")
    print("Done. Run: python scripts/build_layers.py")


if __name__ == "__main__":
    main()
