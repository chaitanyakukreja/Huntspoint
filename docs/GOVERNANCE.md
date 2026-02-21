# AI & Governance

## Bias risks

- **Industrial vs residential exposure**: Hunts Point is heavily industrial (food distribution). Our exposure index combines pollution and traffic; areas near warehouses and truck routes will score higher. This can:
  - **Reflect reality** (higher exposure where activity is highest).
  - **Reinforce** prioritization of already-burdened neighborhoods if used only for “efficiency” (e.g. routing more trucks) without equity criteria.
- **Mitigation**: Use the platform to **highlight** disproportionate exposure and to inform **reduction** of emissions and traffic (e.g. cleaner fleet, off-peak routing, last-mile alternatives), not only to optimize logistics. Pair with health and equity indicators in planning.

## Data reliability

- **NYC Open Data**: Official but may have gaps, latency, or sensor issues; preliminary data may change.
- **OSMnx**: OpenStreetMap can be incomplete or outdated; truck restrictions or road types may be wrong.
- **Proxies**: Noise and congestion are **modeled**, not measured; clearly labeled. Do not treat as verified measurements.

## Transparency of models

- **Documentation**: [MODELS.md](MODELS.md) describes how pollution, noise proxy, congestion, and exposure index are computed.
- **In product**: Tooltips and layer metadata show `data_type` (e.g. observed vs proxy) and short notes (e.g. `congestion_note`, `noise_note`).
- **Weights**: Exposure index weights (0.5, 0.3, 0.2) are illustrative; document any change when used for policy.

## Ethical use of routing insights

- **Routing**: Identifying high-density truck corridors and bottlenecks can be used to:
  - **Reduce** through-traffic in residential areas and improve air quality.
  - **Improve** freight efficiency only if coupled with emission and health constraints.
- **Recommendation**: Do not use the platform solely to minimize travel time or cost if it increases exposure in already overburdened areas. Prefer routing and policy that **reduce** cumulative exposure and support environmental justice goals.
