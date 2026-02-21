#!/usr/bin/env bash
# Copy layer GeoJSON and API payloads into public/ for Vercel static deploy.
# Run from project root after: python scripts/build_layers.py
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/public/layers" "$ROOT/public/api"
cp "$ROOT/data/layers/grid_layers.geojson" "$ROOT/public/layers/" 2>/dev/null || true
cp "$ROOT/data/layers/truck_routes.geojson" "$ROOT/public/layers/" 2>/dev/null || true
echo '{"min_lat":40.798,"max_lat":40.818,"min_lon":-73.895,"max_lon":-73.865,"center":[40.808,-73.88]}' > "$ROOT/public/api/bounds.json"
echo "Prepared public/ for Vercel. Commit public/layers/* and public/api/* if changed."
