"""
Configuration for Hunts Point Geospatial Intelligence Platform.
Hunts Point Peninsula, Bronx, NYC.
"""

# Hunts Point peninsula bounding box (South Bronx, East River)
# Finer than borough; covers the industrial peninsula
HUNTS_POINT_BOUNDS = {
    "min_lat": 40.798,
    "max_lat": 40.818,
    "min_lon": -73.895,
    "max_lon": -73.865,
}

# Center for map default view
CENTER_LAT = 40.808
CENTER_LON = -73.880

# NYC Open Data - Air Quality (DOHMH-related / Environment)
NYC_AIR_QUALITY_URL = "https://data.cityofnewyork.us/resource/c3uy-2p5r.json"
NYC_AIR_QUALITY_LIMIT = 5000

# H3 hexagonal grid (resolution 10 ≈ 0.1 km² per cell; good for neighborhood scale)
H3_RESOLUTION = 10

# Fallback rectangular grid (if H3 not used)
GRID_ROWS = 24
GRID_COLS = 24

# Time-of-day bins for temporal analysis (hour ranges)
TIME_BINS = {
    "early_morning": (4, 9),   # peak logistics
    "midday": (9, 17),
    "evening": (17, 22),
    "night": (22, 4),
}

# OSMnx network type for freight (driving = cars + trucks; we filter by highway type in code)
NETWORK_TYPE = "drive"

# Cache paths (relative to project root)
DATA_DIR = "data"
CACHE_AIR = "data/air_quality.json"
CACHE_GRAPH = "data/osmnx_graph.gpkg"
CACHE_GRID = "data/grid.geojson"
CACHE_LAYERS = "data/layers"
