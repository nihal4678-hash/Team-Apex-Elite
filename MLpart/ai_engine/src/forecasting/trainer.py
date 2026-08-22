"""Stage 5 — Electricity demand forecasting agent."""

from __future__ import annotations

from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

from src.utils.config import GENERATED_DIR, MLRUNS_DIR, MODELS_DIR, PROCESSED_DIR, RANDOM_SEED, REPORTS_DIR
from src.utils.io import save_csv, save_json
from src.utils.logging_utils import get_logger
from src.utils.validation import ValidationResult

logger = get_logger("ecomind.forecast")

FEATURE_COLS = [
    "hour",
    "day_of_week",
    "is_weekend",
    "is_working_hours",
    "occupancy",
    "occupancy_ratio",
    "outdoor_temperature_c",
    "humidity_pct",
    "cooling_load_index",
    "active_device_count",
]


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.clip(np.abs(y_true), 1e-6, None)
    return float(np.mean(np.abs((y_true - y_pred) / denom)) * 100.0)


def metrics_dict(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
        "mape": mape(y_true, y_pred),
    }


def aggregate_hourly(df: pd.DataFrame) -> pd.DataFrame:
    g = df.copy()
    g["timestamp_hour"] = g["timestamp"].dt.floor("h")
    agg = (
        g.groupby(["timestamp_hour", "building_id"], as_index=False)
        .agg(
            energy_kwh=("energy_kwh", "sum"),
            occupancy=("occupancy", "sum"),
            occupancy_ratio=("occupancy_ratio", "mean"),
            outdoor_temperature_c=("outdoor_temperature_c", "mean"),
            humidity_pct=("humidity_pct", "mean"),
            cooling_load_index=("cooling_load_index", "mean"),
            active_device_count=("active_device_count", "mean"),
            hour=("hour", "first"),
            day_of_week=("day_of_week", "first"),
            is_weekend=("is_weekend", "first"),
            is_working_hours=("is_working_hours", "first"),
        )
        .rename(columns={"timestamp_hour": "timestamp"})
    )
    return agg


def _try_prophet(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, Any] | None:
    try:
        from prophet import Prophet
    except Exception as exc:  # pragma: no cover
        logger.warning("Prophet unavailable: %s", exc)
        return None
    campus = train.groupby("timestamp", as_index=False)["energy_kwh"].sum().rename(
        columns={"timestamp": "ds", "energy_kwh": "y"}
    )
    future = test.groupby("timestamp", as_index=False)["energy_kwh"].sum().rename(
        columns={"timestamp": "ds", "energy_kwh": "y"}
    )
    model = Prophet(daily_seasonality=True, weekly_seasonality=True, seasonality_mode="additive")
    model.fit(campus)
    pred = model.predict(future[["ds"]])
    scores = metrics_dict(future["y"].to_numpy(), pred["yhat"].to_numpy())
    return {"name": "Prophet", "model": model, "metrics": scores, "level": "campus"}


def _log_mlflow(all_metrics: dict[str, dict[str, float]], best_name: str) -> None:
    try:
        import mlflow

        MLRUNS_DIR.mkdir(parents=True, exist_ok=True)
        mlflow.set_tracking_uri(MLRUNS_DIR.as_uri())
        mlflow.set_experiment("ecomind-forecasting")
        with mlflow.start_run(run_name=f"forecast-{best_name}"):
            mlflow.log_param("best_model", best_name)
            for name, scores in all_metrics.items():
                for k, v in scores.items():
                    mlflow.log_metric(f"{name}_{k}", v)
    except Exception as exc:
        logger.warning("MLflow logging skipped: %s", exc)


def run_stage5() -> dict[str, Any]:
    df = pd.read_csv(PROCESSED_DIR / "processed_sensor_data.csv", parse_dates=["timestamp"])
    hourly = aggregate_hourly(df)
    X = hourly[FEATURE_COLS]
    y = hourly["energy_kwh"].to_numpy()
    X_train, X_test, y_train, y_test, train_df, test_df = train_test_split(
        X, y, hourly, test_size=0.2, random_state=RANDOM_SEED, shuffle=False
    )

    candidates: dict[str, Any] = {}
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    candidates["LinearRegression"] = {
        "model": lr,
        "metrics": metrics_dict(y_test, lr.predict(X_test)),
    }

    rf = RandomForestRegressor(
        n_estimators=80, max_depth=12, random_state=RANDOM_SEED, n_jobs=-1, min_samples_leaf=4
    )
    rf.fit(X_train, y_train)
    candidates["RandomForest"] = {
        "model": rf,
        "metrics": metrics_dict(y_test, rf.predict(X_test)),
    }

    xgb = XGBRegressor(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_SEED,
        n_jobs=-1,
        tree_method="hist",
    )
    xgb.fit(X_train, y_train)
    candidates["XGBoost"] = {
        "model": xgb,
        "metrics": metrics_dict(y_test, xgb.predict(X_test)),
    }

    prophet_pack = _try_prophet(train_df, test_df)
    prophet_metrics = prophet_pack["metrics"] if prophet_pack else None

    ranked = sorted(candidates.items(), key=lambda kv: kv[1]["metrics"]["mae"])
    best_name, best_pack = ranked[0]
    best_model = best_pack["model"]

    pred = best_model.predict(X)
    hourly["predicted_energy_kwh"] = pred
    hourly["residual_kwh"] = hourly["energy_kwh"] - hourly["predicted_energy_kwh"]
    hourly["model"] = best_name

    importance = pd.DataFrame({"feature": FEATURE_COLS, "importance": np.nan})
    if hasattr(best_model, "feature_importances_"):
        importance["importance"] = best_model.feature_importances_
    elif hasattr(best_model, "coef_"):
        importance["importance"] = np.abs(best_model.coef_)
        importance["importance"] = importance["importance"] / importance["importance"].sum()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / "forecast_model.pkl"
    joblib.dump(
        {
            "model": best_model,
            "model_name": best_name,
            "features": FEATURE_COLS,
            "metrics": best_pack["metrics"],
            "all_metrics": {k: v["metrics"] for k, v in candidates.items()},
        },
        model_path,
    )
    pred_path = save_csv(hourly, GENERATED_DIR / "forecast_predictions.csv")
    fi_path = save_csv(importance, GENERATED_DIR / "feature_importance.csv")

    all_metrics = {k: v["metrics"] for k, v in candidates.items()}
    if prophet_metrics:
        all_metrics["Prophet"] = prophet_metrics
    _log_mlflow(all_metrics, best_name)

    validation = ValidationResult(stage="stage5_forecasting", passed=True)
    validation.add("model_serialized", model_path.exists(), str(model_path))
    validation.add("predictions_written", pred_path.exists(), str(pred_path))
    validation.add("best_model_selected", best_name in candidates, best_name)
    validation.add("r2_positive", best_pack["metrics"]["r2"] > 0, str(best_pack["metrics"]["r2"]))

    report = {
        "stage": 5,
        "name": "Forecasting Agent",
        "validation": validation.to_dict(),
        "best_model": best_name,
        "metrics": all_metrics,
        "paths": {
            "forecast_model": str(model_path),
            "forecast_predictions": str(pred_path),
            "feature_importance": str(fi_path),
        },
        "pending_issues": validation.pending_issues,
    }
    save_json(REPORTS_DIR / "stage5_forecasting.json", report)
    if not validation.passed:
        raise RuntimeError(f"Stage 5 validation failed: {validation.pending_issues}")
    logger.info("Stage 5 complete. Best model=%s metrics=%s", best_name, best_pack["metrics"])
    return report
