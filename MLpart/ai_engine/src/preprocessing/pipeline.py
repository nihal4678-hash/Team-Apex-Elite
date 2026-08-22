"""Stage 3 — Sensor preprocessing and feature engineering pipeline."""

from __future__ import annotations

from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.utils.config import MODELS_DIR, PROCESSED_DIR, RANDOM_SEED, WORKING_HOURS
from src.utils.io import load_csv, save_csv, save_json
from src.utils.logging_utils import get_logger
from src.utils.validation import ValidationResult

logger = get_logger("ecomind.preprocess")

CATEGORICAL = ["building_id", "category"]
NUMERIC_SCALE = [
    "occupancy",
    "indoor_temperature_c",
    "outdoor_temperature_c",
    "humidity_pct",
    "computer_usage",
    "voltage_v",
    "current_a",
    "power_factor",
    "frequency_hz",
    "power_w",
    "energy_kwh",
    "occupancy_ratio",
    "temperature_diff_c",
    "active_device_count",
    "cooling_load_index",
    "hour",
    "day_of_week",
]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"])
    out = out.sort_values(["room_id", "timestamp"])
    out = out.drop_duplicates(subset=["room_id", "timestamp"], keep="last")
    out = out.dropna(subset=["timestamp", "room_id", "energy_kwh"])

    numeric_cols = out.select_dtypes(include=[np.number]).columns
    out[numeric_cols] = out[numeric_cols].interpolate(limit_direction="both")
    out[numeric_cols] = out[numeric_cols].fillna(out[numeric_cols].median())

    out["hour"] = out["timestamp"].dt.hour
    out["day_of_week"] = out["timestamp"].dt.dayofweek
    out["is_weekend"] = (out["day_of_week"] >= 5).astype(np.int8)
    out["is_working_hours"] = (
        (out["hour"] >= WORKING_HOURS[0]) & (out["hour"] < WORKING_HOURS[1]) & (out["is_weekend"] == 0)
    ).astype(np.int8)
    out["occupancy_ratio"] = out["occupancy"] / out["room_capacity"].clip(lower=1)
    out["temperature_diff_c"] = out["indoor_temperature_c"] - out["outdoor_temperature_c"]
    out["active_device_count"] = (
        out["lights_status"]
        + out["fans_status"]
        + out["ac_status"]
        + out["projector_status"]
        + (out["computer_usage"] > 0.05).astype(np.int8)
    )
    out["cooling_load_index"] = (
        out["ac_status"] * np.clip(out["outdoor_temperature_c"] - 24.0, 0, None) * (1 + out["occupancy_ratio"])
    )
    out["month"] = out["timestamp"].dt.month
    out["date"] = out["timestamp"].dt.date.astype(str)
    return out


def build_sklearn_pipeline() -> Pipeline:
    transformer = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_SCALE),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
        ],
        remainder="drop",
    )
    return Pipeline(steps=[("features", transformer)])


def validate_processed(df: pd.DataFrame) -> ValidationResult:
    result = ValidationResult(stage="stage3_preprocessing", passed=True)
    result.add("no_missing_values", int(df.isna().sum().sum()) == 0, f"nulls={int(df.isna().sum().sum())}")
    dupes = df.duplicated(subset=["room_id", "timestamp"]).sum()
    result.add("no_duplicate_room_timestamps", int(dupes) == 0, f"dupes={int(dupes)}")
    required = [
        "hour",
        "day_of_week",
        "is_weekend",
        "is_working_hours",
        "occupancy_ratio",
        "temperature_diff_c",
        "active_device_count",
        "cooling_load_index",
    ]
    missing = [c for c in required if c not in df.columns]
    result.add("feature_columns_present", len(missing) == 0, f"missing={missing}")
    return result


def run_stage3() -> dict[str, Any]:
    raw = load_csv(PROCESSED_DIR.parent / "generated" / "sensor_readings.csv")
    processed = engineer_features(raw)
    pipeline = build_sklearn_pipeline()
    sample = processed.sample(n=min(20_000, len(processed)), random_state=RANDOM_SEED)
    pipeline.fit(sample)

    processed_path = save_csv(processed, PROCESSED_DIR / "processed_sensor_data.csv")
    model_path = MODELS_DIR / "feature_pipeline.pkl"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"pipeline": pipeline, "numeric": NUMERIC_SCALE, "categorical": CATEGORICAL, "seed": RANDOM_SEED},
        model_path,
    )
    validation = validate_processed(processed)
    report = {
        "stage": 3,
        "name": "Sensor Preprocessing Agent",
        "validation": validation.to_dict(),
        "paths": {"processed": str(processed_path), "feature_pipeline": str(model_path)},
        "summary": {"rows": int(len(processed)), "columns": list(processed.columns)},
        "pending_issues": validation.pending_issues,
    }
    save_json(PROCESSED_DIR.parent.parent / "reports" / "stage3_preprocessing.json", report)
    if not validation.passed:
        raise RuntimeError(f"Stage 3 validation failed: {validation.pending_issues}")
    logger.info("Stage 3 complete: %s rows", len(processed))
    return report
