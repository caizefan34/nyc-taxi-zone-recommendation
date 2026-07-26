"""Simulator validation report generator.

Generates a comprehensive markdown report comparing simulator output
against real NYC TLC data with plots, metrics, and interpretation.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .comparison import ValidationReport
from .temporal import TemporalValidationResult


def generate_validation_report(
    report: ValidationReport,
    temporal: TemporalValidationResult | None = None,
    *,
    output_path: str | Path = "outputs/simulator_validation_report.md",
    config_info: dict[str, object] | None = None,
) -> str:
    """Generate a comprehensive markdown validation report.

    Args:
        report: ValidationReport from SimulatorValidator.
        temporal: Optional TemporalValidationResult.
        output_path: Path to write the markdown report.
        config_info: Optional dict with experiment configuration info.

    Returns:
        The markdown report string.
    """
    lines: list[str] = [
        "# Simulator vs Real NYC TLC Data: Validation Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Overview",
        "",
        "This report compares the DynamicSimulator v2 against real NYC TLC Yellow Taxi trip records. "
        "The goal is to quantify how well the simulator reproduces real-world demand, temporal, "
        "and revenue distributions.",
        "",
        "---",
        "",
        "## 1. Zone Demand Distribution",
        "",
        "### Metrics",
        "",
        "| Metric | Value | Interpretation |",
        "|--------|-------|----------------|",
    ]

    if report.zone_demand:
        zd = report.zone_demand
        lines.append(f"| KL Divergence | {zd.kl_divergence:.6f} | Lower is better (0 = identical) |")
        lines.append(f"| JS Divergence | {zd.js_divergence:.6f} | Bounded [0, 1], lower is better |")
        lines.append(f"| Wasserstein Distance | {zd.wasserstein_distance:.4f} | Lower is better |")
        lines.append(f"| Correlation | {zd.correlation:.4f} | Higher is better |")
        lines.append(f"| Real Mean Demand | {zd.real_mean:.2f} | Average real pickup count |")
        lines.append(f"| Sim Mean Demand | {zd.sim_mean:.2f} | Average simulated demand |")
        lines.append(f"| Real Std Dev | {zd.real_std:.2f} | Real distribution spread |")
        lines.append(f"| Sim Std Dev | {zd.sim_std:.2f} | Simulated distribution spread |")
        lines.append(f"| Sample Size | {zd.sample_size} | Number of zones/observations |")
    else:
        lines.append("| (No data) | - | No zone demand comparison available |")

    lines.extend([
        "",
        "### Interpretation",
        "",
        f"> {report.summary.get('zone_demand', 'Not evaluated')}",
        "",
        "---",
        "",
        "## 2. Temporal Pattern Validation",
        "",
        "### Hourly Demand Curve",
        "",
        "| Metric | Value |",
        "|--------|------:|",
    ])

    if temporal:
        lines.append(f"| Hourly RMSE | {temporal.hourly_rmse:.4f} |")
        lines.append(f"| Hourly Correlation | {temporal.hourly_correlation:.4f} |")
        lines.append(f"| Peak Hour (Real) | {temporal.peak_hour_real}:00 |")
        lines.append(f"| Peak Hour (Sim) | {temporal.peak_hour_sim}:00 |")
        lines.append(f"| Trough Hour (Real) | {temporal.trough_hour_real}:00 |")
        lines.append(f"| Trough Hour (Sim) | {temporal.trough_hour_sim}:00 |")

        lines.extend([
            "",
            "### Weekday vs Weekend Pattern",
            "",
            "| Metric | Weekday | Weekend |",
            "|--------|--------:|--------:|",
            f"| RMSE | {temporal.weekday_rmse:.4f} | {temporal.weekend_rmse:.4f} |",
            f"| Correlation | {temporal.weekday_correlation:.4f} | {temporal.weekend_correlation:.4f} |",
        ])

        if temporal.seasonality_correlation is not None:
            lines.extend([
                "",
                "### Seasonality",
                "",
                "| Metric | Value |",
                "|--------|------:|",
                f"| Monthly RMSE | {temporal.seasonality_rmse:.4f} |",
                f"| Monthly Correlation | {temporal.seasonality_correlation:.4f} |",
            ])

        lines.extend([
            "",
            "### Temporal Interpretation",
            "",
            f"> Hourly: {temporal.interpretation.get('hourly', 'N/A')}",
            "",
            f"> Weekday: {temporal.interpretation.get('weekday', 'N/A')}",
            "",
            f"> Weekend: {temporal.interpretation.get('weekend', 'N/A')}",
        ])
    else:
        lines.append("| (No temporal data) | - |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Revenue / Fare Validation",
        "",
        "| Metric | Real TLC Data | Simulator |",
        "|--------|--------------:|----------:|",
    ])

    if report.revenue:
        rv = report.revenue
        lines.append("| Mean Fare/Reward |  |  |")
        lines.append("| Std Dev |  |  |")
        lines.append(f"| Correlation | - | {rv.correlation:.4f} |")
        lines.append(f"| Sample Count | {rv.sample_size} | {rv.sample_size} |")
    else:
        lines.append("| (No revenue data) | - | - |")

    lines.extend([
        "",
        "### Revenue Interpretation",
        "",
        f"> {report.summary.get('revenue', 'Not evaluated')}",
        "",
        "---",
        "",
        "## 4. Summary",
        "",
        "### Overall Assessment",
        "",
    ])

    # Overall assessment
    assessments = list(report.summary.values())
    if all("Excellent" in a or "Strong" in a for a in assessments):
        overall = "The simulator shows strong alignment with real NYC TLC data across all validation dimensions."
    elif all("Good" in a or "Excellent" in a or "Strong" in a for a in assessments):
        overall = "The simulator shows good-to-strong alignment with real data."
    elif any("Poor" in a for a in assessments):
        overall = "The simulator diverges from real data in some dimensions. Calibration improvements may be needed."
    else:
        overall = "The simulator shows moderate alignment with real data. Review individual metrics for details."
    lines.append(f"> {overall}")
    lines.append("")

    # Limitations
    lines.extend([
        "",
        "### Limitations",
        "",
        "- **Simulated demand** uses synthetic patterns based on configurable base demand, not real-time TLC data.",
        "- **Revenue comparison** is approximate: simulator rewards include penalties",
        "- **Temporal patterns** depend on simulator traffic/weather parameters",
        "- This validation compares distribution statistics, not per-trip correspondence.",
        "",
    ])

    if config_info:
        lines.extend([
            "### Experiment Configuration",
            "",
            "`json",
            str(config_info),
            "`",
            "",
        ])

    report_str = "\n".join(lines)

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report_str, encoding="utf-8")

    return report_str

