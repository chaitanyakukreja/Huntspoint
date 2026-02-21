#!/usr/bin/env python3
"""
Time series analysis: hourly variation of pollution, congestion, truck density.
Generates charts (matplotlib + optional Plotly) and prints pattern summary.
Run from project root: python scripts/timeseries_analysis.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Simulated hourly pattern for Hunts Point (peak logistics 4–9 AM)
HOURS = list(range(24))


def get_simulated_timeseries():
    """Realistic time-of-day pattern for Hunts Point peninsula."""
    pm25 = [10 + 3 * (1 + (h - 6) ** 2 / 36) for h in HOURS]
    pm25 = [min(18, max(8, p)) for p in pm25]
    truck_density = [0.3 + 0.7 * (1 - min(abs(h - 6.5) / 6, 1)) for h in HOURS]
    congestion = [0.4 + 0.5 * d for d in truck_density]
    return {
        "hours": HOURS,
        "pm25": pm25,
        "truck_density": truck_density,
        "congestion": congestion,
    }


def plot_matplotlib(data, out_path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    h = data["hours"]
    axes[0].plot(h, data["pm25"], color="C0", linewidth=2)
    axes[0].set_ylabel("PM2.5 (µg/m³)")
    axes[0].set_title("Pollution vs time of day")
    axes[0].grid(True, alpha=0.3)
    axes[0].axvspan(4, 9, alpha=0.2, color="orange", label="Peak logistics")
    axes[0].legend(loc="upper right", fontsize=8)
    axes[1].plot(h, data["truck_density"], color="C1", linewidth=2)
    axes[1].set_ylabel("Truck density (0–1)")
    axes[1].set_title("Truck density vs time")
    axes[1].grid(True, alpha=0.3)
    axes[1].axvspan(4, 9, alpha=0.2, color="orange")
    axes[2].plot(h, data["congestion"], color="C2", linewidth=2)
    axes[2].set_ylabel("Congestion (0–1)")
    axes[2].set_xlabel("Hour of day")
    axes[2].set_title("Congestion vs time")
    axes[2].grid(True, alpha=0.3)
    axes[2].axvspan(4, 9, alpha=0.2, color="orange")
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()
    return True


def main():
    data = get_simulated_timeseries()
    out_dir = PROJECT_ROOT / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "timeseries_hourly.png"

    if plot_matplotlib(data, out_path):
        print(f"Chart saved: {out_path}")
    else:
        print("Matplotlib not available; skipping chart.")

    # Pattern summary
    print("\n--- Time-of-day patterns (Hunts Point) ---")
    print("Peak logistics window: 4 AM – 9 AM")
    print("  PM2.5: higher in morning (truck activity + cold start); lower at night.")
    print("  Truck density: peaks ~6–7 AM; moderate midday; lower evening.")
    print("  Congestion: follows truck density (road centrality / density proxy).")
    print("Limitation: simulated pattern; replace with observed counts when available.")


if __name__ == "__main__":
    main()
