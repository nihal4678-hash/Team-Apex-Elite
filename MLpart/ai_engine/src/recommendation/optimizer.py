"""Stage 7 — Optimization & Actionable Recommendation Agent for EcoMind AI."""

from __future__ import annotations

from typing import Any
import joblib
import numpy as np
import pandas as pd

from src.utils.config import CAMPUS, GENERATED_DIR, MODELS_DIR, PROCESSED_DIR, REPORTS_DIR, VFSTR_AUDIT, TARIFF_PEAK_HOURS
from src.utils.io import load_csv, save_csv, save_json
from src.utils.logging_utils import get_logger
from src.utils.validation import ValidationResult

logger = get_logger("ecomind.optimizer")


def generate_recommendations(
    forecast_df: pd.DataFrame, alerts_df: pd.DataFrame, buildings_df: pd.DataFrame
) -> pd.DataFrame:
    """Generate prioritized energy optimization recommendations based on forecasts and anomaly alerts."""
    recs: list[dict[str, Any]] = []
    rec_counter = 1

    # 1. Peak Tariff Load Shifting & Precooling Recommendation
    peak_forecast = forecast_df[forecast_df["hour"].between(TARIFF_PEAK_HOURS[0], TARIFF_PEAK_HOURS[1] - 1)]
    if not peak_forecast.empty:
        high_peak_buildings = peak_forecast.groupby("building_id")["predicted_energy_kwh"].sum().sort_values(ascending=False)
        top_building = high_peak_buildings.index[0]
        top_kwh = float(high_peak_buildings.iloc[0])
        est_kwh_save = top_kwh * 0.18
        est_inr_save = est_kwh_save * CAMPUS["tariff_inr_per_kwh"]
        est_co2_kg = est_kwh_save * CAMPUS["grid_carbon_kg_per_kwh"] * 30.0

        recs.append(
            {
                "recommendation_id": f"REC-{rec_counter:03d}",
                "building_id": top_building,
                "category": "peak_load_shading",
                "priority": "critical",
                "intervention_type": "HVAC Precooling & Tariff Shifting",
                "recommended_action": f"Pre-cool building by 1.5°C between 15:00-17:00 and setback thermostat to 26°C during peak tariff hours (18:00-22:00).",
                "target_schedule": "18:00 - 22:00 Daily",
                "estimated_daily_kwh_saved": np.round(est_kwh_save, 2),
                "estimated_daily_inr_saved": np.round(est_inr_save, 2),
                "estimated_monthly_co2_reduction_kg": np.round(est_co2_kg, 2),
            }
        )
        rec_counter += 1

    # 2. Solar PV Self-Consumption Alignment
    solar_buildings = buildings_df[buildings_df.get("solar_pv_installed", True)]["building_id"].tolist()
    recs.append(
        {
            "recommendation_id": f"REC-{rec_counter:03d}",
            "building_id": "LAB-CSE" if "LAB-CSE" in buildings_df["building_id"].values else solar_buildings[0],
            "category": "solar_alignment",
            "priority": "high",
            "intervention_type": "Rooftop Solar Self-Consumption Maximization",
            "recommended_action": f"Schedule heavy IT batch processing and computer lab workloads during peak 1 MW rooftop solar generation hours (10:00-14:00).",
            "target_schedule": "10:00 - 14:00 Weekdays",
            "estimated_daily_kwh_saved": 45.5,
            "estimated_daily_inr_saved": np.round(45.5 * CAMPUS["tariff_inr_per_kwh"], 2),
            "estimated_monthly_co2_reduction_kg": np.round(45.5 * CAMPUS["grid_carbon_kg_per_kwh"] * 30.0, 2),
        }
    )
    rec_counter += 1

    # 3. Anomaly-Driven Wastage Mitigation Recommendations
    if not alerts_df.empty:
        waste_by_bldg = alerts_df.groupby("building_id")["estimated_waste_kwh"].sum().sort_values(ascending=False)
        for b_id, total_waste in waste_by_bldg.head(3).items():
            b_alerts = alerts_df[alerts_df["building_id"] == b_id]
            top_reason = b_alerts["reason"].mode().iloc[0] if not b_alerts.empty else "Operational inefficiency"
            est_daily_save = total_waste / max(1, len(alerts_df["timestamp"].unique())) if "timestamp" in alerts_df.columns else total_waste * 0.1
            est_inr = est_daily_save * CAMPUS["tariff_inr_per_kwh"]
            est_co2 = est_daily_save * CAMPUS["grid_carbon_kg_per_kwh"] * 30.0

            recs.append(
                {
                    "recommendation_id": f"REC-{rec_counter:03d}",
                    "building_id": b_id,
                    "category": "wastage_mitigation",
                    "priority": "high" if est_daily_save > 10 else "medium",
                    "intervention_type": "Automated Sensor Control Lockout",
                    "recommended_action": f"Remediate recurring fault ({top_reason}) via BMS sensor lockouts and after-hours power cuts.",
                    "target_schedule": "Immediate Automated Rule",
                    "estimated_daily_kwh_saved": np.round(est_daily_save, 2),
                    "estimated_daily_inr_saved": np.round(est_inr, 2),
                    "estimated_monthly_co2_reduction_kg": np.round(est_co2, 2),
                }
            )
            rec_counter += 1

    # 4. LED & Efficient Appliance Optimization (VFSTR Carbon Audit grounding)
    recs.append(
        {
            "recommendation_id": f"REC-{rec_counter:03d}",
            "building_id": "CAMPUS-WIDE",
            "category": "retrofit_optimization",
            "priority": "medium",
            "intervention_type": "Appliance Efficiency Retrofit",
            "recommended_action": f"Upgrade remaining 15% non-LED lighting (1,500 lamps) and 25% non-BLDC fans (525 units) to 100% efficient models as outlined in VFSTR Carbon Audit.",
            "target_schedule": "Medium-Term Action Plan",
            "estimated_daily_kwh_saved": 85.0,
            "estimated_daily_inr_saved": np.round(85.0 * CAMPUS["tariff_inr_per_kwh"], 2),
            "estimated_monthly_co2_reduction_kg": np.round(85.0 * CAMPUS["grid_carbon_kg_per_kwh"] * 30.0, 2),
        }
    )

    df_recs = pd.DataFrame(recs)
    return df_recs


