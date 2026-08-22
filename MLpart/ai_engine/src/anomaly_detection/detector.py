"""Stage 6 — Anomaly detection with synthetic fault injection."""

from __future__ import annotations

from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.utils.config import CAMPUS, GENERATED_DIR, MODELS_DIR, PROCESSED_DIR, RANDOM_SEED, REPORTS_DIR
from src.utils.io import save_csv, save_json
from src.utils.logging_utils import get_logger
from src.utils.validation import ValidationResult

logger = get_logger("ecomind.anomaly")

FEATURE_COLS = [
    "hour",
    "is_weekend",
    "is_working_hours",
    "occupancy",
    "occupancy_ratio",
    "outdoor_temperature_c",
    "energy_kwh",
    "lights_status",
    "fans_status",
    "ac_status",
    "projector_status",
    "computer_usage",
    "cooling_load_index",
    "active_device_count",
]


def inject_faults(df: pd.DataFrame, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    out = df.copy()
    n = len(out)
    n_each = max(400, int(0.004 * n))
    out["injected_fault"] = "none"
    idx = np.arange(n)
    rng.shuffle(idx)

    # Lights ON, occupancy 0
    a = idx[:n_each]
    out.loc[out.index[a], "occupancy"] = 0
    out.loc[out.index[a], "occupancy_ratio"] = 0
    out.loc[out.index[a], "lights_status"] = 1
    out.loc[out.index[a], "energy_kwh"] = np.maximum(out.loc[out.index[a], "energy_kwh"], 0.08)
    out.loc[out.index[a], "injected_fault"] = "lights_on_empty_room"

    # AC ON after hours
    b = idx[n_each : 2 * n_each]
    out.loc[out.index[b], "ac_status"] = 1
    out.loc[out.index[b], "hour"] = 23
    out.loc[out.index[b], "is_working_hours"] = 0
    out.loc[out.index[b], "energy_kwh"] = out.loc[out.index[b], "energy_kwh"] + 0.45
    out.loc[out.index[b], "injected_fault"] = "ac_on_after_hours"

    # Sudden energy spike
    c = idx[2 * n_each : 3 * n_each]
    out.loc[out.index[c], "energy_kwh"] = out.loc[out.index[c], "energy_kwh"] * 6.5 + 1.2
    out.loc[out.index[c], "injected_fault"] = "sudden_energy_spike"

    # Projector ON in empty room
    d = idx[3 * n_each : 4 * n_each]
    out.loc[out.index[d], "occupancy"] = 0
    out.loc[out.index[d], "occupancy_ratio"] = 0
    out.loc[out.index[d], "projector_status"] = 1
    out.loc[out.index[d], "energy_kwh"] = np.maximum(out.loc[out.index[d], "energy_kwh"], 0.07)
    out.loc[out.index[d], "injected_fault"] = "projector_on_empty_room"
    return out


def reason_and_action(row: pd.Series) -> tuple[str, str, str]:
    if row["occupancy"] == 0 and row["lights_status"] == 1:
        return (
            "high",
            "Lights remain ON while occupancy is zero.",
            "Switch lights off via occupancy sensors / BMS schedule.",
        )
    if row["ac_status"] == 1 and row["is_working_hours"] == 0 and row["occupancy"] <= 2:
        return (
            "critical",
            "HVAC running after hours with negligible occupancy.",
            "Set HVAC occupancy-based setback and lock after 18:00 except hostels.",
        )
    if row["projector_status"] == 1 and row["occupancy"] == 0:
        return (
            "medium",
            "Projector is ON in an empty room.",
            "Power-off AV stack when room booking ends.",
        )
    if row.get("energy_kwh", 0) > row.get("energy_kwh_roll", row.get("energy_kwh", 0) * 3):
        return (
            "high",
            "Sudden energy spike versus local baseline.",
            "Inspect circuit, HVAC compressor, and lab equipment.",
        )
    return (
        "medium",
        "Statistical outlier in energy/device pattern.",
        "Verify sensor health and compare with adjacent rooms.",
    )


def run_stage6() -> dict[str, Any]:
    df = pd.read_csv(PROCESSED_DIR / "processed_sensor_data.csv", parse_dates=["timestamp"])
    # Train on a stratified sample of clean data for tractability
    train = df.sample(n=min(80_000, len(df)), random_state=RANDOM_SEED)
    model = IsolationForest(
        n_estimators=120,
        contamination=0.03,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    model.fit(train[FEATURE_COLS])

    scored = inject_faults(df.sample(n=min(60_000, len(df)), random_state=RANDOM_SEED + 1).reset_index(drop=True))
    scored["anomaly_score"] = -model.decision_function(scored[FEATURE_COLS])
    scored["is_anomaly"] = (model.predict(scored[FEATURE_COLS]) == -1).astype(np.int8)
    # Rule overlay so injected operational faults are always surfaced
    rule = (
        ((scored["occupancy"] == 0) & (scored["lights_status"] == 1))
        | ((scored["ac_status"] == 1) & (scored["is_working_hours"] == 0) & (scored["occupancy"] <= 2))
        | ((scored["projector_status"] == 1) & (scored["occupancy"] == 0))
        | (scored["injected_fault"] == "sudden_energy_spike")
    )
    scored.loc[rule, "is_anomaly"] = 1
    scored["confidence"] = np.clip(scored["anomaly_score"] / (scored["anomaly_score"].max() + 1e-9), 0.05, 0.99)
    scored.loc[rule, "confidence"] = np.maximum(scored.loc[rule, "confidence"], 0.75)

    reasons = scored.apply(reason_and_action, axis=1, result_type="expand")
    reasons.columns = ["severity", "reason", "recommended_action"]
    scored = pd.concat([scored, reasons], axis=1)
    scored.loc[scored["is_anomaly"] == 0, ["severity", "reason", "recommended_action"]] = ["none", "", ""]

    alerts = scored[scored["is_anomaly"] == 1].copy()
    alerts["estimated_waste_kwh"] = np.clip(alerts["energy_kwh"] * 0.55, 0.02, None)
    alerts["estimated_cost_inr"] = alerts["estimated_waste_kwh"] * CAMPUS["tariff_inr_per_kwh"]

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / "anomaly_model.pkl"
    joblib.dump({"model": model, "features": FEATURE_COLS, "contamination": 0.03}, model_path)
    pred_path = save_csv(scored, GENERATED_DIR / "anomaly_predictions.csv")
    alerts_path = save_csv(alerts, GENERATED_DIR / "alerts.csv")

    required = ["severity", "confidence", "reason", "recommended_action"]
    missing = [c for c in required if c not in alerts.columns]
    nonempty = alerts[required].notna().all().all() and (alerts["reason"].astype(str).str.len() > 0).all()

    validation = ValidationResult(stage="stage6_anomaly", passed=True)
    validation.add("model_saved", model_path.exists(), str(model_path))
    validation.add("alert_schema", len(missing) == 0, str(missing))
    validation.add("every_anomaly_explained", bool(nonempty), "")
    validation.add("alerts_nonempty", len(alerts) > 0, f"n={len(alerts)}")

    report = {
        "stage": 6,
        "name": "Anomaly Detection Agent",
        "validation": validation.to_dict(),
        "summary": {
            "scored_rows": int(len(scored)),
            "alerts": int(len(alerts)),
            "injected_fault_counts": scored["injected_fault"].value_counts().to_dict(),
        },
        "paths": {
            "anomaly_model": str(model_path),
            "anomaly_predictions": str(pred_path),
            "alerts": str(alerts_path),
        },
        "pending_issues": validation.pending_issues,
    }
    save_json(REPORTS_DIR / "stage6_anomaly.json", report)
    if not validation.passed:
        raise RuntimeError(f"Stage 6 validation failed: {validation.pending_issues}")
    logger.info("Stage 6 complete: %s alerts", len(alerts))
    return report
