#!/usr/bin/env python3
"""
Streamlit web demo for NYC Taxi Zone Recommendation.

Usage:
    streamlit run app/app.py

This demo calls into the existing pipeline (scripts/run_live_demo.py).
No model training required — uses pre-computed fallbacks.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    import streamlit as st
except ImportError:
    print("Streamlit not installed. Install with: pip install streamlit")
    print("Then run: streamlit run app/app.py")
    sys.exit(1)
from scripts.run_live_demo import build_features, forecast_demand, recommend_policy, simulate_state

ZONE_LOOKUP = {
    237: "Upper East Side North",
    236: "Upper East Side South",
    170: "Murray Hill",
    161: "Midtown Center",
    224: "Upper West Side South",
    162: "Midtown East",
    163: "Midtown West",
    48: "Times Square",
    90: "Chelsea",
    100: "East Village",
}
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
def main():
    st.set_page_config(
        page_title="NYC Taxi Zone Recommendation",
        page_icon="\U0001f695",
        layout="wide",
    )
    st.title("\U0001f695 NYC Taxi Zone Recommendation Demo")
    st.markdown(
        "Interactive demo of the zone recommendation pipeline. "
        "Results are **simulation-based** and do not reflect real-world deployment."
    )
    st.sidebar.header("Input Parameters")
    zone_ids = sorted(ZONE_LOOKUP.keys())
    zone_options = {"{} — {}".format(zid, ZONE_LOOKUP[zid]): zid for zid in zone_ids}
    selected_zone_label = st.sidebar.selectbox(
        "Current Zone", list(zone_options.keys()), index=0
    )
    zone_id = zone_options[selected_zone_label]
    hour = st.sidebar.slider("Hour of Day", 0, 23, 14)
    day_name = st.sidebar.selectbox("Day of Week", DAY_NAMES, index=2)
    month = st.sidebar.slider("Month", 1, 12, 7)
    day_map = {name.lower(): i for i, name in enumerate(DAY_NAMES)}
    day_of_week = day_map.get(day_name.lower(), 2)
    features = build_features(zone_id, hour, day_of_week, month)
    forecast = forecast_demand(features)
    sim_state = simulate_state(zone_id, forecast)
    policy = recommend_policy(zone_id, sim_state)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("\U0001f4cd Current State")
        zname = ZONE_LOOKUP.get(zone_id, "Unknown")
        st.metric("Zone", "{} \u2014 {}".format(zone_id, zname))
        st.metric("Time", "{:02d}:00, {}".format(hour, day_name))
        st.subheader("\U0001f4ca Simulator State")
        st.metric("Utilization", "{:.0%}".format(sim_state["utilization"]))
        st.metric("Active Drivers", sim_state["active_drivers"])
        st.metric("Idle Drivers", sim_state["idle_drivers"])
        if "estimated_wait_minutes" in sim_state:
            st.metric("Est. Wait", "{:.1f} min".format(sim_state["estimated_wait_minutes"]))
    with col2:
        st.subheader("\U0001f52e Demand Forecast")
        st.metric("Predicted Pickups", forecast["predicted_pickups"])
        if "confidence_lower" in forecast:
            col_l, col_r = st.columns(2)
            col_l.metric("CI Lower", forecast["confidence_lower"])
            col_r.metric("CI Upper", forecast["confidence_upper"])
        st.caption("Model: {}".format(forecast.get("model", "fallback")))
        st.subheader("\U0001f3c6 Top-3 Recommendations")
        recs = policy["recommendations"]
        for i, rec in enumerate(recs):
            zone_name = ZONE_LOOKUP.get(rec["zone_id"], "Zone {}".format(rec["zone_id"]))
            with st.container():
                st.markdown("**#{} {}**".format(i+1, zone_name))
                c1, c2 = st.columns(2)
                c1.metric("Expected Reward", "${:.1f}".format(rec["expected_reward"]))
                if "pickup_prob" in rec:
                    c2.metric("Pickup Prob", "{:.0%}".format(rec["pickup_prob"]))
        st.subheader("\U0001f4b5 Overall")
        st.metric("Best Expected Reward", "${:.1f}".format(policy["expected_reward"]))
        st.metric("Strategy", policy["strategy"])
    with st.expander("Pipeline Details"):
        st.json({
            "input": {"zone_id": zone_id, "hour": hour, "day": day_name, "month": month},
            "forecast": forecast,
            "simulator": sim_state,
            "recommendation": policy,
        })
    st.divider()
    st.caption(
        "\u26a0\ufe0f **Disclaimer:** This demo uses simulation-based inference with pre-computed "
        "statistics. Results are for research demonstration only and do not represent "
        "real-world deployment performance. See [docs/live_demo.md](docs/live_demo.md) "
        "for more information."
    )
if __name__ == "__main__":
    main()
