# -*- coding: utf-8 -*-
"""Extension 2: Interactive Recommendation System with Data Analysis."""
from __future__ import annotations
import csv, os
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ZONE_COUNT = 263; SLOT_COUNT = 48
STATISTICS_PATH = PROJECT_ROOT / "data/processed/zone_time_statistics.parquet"
TRAVEL_TIME_PATH = PROJECT_ROOT / "data/processed/travel_time_matrix_dijkstra.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
WD_NAMES = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def load_statistics():
    demand = [[[0.0]*ZONE_COUNT for _ in range(SLOT_COUNT)] for _ in range(7)]
    mean_fare = [[[0.0]*ZONE_COUNT for _ in range(SLOT_COUNT)] for _ in range(7)]
    cols = ["pickup_location_id","weekday","time_slot","pickup_count","mean_fare_amount"]
    for row in pq.read_table(STATISTICS_PATH, columns=cols).to_pylist():
        loc = int(row["pickup_location_id"]) - 1
        wd = int(row["weekday"]); ts = int(row["time_slot"])
        if 0 <= loc < ZONE_COUNT:
            demand[wd][ts][loc] = float(row["pickup_count"])
            rf = row["mean_fare_amount"]
            if rf is not None and np.isfinite(float(rf)):
                mean_fare[wd][ts][loc] = max(0.0, float(rf))
    return demand, mean_fare

def load_travel_time():
    with TRAVEL_TIME_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f); next(reader)
        return [[float(v) for v in row[1:]] for row in reader]

def load_zone_info():
    path = PROJECT_ROOT / "data/meta/taxi_zone_lookup.csv"
    if not path.exists(): return {}
    info = {}
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            info[int(row["LocationID"])] = {"borough": row["Borough"], "zone": row["Zone"]}
    return info

def _next_half_hour(dt):
    start = dt.replace(minute=(dt.minute // 30) * 30, second=0, microsecond=0)
    return start + timedelta(minutes=30)

def baseline_2_recommend(dt, loc, demand, mf, tt):
    target = _next_half_hour(dt)
    slot = target.hour * 2 + target.minute // 30; wd = target.weekday()
    times = tt[loc - 1]
    scores = [demand[wd][slot][j] * mf[wd][slot][j] / (times[j] + 1.0) if np.isfinite(times[j]) else 0.0 for j in range(ZONE_COUNT)]
    ordered = sorted(range(1, ZONE_COUNT + 1), key=lambda z: (-scores[z - 1], z))
    return ordered[:3]

def improved_recommend(dt, loc, demand, mf, tt):
    ZC=ZONE_COUNT; SC=SLOT_COUNT; WSC=7*SC; origin=loc-1
    target=_next_half_hour(dt); slot=target.hour*2+target.minute//30; wd=target.weekday(); state=wd*SC+slot
    times=tt[origin]
    base=[demand[wd][slot][j]*mf[wd][slot][j]/(times[j]+1.0) if np.isfinite(times[j]) and times[j]>=0 else 0.0 for j in range(ZC)]
    ordered=sorted(range(ZC), key=lambda z: (-base[z], z)); candidates=set(ordered[:50]); candidates.add(origin)
    arr_slots=[state if j==origin else ((state+int(np.floor(times[j]/30.0+0.5)))%WSC if np.isfinite(times[j]) and times[j]>=0 else -1) for j in range(ZC)]
    two_step=list(base)
    for z in candidates:
        if arr_slots[z]<0: continue
        arr=arr_slots[z]; aw=arr//SC; a_s=arr%SC
        d=demand[aw][a_s][z]; p=d/(d+240.0) if d>0 else 0.0; f=mf[aw][a_s][z]
        nf=(arr+1)%WSC; nw=nf//SC; ns=nf%SC
        d3=demand[nw][ns][z]; vf=d3/(d3+240.0)*mf[nw][ns][z] if d3>0 else 0.0
        u=p*f+(1-p)*0.5*vf
        mc=0.0 if z==origin else tt[origin][z]
        if np.isfinite(mc) and mc>=0: two_step[z]=u/(int(np.floor(mc/30.0+0.5))+1.0)
        else: two_step[z]=0.0
    final=sorted(range(1,ZC+1), key=lambda z: (-two_step[z-1], z))
    return final[:3]

# --- Charts ---

def _plot_demand_by_time(demand, output_dir):
    slot_total = [sum(demand[wd][ts][z] for wd in range(7) for z in range(ZONE_COUNT)) for ts in range(SLOT_COUNT)]
    fig, ax = plt.subplots(figsize=(12, 4))
    hours = [f"{ts//2:02d}:{str((ts%2)*30).zfill(2)}" for ts in range(SLOT_COUNT)]
    colors = ["#e74c3c" if 32 <= ts <= 40 else "#3498db" for ts in range(SLOT_COUNT)]
    ax.bar(range(SLOT_COUNT), slot_total, color=colors, width=0.8)
    ax.set_xticks(range(0, SLOT_COUNT, 4))
    ax.set_xticklabels([hours[i] for i in range(0, SLOT_COUNT, 4)], rotation=45, fontsize=8)
    ax.set_title("NYC Taxi Demand by Time of Day")
    ax.set_ylabel("Total Pickup Demand")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "chart_demand_by_time.png"), dpi=120)
    plt.close(fig)
    print("  [OK] chart_demand_by_time.png")

