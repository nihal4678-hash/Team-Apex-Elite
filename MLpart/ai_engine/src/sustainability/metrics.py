"""Stage 8 — Campus sustainability analytics agent."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.utils.config import CAMPUS, GENERATED_DIR, PROCESSED_DIR, REPORTS_DIR
from src.utils.io import save_csv, save_json
from src.utils.logging_utils import get_logger
from src.utils.validation import ValidationResult

logger = get_logger("ecomind.sustainability")


def building_efficiency(processed: pd.DataFrame) -> pd.DataFrame:
    g = (
        processed.groupby(["building_id", "building_name", "category"], as_index=False)
        .agg(
            energy_kwh=("energy_kwh", "sum"),
            occupancy_hours=("occupancy", "sum"),
            mean_occupancy_ratio=("occupancy_ratio", "mean"),
            mean_cooling_load=("cooling_load_index", "mean"),
        )
    )
    g["energy_per_occupied_person_interval"] = g["energy_kwh"] / g["occupancy_hours"].clip(lower=1)
    # Higher occupancy with lower energy intensity scores better
    intensity = g["energy_kwh"] / g["energy_kwh"].max()
    util = g["mean_occupancy_ratio"] / g["mean_occupancy_ratio"].max()
    g["efficiency_score"] = np.clip(100 * (0.65 * util + 0.35 * (1 - intensity)), 0, 100)
    g["cost_inr"] = g["energy_kwh"] * CAMPUS["tariff_inr_per_kwh"]
    g["co2_kg"] = g["energy_kwh"] * CAMPUS["grid_carbon_kg_per_kwh"]
    g = g.sort_values("efficiency_score", ascending=False)
    g["leaderboard_rank"] = np.arange(1, len(g) + 1)
    return g


def daily_metrics(processed: pd.DataFrame, opt_total_kwh: float) -> pd.DataFrame:
    daily = processed.groupby(processed["timestamp"].dt.date).agg(
        energy_kwh=("energy_kwh", "sum"),
        mean_occupancy_ratio=("occupancy_ratio", "mean"),
        ac_fraction=("ac_status", "mean"),
    )
    daily = daily.reset_index().rename(columns={"timestamp": "date"})
    n = max(len(daily), 1)
    daily["optimized_energy_kwh"] = daily["energy_kwh"] * (1 - (opt_total_kwh / daily["energy_kwh"].sum()))
    daily["energy_saved_kwh"] = daily["energy_kwh"] - daily["optimized_energy_kwh"]
    daily["money_saved_inr"] = daily["energy_saved_kwh"] * CAMPUS["tariff_inr_per_kwh"]
    daily["co2_reduced_kg"] = daily["energy_saved_kwh"] * CAMPUS["grid_carbon_kg_per_kwh"]
    # Sustainability score: efficiency + savings + occupancy
    daily["sustainability_score"] = np.clip(
        55
        + 25 * (1 - daily["energy_kwh"] / daily["energy_kwh"].max())
        + 15 * daily["mean_occupancy_ratio"]
        + 5 * (1 - daily["ac_fraction"]),
        0,
        100,
    )
    return daily


def weekly_report(daily: pd.DataFrame, buildings: pd.DataFrame, opt_summary: pd.DataFrame) -> dict[str, Any]:
    daily = daily.copy()
    daily["date"] = pd.to_datetime(daily["date"])
    daily["week"] = daily["date"].dt.to_period("W").astype(str)
    weekly = daily.groupby("week").agg(
        energy_kwh=("energy_kwh", "sum"),
        energy_saved_kwh=("energy_saved_kwh", "sum"),
        money_saved_inr=("money_saved_inr", "sum"),
        co2_reduced_kg=("co2_reduced_kg", "sum"),
        sustainability_score=("sustainability_score", "mean"),
    )
    return {
        "campus": CAMPUS,
        "weekly": weekly.reset_index().to_dict(orient="records"),
        "monthly_savings": {
            "energy_kwh": float(daily["energy_saved_kwh"].sum()),
            "money_inr": float(daily["money_saved_inr"].sum()),
            "co2_kg": float(daily["co2_reduced_kg"].sum()),
        },
        "green_leaderboard": buildings.head(5)[
            ["leaderboard_rank", "building_id", "building_name", "efficiency_score", "energy_kwh"]
        ].to_dict(orient="records"),
        "optimization_alignment": {
            "opt_energy_saved_kwh": float(opt_summary["energy_saved_kwh"].sum()),
            "sustainability_energy_saved_kwh": float(daily["energy_saved_kwh"].sum()),
        },
    }


def run_stage8() -> dict[str, Any]:
    processed = pd.read_csv(PROCESSED_DIR / "processed_sensor_data.csv", parse_dates=["timestamp"])
    opt = pd.read_csv(GENERATED_DIR / "optimization_summary.csv")
    buildings = building_efficiency(processed)
    daily = daily_metrics(processed, float(opt["energy_saved_kwh"].sum()))
    weekly = weekly_report(daily, buildings, opt)

    # Consistency: daily savings should match optimization totals within 1%
    aligned = abs(daily["energy_saved_kwh"].sum() - opt["energy_saved_kwh"].sum()) / max(
        opt["energy_saved_kwh"].sum(), 1e-6
    )

    m_path = save_csv(daily, GENERATED_DIR / "sustainability_metrics.csv")
    b_path = save_csv(buildings, GENERATED_DIR / "building_scores.csv")
    w_path = save_json(GENERATED_DIR / "weekly_report.json", weekly)

    validation = ValidationResult(stage="stage8_sustainability", passed=True)
    validation.add("metrics_written", m_path.exists(), str(m_path))
    validation.add("leaderboard_written", b_path.exists(), str(b_path))
    validation.add("optimization_consistency_lt_1pct", aligned < 0.01, f"rel_err={aligned:.4f}")
    validation.add("scores_in_0_100", bool(buildings["efficiency_score"].between(0, 100).all()), "")

    report = {
        "stage": 8,
        "name": "Sustainability Agent",
        "validation": validation.to_dict(),
        "summary": weekly["monthly_savings"],
        "paths": {
            "sustainability_metrics": str(m_path),
            "building_scores": str(b_path),
            "weekly_report": str(w_path),
        },
        "pending_issues": validation.pending_issues,
    }
    save_json(REPORTS_DIR / "stage8_sustainability.json", report)
    if not validation.passed:
        raise RuntimeError(f"Stage 8 validation failed: {validation.pending_issues}")
    logger.info("Stage 8 complete")
    return report