def validate_recommendations(df: pd.DataFrame) -> ValidationResult:
    result = ValidationResult(stage="stage7_optimization", passed=True)
    result.add("recommendations_nonempty", len(df) > 0, f"n={len(df)}")
    required = [
        "recommendation_id",
        "building_id",
        "priority",
        "intervention_type",
        "recommended_action",
        "estimated_daily_kwh_saved",
        "estimated_daily_inr_saved",
    ]
    missing = [c for c in required if c not in df.columns]
    result.add("valid_schema", len(missing) == 0, f"missing={missing}")
    result.add("positive_savings", (df["estimated_daily_kwh_saved"] > 0).all(), "")
    return result


def run_stage7() -> dict[str, Any]:
    logger.info("Executing Stage 7 — Optimization & Actionable Recommendation Agent...")
    forecast_df = load_csv(GENERATED_DIR / "forecast_predictions.csv")
    alerts_df = load_csv(GENERATED_DIR / "alerts.csv")
    buildings_df = load_csv(GENERATED_DIR / "buildings.csv")

    recs_df = generate_recommendations(forecast_df, alerts_df, buildings_df)
    validation = validate_recommendations(recs_df)

    recs_path = save_csv(recs_df, GENERATED_DIR / "recommendations.csv")

    # Serialize optimization rules metadata
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    rules_path = MODELS_DIR / "optimization_rules.pkl"
    joblib.dump({"total_recommendations": len(recs_df), "categories": recs_df["category"].tolist()}, rules_path)

    total_kwh_saved = float(recs_df["estimated_daily_kwh_saved"].sum())
    total_inr_saved = float(recs_df["estimated_daily_inr_saved"].sum())
    total_co2_kg_saved = float(recs_df["estimated_monthly_co2_reduction_kg"].sum())

    report = {
        "stage": 7,
        "name": "Optimization & Actionable Recommendation Agent",
        "validation": validation.to_dict(),
        "paths": {
            "recommendations": str(recs_path),
            "optimization_rules": str(rules_path),
        },
        "summary": {
            "total_recommendations": int(len(recs_df)),
            "total_estimated_daily_kwh_saved": total_kwh_saved,
            "total_estimated_daily_inr_saved": total_inr_saved,
            "total_estimated_monthly_co2_reduction_kg": total_co2_kg_saved,
            "priorities": recs_df["priority"].value_counts().to_dict(),
        },
        "pending_issues": validation.pending_issues,
    }
    save_json(REPORTS_DIR / "stage7_optimization.json", report)
    if not validation.passed:
        raise RuntimeError(f"Stage 7 validation failed: {validation.pending_issues}")
    logger.info("Stage 7 complete: %d optimization recommendations generated", len(recs_df))
    return report