def _plot_demand_by_weekday(demand, output_dir):
    wd_total = [sum(demand[wd][ts][z] for ts in range(SLOT_COUNT) for z in range(ZONE_COUNT)) for wd in range(7)]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(WD_NAMES, wd_total, color=["#3498db"]*5 + ["#e67e22"]*2)
    for i, v in enumerate(wd_total):
        ax.text(i, v + 5000, f"{v/1000:.0f}k", ha="center", fontsize=9)
    ax.set_ylabel("Total Pickup Demand")
    ax.set_title("NYC Taxi Demand by Day of Week")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "chart_demand_by_weekday.png"), dpi=120)
    plt.close(fig)
    print("  [OK] chart_demand_by_weekday.png")

def _plot_top_zones(demand, output_dir, zone_info):
    zone_total = [sum(demand[wd][ts][z] for wd in range(7) for ts in range(SLOT_COUNT)) for z in range(ZONE_COUNT)]
    top = sorted(range(ZONE_COUNT), key=lambda z: -zone_total[z])[:15]
    labels = [zone_info.get(z+1, {}).get("zone", f"Zone {z+1}")[:20] for z in top]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(range(15), [zone_total[z] for z in top][::-1], color="#2ecc71")
    ax.set_yticks(range(15))
    ax.set_yticklabels(labels[::-1], fontsize=8)
    ax.set_title("Top 15 Zones by Total Demand")
    ax.set_xlabel("Total Pickup Demand")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "chart_top_zones.png"), dpi=120)
    plt.close(fig)
    print("  [OK] chart_top_zones.png")

def _plot_fare_distribution(demand, mf, output_dir):
    fares = [mf[wd][ts][z] for wd in range(7) for ts in range(SLOT_COUNT) for z in range(ZONE_COUNT) if demand[wd][ts][z]>0 and mf[wd][ts][z]>0]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(fares, bins=50, color="#9b59b6", alpha=0.7, edgecolor="white")
    ax.set_xlabel("Mean Fare Amount ($)")
    ax.set_ylabel("Frequency")
    ax.set_title("Distribution of Mean Fare")
    mn = np.mean(fares)
    ax.axvline(mn, color="red", linestyle="--", label=f"Mean: ${mn:.2f}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "chart_fare_distribution.png"), dpi=120)
    plt.close(fig)
    print("  [OK] chart_fare_distribution.png")

def generate_all_charts(demand, mf, output_dir, zinfo):
    os.makedirs(output_dir, exist_ok=True)
    _plot_demand_by_time(demand, output_dir)
    _plot_demand_by_weekday(demand, output_dir)
    _plot_top_zones(demand, output_dir, zinfo)
    _plot_fare_distribution(demand, mf, output_dir)
    print("Charts in:", output_dir)

# --- Interactive CLI ---

def _show_recommendation(sname, top3, dt, loc, demand, mf, tt, zinfo):
    target = _next_half_hour(dt)
    slot = target.hour * 2 + target.minute // 30; wd = target.weekday()
    print(f"  [{sname}]")
    for rank, z in enumerate(top3, 1):
        idx = z - 1; d = demand[wd][slot][idx]; f = mf[wd][slot][idx]; t = tt[loc - 1][idx]
        info = zinfo.get(z, {}); zn = info.get("zone", f"Zone {z}"); bo = info.get("borough", "")
        ts = f"{t:.1f}min" if np.isfinite(t) and t >= 0 else "N/A"
        print(f"    #{rank}: Zone {z} ({zn})")
        print(f"         Borough: {bo}")
        print(f"         Demand: {d:.0f} | Fare: ${f:.2f} | Travel: {ts}")

def _interactive_loop(demand, mf, tt, zinfo):
    print("=" * 60)
    print("  Interactive Recommendation System")
    print("  Enter q to quit, charts to regenerate")
    print("=" * 60)
    print("Example: datetime=2023-01-30 08:15, zone=132\n")
    while True:
        try:
            dt_str = input("  Enter datetime (YYYY-MM-DD HH:MM): ").strip()
            if dt_str.lower() in ("q", "quit", "exit"): break
            if dt_str.lower() == "charts":
                generate_all_charts(demand, mf, OUTPUT_DIR / "extension_2_charts", zinfo)
                continue
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            loc_str = input("  Enter location ID (1-263): ").strip()
            if loc_str.lower() in ("q", "quit", "exit"): break
            loc = int(loc_str)
            if not 1 <= loc <= ZONE_COUNT: print("  [ERROR] Location ID must be 1-263"); continue
            print()
            slot = dt.hour * 2 + dt.minute // 30
            print(f"  Current: {dt.strftime("%Y-%m-%d %H:%M")} (WD={dt.weekday()}, Slot={slot})")
            zn = zinfo.get(loc, {}).get("zone", "Unknown")
            print(f"  Location: Zone {loc} ({zn})")
            top3_b2 = baseline_2_recommend(dt, loc, demand, mf, tt)
            top3_imp = improved_recommend(dt, loc, demand, mf, tt)
            _show_recommendation("Baseline 2 (Single-step)", top3_b2, dt, loc, demand, mf, tt, zinfo)
            print()
            _show_recommendation("Improved (Two-step)", top3_imp, dt, loc, demand, mf, tt, zinfo)
            print("-" * 60)
        except ValueError as e: print(f"  [ERROR] {e}")
        except KeyboardInterrupt: print(); break
    print("  Goodbye!")

def main():
    print("Loading data...")
    demand, mf = load_statistics(); tt = load_travel_time(); zinfo = load_zone_info()
    total_pk = sum(sum(d) for wd in demand for ts in wd for d in ts)
    print(f"  Statistics: {total_pk:.0f} total pickups in {len(tt)}x{len(tt[0])} matrix")
    generate_all_charts(demand, mf, OUTPUT_DIR / "extension_2_charts", zinfo)
    _interactive_loop(demand, mf, tt, zinfo)

if __name__ == "__main__":
    main()