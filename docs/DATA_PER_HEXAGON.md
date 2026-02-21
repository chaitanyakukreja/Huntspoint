# How We Get Data for Each Hexagon

This explains where the numbers in each H3 hexagon come from and why air pollution and noise proxy can look similar.

## 1. Creating the hexagons

- We use **H3** (Uber’s hexagonal grid) at **resolution 10** (~0.1 km² per cell).
- We take the Hunts Point bounding box and call **`h3shape_to_cells`** (or `polygon_to_cells`) to get every H3 cell that overlaps that box.
- Each cell gets a polygon (from **`cell_to_boundary`**) and is stored as a row in a GeoDataFrame. That’s our set of hexagons.

So: **hexagons = H3 cells whose boundaries overlap Hunts Point.**

## 2. Road data per hexagon (the main input)

- We download the **road network** for Hunts Point from **OpenStreetMap** using **OSMnx** (drive network).
- For each hexagon we:
  - Find all OSM **edges** (road segments) that **intersect** that hexagon (spatial join).
  - Sum their **length in km** (in a projected CRS, e.g. UTM for NYC).
- That sum is **`road_km`** for that hexagon.

So: **road_km per hexagon = total length of roads inside that hexagon (from OSM).**

## 3. Air pollution (PM2.5) per hexagon

- **First we try NYC Open Data:** we fetch the NYC air quality dataset and, for each monitor/sample point with lat/lon, we assign it to the hexagon that contains it. Then we take the **mean PM2.5** of all points in each hexagon.
- **When that doesn’t vary in our area** (e.g. no monitors inside Hunts Point, or one borough-level value everywhere), we use a **spatially adjusted proxy** so the map still shows variation:
  - We already have **road_km** and **noise_proxy** per hexagon (see below).
  - We set  
    **PM2.5 = base + 6 × (0.6 × road_km_norm + 0.4 × noise_proxy)**  
    so values sit in a range like ~10–18 µg/m³, with **higher values where there’s more road and higher noise proxy**.
  - We set **data_type** to **"proxy (spatially adjusted from roads & truck routes)"** so you know it’s not from monitors in that area.

So: **air pollution per hexagon = either mean of NYC air points in that hexagon, or (when flat) a proxy from road length + noise proxy.**

## 4. Noise proxy per hexagon

- We **do not** have real decibel measurements per hexagon.
- We use **road_km** as a stand‑in for “how much traffic/noise is likely here”:
  - **noise_proxy = normalized(road_km)** scaled to something like 0.3–0.8 for display (or 0–1 internally).
- So: **noise proxy per hexagon = function of road length in that hexagon (OSM).**

## 5. Truck routes (lines, not per hexagon)

- **Truck routes** are the **same OSM road edges** (from OSMnx) drawn as **lines** on the map.
- They are **not** aggregated per hexagon; they’re the raw road network we also use to compute **road_km** (and thus noise and the air proxy).

---

## Why air pollution and noise proxy look similar

- **Noise proxy** is defined from **road_km** (more road ⇒ higher noise proxy).
- **When we use the fallback**, **air pollution** is set from **road_km + noise_proxy**. So in that case **both layers are driven by the same road (and truck) pattern**.
- So:
  - **If you see "proxy (spatially adjusted from roads & truck routes)"** in the sidebar for air pollution, then the air layer is **intentionally** derived from roads and noise. It’s **expected** that air and noise look similar; nothing is wrong with the data.
  - In the **real world**, traffic also drives both noise and PM2.5, so some similarity is expected even when we use real monitor data. In our current setup, when we don’t have monitor-based variation, we make that link explicit so the map still gives useful spatial insight (e.g. “worse along truck corridors”).

---

## Summary table

| What you see      | Source per hexagon |
|-------------------|--------------------|
| Hexagons          | H3 grid over Hunts Point bbox |
| road_km           | Sum of OSM road lengths intersecting the hexagon |
| Noise proxy       | Normalized road_km (proxy for traffic-related noise) |
| Air pollution     | NYC Open Data mean in hexagon, or proxy from road_km + noise_proxy when flat |
| Truck routes      | OSM road edges (lines), not per-hexagon |
