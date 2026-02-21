# Analysis Insights, Limitations & Future Improvements

## Analysis insights

- **Spatial**: Pollution and exposure tend to be higher near the core of the peninsula and along major truck corridors; congestion and noise proxies follow road density.
- **Temporal**: Simulated pattern shows **peak logistics 4–9 AM** (truck density and congestion peak; PM2.5 with a morning bump). Midday is moderate; evening lower. Aligns with known Hunts Point food distribution activity.
- **Correlation**: Pollution vs truck density and congestion vs time of day are aligned in the model by design; with real data, correlation can be tested.
- **Truck network**: OSMnx extracts the drive network; high-density corridors and bottlenecks can be identified by overlaying road density or centrality with pollution hotspots.

## Limitations

- **Resolution**: Grid is 24×24; census tracts could be used for policy alignment; current choice is custom grid for speed and clarity.
- **Data**: Air quality may be sparse (proxy used when no points in bounds); congestion and noise are **proxies**, not measured.
- **Static layers**: Map layers do not change by time of day; time variation is only in the time-series chart and API.
- **No GEE**: Satellite-derived NO2/aerosol not included in MVP; can be added with auth and fallback.
- **Truck filter**: All driveable edges shown as truck routes; no OSM truck-only filter in MVP.

## Future improvements

- **Real traffic counts**: Integrate NYC traffic or sensor data for congestion and truck density by time.
- **Census tracts**: Option to aggregate to tract-level for equity and health analyses.
- **Google Earth Engine**: Add NO2/aerosol; document auth; fallback to local/proxy.
- **Time-slider**: Map layers that switch by time bin (early morning / midday / evening).
- **Export**: Allow export of exposure index or PM2.5 by area for reports.
- **Routing**: Suggest routes that minimize exposure (with equity constraints).
