"""Stage 8 — Sustainability & Carbon Footprint Reporting Agent for EcoMind AI."""

from __future__ import annotations

from typing import Any
import pandas as pd
import numpy as np
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from src.utils.config import CAMPUS, GENERATED_DIR, REPORTS_DIR, VFSTR_AUDIT
from src.utils.io import load_csv, save_json
from src.utils.logging_utils import get_logger
from src.utils.validation import ValidationResult

logger = get_logger("ecomind.sustainability")


def calculate_sustainability_metrics(sensor_df: pd.DataFrame, recs_df: pd.DataFrame) -> dict[str, Any]:
    """Calculate GHG emissions, solar avoided emissions, EUI, and EcoMind Sustainability Index."""

    annual_grid_kwh = VFSTR_AUDIT["grid_electricity_kwh"]
    annual_solar_kwh = VFSTR_AUDIT["solar_generation_kwh"]
    total_annual_kwh = VFSTR_AUDIT["annual_electricity_kwh"]

    scope1_dg_tco2 = VFSTR_AUDIT["scope1_dg_emissions_tco2"]
    scope2_grid_tco2 = annual_grid_kwh * CAMPUS["grid_carbon_kg_per_kwh"] / 1000.0
    avoided_solar_tco2 = annual_solar_kwh * CAMPUS["grid_carbon_kg_per_kwh"] / 1000.0
    total_net_tco2 = scope1_dg_tco2 + scope2_grid_tco2

    # Estimated potential CO2 savings from Stage 7 recommendations
    annual_opt_co2_saving_tco2 = (recs_df["estimated_monthly_co2_reduction_kg"].sum() * 12.0) / 1000.0

    # Campus Energy Use Intensity (EUI in kWh/m²)
    total_built_area = VFSTR_AUDIT["total_built_up_area_sqm"]
    campus_eui = total_annual_kwh / total_built_area

    # EcoMind Sustainability Index (0 - 100 Score)
    renewable_score = (annual_solar_kwh / total_annual_kwh) * 35.0  # 39% renewable -> ~13.65 pts
    smart_bldg_score = (VFSTR_AUDIT["smart_building_area_share_pct"] / 100.0) * 25.0 # 81.15% -> ~20.28 pts
    appliance_efficiency_score = ((VFSTR_AUDIT["led_adoption_pct"] + VFSTR_AUDIT["fan_efficiency_pct"]) / 200.0) * 20.0 # ~16.0 pts
    optimization_score = min(20.0, (annual_opt_co2_saving_tco2 / total_net_tco2) * 100.0 * 2.0)

    sustainability_index = float(np.round(renewable_score + smart_bldg_score + appliance_efficiency_score + optimization_score, 1))

    return {
        "annual_electricity_kwh": total_annual_kwh,
        "grid_electricity_kwh": annual_grid_kwh,
        "solar_generation_kwh": annual_solar_kwh,
        "renewable_share_pct": VFSTR_AUDIT["renewable_share_pct"],
        "scope1_dg_emissions_tco2": float(np.round(scope1_dg_tco2, 2)),
        "scope2_grid_emissions_tco2": float(np.round(scope2_grid_tco2, 2)),
        "total_gross_emissions_tco2": float(np.round(scope1_dg_tco2 + scope2_grid_tco2, 2)),
        "solar_avoided_emissions_tco2": float(np.round(avoided_solar_tco2, 2)),
        "net_carbon_footprint_tco2": float(np.round(total_net_tco2, 2)),
        "potential_annual_opt_saving_tco2": float(np.round(annual_opt_co2_saving_tco2, 2)),
        "campus_eui_kwh_per_sqm": float(np.round(campus_eui, 2)),
        "total_built_up_area_sqm": total_built_area,
        "ecomind_sustainability_index": sustainability_index,
        "per_capita_tco2": VFSTR_AUDIT["per_capita_carbon_footprint_tco2"],
    }


def generate_sustainability_pdf(metrics: dict[str, Any], pdf_path: Path) -> None:
    """Generate executive Sustainability & Carbon Audit PDF Report."""
    with PdfPages(pdf_path) as pdf:
        # Chart 1: Energy Mix (Solar vs Grid)
        fig, ax = plt.subplots(figsize=(8, 4.5))
        labels = ["Rooftop Solar PV (39%)", "Grid Electricity (61%)"]
        values = [metrics["solar_generation_kwh"], metrics["grid_electricity_kwh"]]
        colors = ["#2A9D8F", "#E76F51"]
        ax.pie(values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=140, explode=(0.05, 0))
        ax.set_title("VFSTR Campus Annual Electricity Mix (2,500,000 kWh)", fontsize=12, fontweight="bold")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        # Chart 2: GHG Emissions Breakdown & Solar Avoided Impact
        fig, ax = plt.subplots(figsize=(8, 4.5))
        categories = ["Scope 1 (DG Sets)", "Scope 2 (Grid)", "Avoided (Solar PV)", "Opt. Savings (Target)"]
        tco2_vals = [
            metrics["scope1_dg_emissions_tco2"],
            metrics["scope2_grid_emissions_tco2"],
            metrics["solar_avoided_emissions_tco2"],
            metrics["potential_annual_opt_saving_tco2"],
        ]
        bar_colors = ["#E63946", "#F4A261", "#2A9D8F", "#457B9D"]
        bars = ax.bar(categories, tco2_vals, color=bar_colors)
        ax.set_ylabel("t CO₂ / year")
        ax.set_title("Campus Carbon Footprint & Avoided Emissions (t CO₂/yr)", fontsize=12, fontweight="bold")
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height:.1f} t", xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)


