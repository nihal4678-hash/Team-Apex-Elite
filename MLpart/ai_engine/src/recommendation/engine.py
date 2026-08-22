"""Stage 7 — Energy optimization / recommendation agent."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.utils.config import CAMPUS, GENERATED_DIR, REPORTS_DIR, TARIFF_PEAK_HOURS
from src.utils.io import save_csv, save_json
from src.utils.logging_utils import get_logger
from src.utils.validation import ValidationResult

logger = get_logger("ecomind.optimize")


def _impact(kwh: float) -> dict[str, float]:
    cost = kwh * CAMPUS["tariff_inr_per_kwh"]
    co2 = kwh * CAMPUS["grid_carbon_kg_per_kwh"]
    return {
        "energy_saved_kwh": round(float(kwh), 3),
        "money_saved_inr": round(float(cost), 2),
        "co2_reduced_kg": round(float(co2), 3),
    }


def generate_recommendations(alerts: pd.DataFrame, forecast: pd.DataFrame) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    tariff = CAMPUS["tariff_inr_per_kwh"]

    empty_lights = alerts[alerts["reason"].str.contains("Lights remain ON", na=False)]
    if len(empty_lights):
        kwh = float(empty_lights["estimated_waste_kwh"].sum())
        recs.append(
            {
                "recommendation_id": "REC-HVAC-000"[:0] + "REC-LGT-001",
                "category": "lighting_optimization",
                "title": "Occupancy-based lighting shutoff",
                "description": "Auto-off lights in academic/admin rooms when occupancy is zero for 10 minutes.",
                "priority_score": 92,
                "buildings": sorted(empty_lights["building_id"].dropna().unique().tolist())[:8],
                **_impact(kwh),
            }
        )

    ac_after = alerts[alerts["reason"].str.contains("HVAC running after hours", na=False)]
    if len(ac_after):
        kwh = float(ac_after["estimated_waste_kwh"].sum())
        recs.append(
            {
                "recommendation_id": "REC-HVAC-001",
                "category": "hvac_optimization",
                "title": "After-hours HVAC setback",
                "description": "Lock AC except hostels and exam-critical labs after 18:00; raise setpoint to 28°C.",
                "priority_score": 98,
                "buildings": sorted(ac_after["building_id"].dropna().unique().tolist())[:8],
                **_impact(kwh),
            }
        )

    proj = alerts[alerts["reason"].str.contains("Projector is ON", na=False)]
    if len(proj):
        kwh = float(proj["estimated_waste_kwh"].sum())
        recs.append(
            {
                "recommendation_id": "REC-AV-001",
                "category": "device_optimization",
                "title": "Empty-room projector / AV power-down",
                "description": "Tie projector power to room booking end events.",
                "priority_score": 70,
                "buildings": sorted(proj["building_id"].dropna().unique().tolist())[:8],
                **_impact(kwh),
            }
        )

    # Fan optimization from forecast occupancy
    low_occ = forecast[(forecast["occupancy_ratio"] < 0.15) & (forecast["hour"].between(10, 16))]
    if len(low_occ):
        kwh = float(low_occ["energy_kwh"].mean() * 0.08 * min(len(low_occ), 400))
        recs.append(
            {
                "recommendation_id": "REC-FAN-001",
                "category": "fan_optimization",
                "title": "Stage fans with occupancy bands",
                "description": "Run 50% of ceiling fans when occupancy ratio < 0.25 in academic rooms.",
                "priority_score": 74,
                "buildings": sorted(low_occ["building_id"].dropna().unique().tolist())[:8],
                **_impact(kwh),
            }
        )

    # Room scheduling: merge underused classrooms
    underused = forecast.groupby("building_id")["occupancy_ratio"].mean().sort_values()
    if len(underused):
        kwh = float(forecast["energy_kwh"].sum() * 0.012)
        recs.append(
            {
                "recommendation_id": "REC-SCH-001",
                "category": "room_scheduling_optimization",
                "title": "Consolidate low-utilization classrooms",
                "description": "Shift small sections into fewer rooms in the lowest-utilization academic blocks.",
                "priority_score": 80,
                "buildings": underused.head(3).index.tolist(),
                **_impact(kwh),
            }
        )

    peak = forecast[forecast["hour"].between(*TARIFF_PEAK_HOURS)]
    offpeak = forecast[forecast["hour"].between(6, 10)]
    if len(peak) and len(offpeak):
        kwh = float(peak["energy_kwh"].sum() * 0.04)
        recs.append(
            {
                "recommendation_id": "REC-LOAD-001",
                "category": "load_shifting",
                "title": "Shift lab batch jobs and laundry to off-peak",
                "description": "Move non-critical computer-lab imaging and hostel laundry to 06:00–10:00.",
                "priority_score": 85,
                "buildings": ["LAB-CSE", "HST-B", "HST-G"],
                **_impact(kwh),
            }
        )

    # Weather-aware HVAC
    hot = forecast[forecast["outdoor_temperature_c"] >= 33]
    if len(hot):
        kwh = float(hot["energy_kwh"].sum() * 0.03)
        recs.append(
            {
                "recommendation_id": "REC-HVAC-002",
                "category": "hvac_optimization",
                "title": "Pre-cool labs before peak heat",
                "description": "Pre-cool CSE labs 45 minutes before occupancy on days forecast ≥ 33°C.",
                "priority_score": 88,
                "buildings": ["LAB-CSE", "LIB"],
                **_impact(kwh),
            }
        )

    for rec in recs:
        rec["tariff_inr_per_kwh"] = tariff
        rec["grid_carbon_kg_per_kwh"] = CAMPUS["grid_carbon_kg_per_kwh"]
        rec["campus"] = CAMPUS["name"]
    recs.sort(key=lambda r: r["priority_score"], reverse=True)
    return recs


def run_stage7() -> dict[str, Any]:
    alerts = pd.read_csv(GENERATED_DIR / "alerts.csv")
    forecast = pd.read_csv(GENERATED_DIR / "forecast_predictions.csv", parse_dates=["timestamp"])
    recs = generate_recommendations(alerts, forecast)
    summary = pd.DataFrame(recs)
    json_path = save_json(GENERATED_DIR / "recommendations.json", recs)
    csv_path = save_csv(summary, GENERATED_DIR / "optimization_summary.csv")

    validation = ValidationResult(stage="stage7_optimization", passed=True)
    validation.add("recommendations_exist", len(recs) > 0, f"n={len(recs)}")
    impact_ok = all(
        ("energy_saved_kwh" in r and "money_saved_inr" in r and "co2_reduced_kg" in r) for r in recs
    )
    validation.add("every_recommendation_has_impact", impact_ok, "")
    validation.add("priority_present", all("priority_score" in r for r in recs), "")

    report = {
        "stage": 7,
        "name": "Energy Optimization Agent",
        "validation": validation.to_dict(),
        "summary": {
            "n_recommendations": len(recs),
            "total_energy_saved_kwh": float(summary["energy_saved_kwh"].sum()) if len(summary) else 0,
            "total_money_saved_inr": float(summary["money_saved_inr"].sum()) if len(summary) else 0,
            "total_co2_reduced_kg": float(summary["co2_reduced_kg"].sum()) if len(summary) else 0,
        },
        "paths": {"recommendations": str(json_path), "optimization_summary": str(csv_path)},
        "pending_issues": validation.pending_issues,
    }
    save_json(REPORTS_DIR / "stage7_optimization.json", report)
    if not validation.passed:
        raise RuntimeError(f"Stage 7 validation failed: {validation.pending_issues}")
    logger.info("Stage 7 complete: %s recommendations", len(recs))
    return report
