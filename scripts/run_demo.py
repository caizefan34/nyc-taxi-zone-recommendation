"""Demo workflow: zone recommendation pipeline."""
import json
from pathlib import Path


def demo_pipeline():
    """Run demo using pre-computed benchmark results."""
    outputs_dir = Path(__file__).resolve().parent.parent / "outputs"
    fe = json.load(open(outputs_dir / "forecast_evaluation.json"))
    ma = json.load(open(outputs_dir / "multi_agent_benchmark.json"))
    br = json.load(open(outputs_dir / "benchmark_report.json"))

    emae = fe["ensemble"]["demand_mae"]
    lmae = fe["demand"]["lightgbm_mae"]
    hmae = fe["demand"]["historical_mae"]
    srev = ma["strategies"]["single_step"]["average_driver_revenue"]
    hrev = ma["strategies"]["hot_zone"]["average_driver_revenue"]
    trev = ma["strategies"]["two_step"]["average_driver_revenue"]
    drev = br["methods"]["dqn"]["revenue_per_driver"]
    ddrev = br["methods"]["double_dqn"]["revenue_per_driver"]
    ddif = br["methods"]["dqn"]["difference_vs_original"]["mean_difference"]
    dp = br["methods"]["dqn"]["difference_vs_original"]["paired_t_pvalue"]

    pct = (1 - emae/hmae)*100
    print("=== Step 1: Demand Prediction ===")
    print("  Historical Average MAE: {:.3f}".format(hmae))
    print("  LightGBM MAE:           {:.3f}".format(lmae))
    print("  Ensemble MAE:           {:.3f}".format(emae))
    print("  Improvement:            {:.1f}%".format(pct))
    print()
    print("=== Step 2: Simulator (50 drivers, 7 days) ===")
    fstr = "  Hot Zone:      ${:.0f}/driver"
    print(fstr.format(hrev))
    fstr = "  Two-Step:      ${:.0f}/driver"
    print(fstr.format(trev))
    fstr = "  Single-Step:   ${:.0f}/driver"
    print(fstr.format(srev))
    print()
    print("=== Step 3: Policy Recommendation ===")
    fstr = "  DQN Revenue:         ${:.0f}/driver"
    print(fstr.format(drev))
    fstr = "  Double DQN Revenue:  ${:.0f}/driver"
    print(fstr.format(ddrev))
    fstr = "  DQN vs Single-Step:  +${:.0f}/driver (p={:.2e})"
    print(fstr.format(ddif, dp))
    if dp < 0.05:
        print("  >>> Statistical significance achieved (p < 0.05)")
    print("  >> Recommended Policy: DQN")
    fstr = "  >> Expected Revenue:  ${:.0f}/driver/week"
    print(fstr.format(drev))

    result = {
        "demo_version": "2.0.0",
        "demand_prediction": {"historical_mae": hmae, "lightgbm_mae": lmae, "ensemble_mae": emae, "improvement_pct": round(pct, 1)},
        "simulator": {"hot_zone_revenue": round(hrev,2), "two_step_revenue": round(trev,2), "single_step_revenue": round(srev,2)},
        "recommendation": {"recommended_policy": "DQN", "expected_revenue_per_driver": round(drev,2), "dqn_revenue": round(drev,2)},
        "disclaimer": "Uses pre-computed results. Full training needs NYC TLC data (~10GB).",
    }
    d = outputs_dir / "demo"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "demo_result.json"
    with open(p, "w") as f:
        json.dump(result, f, indent=2)
    print("Demo output saved to: {}".format(p))
    return result


if __name__ == "__main__":
    print("=" * 55)
    print("  Dynamic Urban Mobility Decision System")
    print("  Demo Workflow v2.0.0")
    print("=" * 55)
    print()
    demo_pipeline()