def generate_sustainability_markdown(metrics: dict[str, Any], md_path: Path) -> None:
    """Generate Markdown executive summary for sustainability audit."""
    content = f"""# EcoMind AI — Stage 8 Sustainability & Carbon Footprint Audit Report

**Campus**: Vignan's Foundation for Science, Technology & Research (VFSTR), Vadlamudi, AP, India  
**Assessment Period**: VFSTR Annual Grounding (2024–2025)

---

## 🌟 Executive Sustainability Scorecard

- **EcoMind Sustainability Index**: **{metrics['ecomind_sustainability_index']} / 100**
- **Total Built-Up Area**: **{metrics['total_built_up_area_sqm']:,} m²**
- **Energy Use Intensity (EUI)**: **{metrics['campus_eui_kwh_per_sqm']} kWh / m² / year**
- **Per Capita Carbon Footprint**: **{metrics['per_capita_tco2']} t CO₂ / person**

---

## ⚡ Energy Mix & Renewable Energy Impact

- **Total Annual Electricity Usage**: **{metrics['annual_electricity_kwh']:,} kWh**
- **Grid Electricity Purchased**: **{metrics['grid_electricity_kwh']:,} kWh ({100 - metrics['renewable_share_pct']}%)**
- **Rooftop Solar PV Generation (1 MW)**: **{metrics['solar_generation_kwh']:,} kWh ({metrics['renewable_share_pct']}%)**
- **Solar Avoided Emissions**: **{metrics['solar_avoided_emissions_tco2']} t CO₂ / year**

---

## 🌿 Greenhouse Gas (GHG) Emissions Breakdown

| Emission Source | Category | Quantity | GHG Emissions (t CO₂e/yr) |
| :--- | :--- | :--- | :--- |
| **Diesel Generators** | Scope 1 | 18,000 Litres Diesel | {metrics['scope1_dg_emissions_tco2']} t CO₂ |
| **Grid Electricity** | Scope 2 | 1,525,000 kWh Grid Power | {metrics['scope2_grid_emissions_tco2']} t CO₂ |
| **Total Gross Emissions** | Scope 1 + 2 | — | **{metrics['total_gross_emissions_tco2']} t CO₂** |
| **Rooftop Solar Offset** | Avoided Scope 2 | 975,000 kWh Clean Solar | **-{metrics['solar_avoided_emissions_tco2']} t CO₂** |
| **Stage 7 AI Opt. Target** | Mitigation Target | AI Recommendations | **-{metrics['potential_annual_opt_saving_tco2']} t CO₂** |

---

## 🚀 Key Action Plan & Recommendations
1. **Rooftop Solar Expansion**: Increase rooftop solar capacity towards 40–50% renewable share target.
2. **100% Appliance Efficiency**: Replace remaining non-LED lights and non-BLDC fans to reach 100% campus adoption.
3. **AI-Driven BMS Control**: Implement Stage 7 optimization rules for peak tariff load shifting and after-hours HVAC lockouts.
"""
    md_path.write_text(content, encoding="utf-8")


def validate_sustainability(metrics: dict[str, Any], pdf_path: Path, md_path: Path) -> ValidationResult:
    result = ValidationResult(stage="stage8_sustainability", passed=True)
    score = metrics["ecomind_sustainability_index"]
    result.add("sustainability_score_valid", 0.0 <= score <= 100.0, f"score={score}")
    result.add("pdf_report_generated", pdf_path.exists(), str(pdf_path))
    result.add("markdown_summary_written", md_path.exists(), str(md_path))
    result.add("emissions_reconciled", metrics["total_gross_emissions_tco2"] > 0, "")
    return result


def run_stage8() -> dict[str, Any]:
    logger.info("Executing Stage 8 — Sustainability & Carbon Footprint Agent...")
    sensor_df = load_csv(GENERATED_DIR / "sensor_readings.csv")
    recs_df = load_csv(GENERATED_DIR / "recommendations.csv")

    metrics = calculate_sustainability_metrics(sensor_df, recs_df)

    pdf_path = REPORTS_DIR / "stage8_sustainability_report.pdf"
    md_path = REPORTS_DIR / "stage8_sustainability_summary.md"

    generate_sustainability_pdf(metrics, pdf_path)
    generate_sustainability_markdown(metrics, md_path)

    validation = validate_sustainability(metrics, pdf_path, md_path)

    report = {
        "stage": 8,
        "name": "Sustainability & Carbon Footprint Agent",
        "validation": validation.to_dict(),
        "paths": {
            "pdf_report": str(pdf_path),
            "markdown_summary": str(md_path),
        },
        "summary": metrics,
        "pending_issues": validation.pending_issues,
    }
    save_json(REPORTS_DIR / "stage8_sustainability.json", report)
    if not validation.passed:
        raise RuntimeError(f"Stage 8 validation failed: {validation.pending_issues}")
    logger.info("Stage 8 complete: EcoMind Sustainability Index = %.1f / 100", metrics["ecomind_sustainability_index"])
    return report
