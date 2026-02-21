"""
H3 hexagonal grid utilities for Hunts Point.
Provides uniform cells comparable to NYC-wide H3 indexing.
"""

from pathlib import Path

try:
    import h3
except ImportError:
    h3 = None

try:
    import geopandas as gpd
    from shapely.geometry import Polygon
except ImportError:
    gpd = None
    Polygon = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(PROJECT_ROOT))
from config import HUNTS_POINT_BOUNDS, H3_RESOLUTION


def bbox_to_h3_polygon():
    """Return GeoJSON-style polygon for Hunts Point bbox (for h3.polygon_to_cells)."""
    b = HUNTS_POINT_BOUNDS
    # GeoJSON: first and last point same (closed ring); [lng, lat]
    return [[
        [b["min_lon"], b["min_lat"]],
        [b["max_lon"], b["min_lat"]],
        [b["max_lon"], b["max_lat"]],
        [b["min_lon"], b["max_lat"]],
        [b["min_lon"], b["min_lat"]],
    ]]


def get_h3_cells_in_bounds(resolution=None):
    """Return set of H3 cell IDs covering Hunts Point bounds."""
    if h3 is None:
        return set()
    res = resolution if resolution is not None else H3_RESOLUTION
    b = HUNTS_POINT_BOUNDS
    outer = [(b["min_lat"], b["min_lon"]), (b["min_lat"], b["max_lon"]), (b["max_lat"], b["max_lon"]), (b["max_lat"], b["min_lon"]), (b["min_lat"], b["min_lon"])]
    try:
        poly = h3.LatLngPoly(outer)
        cells = h3.h3shape_to_cells(poly, res)
    except Exception:
        try:
            poly = bbox_to_h3_polygon()
            cells = h3.polygon_to_cells({"type": "Polygon", "coordinates": [poly]}, res)
        except Exception:
            cells = set()
    return set(cells)


def h3_cell_to_polygon(cell_id):
    """Return Shapely Polygon for H3 cell (for GeoDataFrame)."""
    if h3 is None or Polygon is None:
        return None
    try:
        boundary = h3.cell_to_boundary(cell_id)
        # h3 returns (lat, lng); Shapely uses (lng, lat)
        if boundary:
            ring = [(p[1], p[0]) for p in boundary]
            ring.append(ring[0])
            return Polygon(ring)
    except Exception:
        pass
    try:
        boundary = h3.cells_to_h3shape([cell_id])
        if hasattr(boundary, "__geo_interface__"):
            from shapely.geometry import shape
            return shape(boundary.__geo_interface__)
    except Exception:
        pass
    return None


def build_h3_gdf(resolution=None):
    """Build GeoDataFrame of H3 hexagons covering Hunts Point."""
    if gpd is None or h3 is None:
        return None
    cells = get_h3_cells_in_bounds(resolution)
    if not cells:
        return None
    rows = []
    for c in cells:
        geom = h3_cell_to_polygon(c)
        if geom is not None:
            rows.append({"h3_cell": c, "geometry": geom})
    if not rows:
        return None
    gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    return gdf
