#!/usr/bin/env python3
"""
Urban Mobility Decision Intelligence — Dashboard

Two modes:
1. Driver View — Zone recommendation for individual drivers
2. Fleet Operations — Fleet-wide KPIs, heatmaps, supply-demand monitoring

Usage:
    streamlit run app/app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    import streamlit as st
except ImportError:
    print("Streamlit not installed. Install with: pip install streamlit")
    sys.exit(1)

import numpy as np
import pandas as pd

ZONE_LOOKUP = {
    237: "Upper East Side North", 236: "Upper East Side South",
    170: "Murray Hill", 161: "Midtown Center",
    224: "Upper West Side South", 162: "Midtown East",
    163: "Midtown West", 48: "Times Square",
    90: "Chelsea", 100: "East Village",
    132: "JFK Airport", 138: "LaGuardia Airport",
    4: "Newark Airport", 140: "South Bronx",
    79: "West Village", 107: "Upper West Side North",
    113: "Lower East Side", 114: "Greenwich Village North",
    186: "Park Slope", 230: "Williamsburg (North Side)",
    234: "Greenpoint", 249: "DUMBO/Vinegar Hill",
    164: "Financial District North",
}
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _generate_fleet_kpis(seed=42):
    """Generate demo fleet KPIs from historical statistics (SIMULATION ONLY)."""
    rng = np.random.RandomState(seed)
    n_zones = len(ZONE_LOOKUP)
    zones = list(ZONE_LOOKUP.keys())
    hour_demand = {z: max(0, rng.poisson(20 - abs(12 - z % 24) * 1.5)) for z in zones}
    total_demand = sum(hour_demand.values())
    fleet_size = 100
    active = fleet_size - rng.randint(5, 20)
    idle = fleet_size - active
    supply_demand_ratio = round(total_demand / max(1, active), 2)
    return {
        "fleet_size": fleet_size, "active_vehicles": active, "idle_vehicles": idle,
        "utilization": round(rng.uniform(0.10, 0.20), 3),
        "predicted_demand": total_demand,
        "supply_demand_ratio": supply_demand_ratio,
        "avg_expected_revenue": round(rng.uniform(20, 35), 2),
        "avg_empty_distance": round(rng.uniform(1.5, 4.0), 2),
        "zone_demand": hour_demand,
        "zone_supply": {z: rng.randint(0, 8) for z in zones},
    }


def _render_zone_labels(zone_ids):
    return [f"{zid} — {ZONE_LOOKUP.get(zid, 'Zone '+str(zid))}" for zid in zone_ids]


def main():
    st.set_page_config(
        page_title="Urban Mobility Decision Intelligence",
        page_icon="\U0001f695",
        layout="wide",
    )
    st.title("\U0001f695 Urban Mobility Decision Intelligence")
    st.caption(
        "DEMO / SIMULATION — Results use pre-computed historical statistics. "
        "Not real-time NYC taxi data."
    )

    mode = st.sidebar.radio("Dashboard Mode", ["Driver View", "Fleet Operations"])

    if mode == "Driver View":
        _render_driver_view()
    else:
        _render_fleet_ops()


def _render_driver_view():
    st.header("Driver Zone Recommendation")
    st.markdown(
        "Get a zone recommendation for a single vehicle. "
        "Results are **simulation-based**."
    )
    zone_ids = sorted(ZONE_LOOKUP.keys())
    zone_options = {f"{zid} — {ZONE_LOOKUP[zid]}": zid for zid in zone_ids}
    selected = st.sidebar.selectbox("Current Zone", list(zone_options.keys()), index=0)
    zone_id = zone_options[selected]
    hour = st.sidebar.slider("Hour", 0, 23, 14)
    day_name = st.sidebar.selectbox("Day", DAY_NAMES, index=2)

    # Simulated recommendation
    rng = np.random.RandomState(zone_id * 100 + hour)
    top_candidates = rng.choice(zone_ids, size=min(10, len(zone_ids)), replace=False)
    top3 = list(top_candidates[:3])
    scores = [round(rng.uniform(0.7, 0.99), 3) for _ in range(3)]
    demands = [max(0, rng.poisson(30)) for _ in range(3)]
    revenues = [round(rng.uniform(15, 45), 2) for _ in range(3)]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Current State")
        st.metric("Zone", f"{zone_id} — {ZONE_LOOKUP.get(zone_id, 'Unknown')}")
        st.metric("Time", f"{hour:02d}:00, {day_name}")
        st.metric("Active Drivers Nearby", rng.randint(3, 15))
        st.metric("Est. Wait Time", f"{rng.uniform(2, 12):.1f} min")

    with col2:
        st.subheader("\U0001f3c6 Top-3 Recommendations")
        for i in range(3):
            zid = top3[i]
            zname = ZONE_LOOKUP.get(zid, f"Zone {zid}")
            with st.container():
                st.markdown(f"**#{i+1} {zid} — {zname}**")
                c1, c2, c3 = st.columns(3)
                c1.metric("Score", f"{scores[i]:.3f}")
                c2.metric("Est. Demand", str(demands[i]))
                c3.metric("Est. Revenue", f"${revenues[i]:.2f}")

    st.divider()
    st.caption(
        "DISCLAIMER: Simulation-based demo. Results are not production evidence. "
        "All outputs use pre-computed historical statistics."
    )


def _render_fleet_ops():
    st.header("\U0001f4ca Fleet Operations Dashboard")
    st.markdown(
        "Fleet-wide monitoring view. All data is **SIMULATION / HISTORICAL REPLAY**."
    )

    kpis = _generate_fleet_kpis(42)

    # KPI Row
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("\U0001f698 Fleet Size", kpis["fleet_size"])
    c2.metric("\U0001f7e2 Active", kpis["active_vehicles"], delta=f"-{kpis['idle_vehicles']} idle")
    c3.metric("\U0001f4c8 Utilization", f"{kpis['utilization']:.1%}")
    c4.metric("\U0001f4c5 Predicted Demand", kpis["predicted_demand"])
    c5.metric("\U0001f4ca Supply/Demand", kpis["supply_demand_ratio"])

    st.divider()

    # Heatmaps (simulated)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("\U0001f525 Demand Heatmap")
        zones = list(ZONE_LOOKUP.keys())
        demand_data = pd.DataFrame({
            "Zone": _render_zone_labels(zones),
            "Demand": [kpis["zone_demand"][z] for z in zones],
        }).sort_values("Demand", ascending=False).head(15)
        st.bar_chart(demand_data.set_index("Zone"))

    with c2:
        st.subheader("\U0001f6d1 Supply Heatmap")
        supply_data = pd.DataFrame({
            "Zone": _render_zone_labels(zones),
            "Supply": [kpis["zone_supply"][z] for z in zones],
        }).sort_values("Supply", ascending=False).head(15)
        st.bar_chart(supply_data.set_index("Zone"))

    # Recommendations table
    st.subheader("\U0001f4cb Fleet Recommendations")
    rec_data = []
    rng = np.random.RandomState(42)
    for v in range(min(10, kpis["fleet_size"])):
        z = rng.choice(zones)
        top_z = rng.choice(zones)
        rec_data.append({
            "Vehicle": f"v{v:03d}",
            "Current Zone": f"{z} — {ZONE_LOOKUP.get(z, '?')}",
            "Recommended Zone": f"{top_z} — {ZONE_LOOKUP.get(top_z, '?')}",
            "Est. Revenue": f"${rng.uniform(15, 45):.2f}",
            "Confidence": f"{rng.uniform(0.70, 0.95):.2f}",
        })
    st.dataframe(pd.DataFrame(rec_data), use_container_width=True)

    # Info box
    st.divider()
    st.info(
        "Model: Two-Step Horizon (v1)  |  Data Timestamp: 2023-01-25  |  "
        "Source: SIMULATION / HISTORICAL REPLAY  |  "
        "Not real-time NYC taxi data"
    )


if __name__ == "__main__":
    main()
