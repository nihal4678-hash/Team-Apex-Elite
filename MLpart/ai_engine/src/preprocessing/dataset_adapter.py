"""Dataset Adapter — Ingests IIIT-Delhi raw campus dataset and maps empirical power profiles to VFSTR Digital Twin topology."""

from __future__ import annotations

from typing import Any
import pandas as pd
import numpy as np

from src.utils.config import IIITD_RAW_DIR, PROCESSED_DIR, CAMPUS
from src.utils.io import load_csv, save_csv
from src.utils.logging_utils import get_logger

logger = get_logger("ecomind.dataset_adapter")

# Mapping IIIT-Delhi building meters to VFSTR building IDs
IIITD_TO_VFSTR_MAP = {
    "Academic": "BLK-A",       # Academic Block A - Engineering
    "Lecture": "BLK-B",        # Academic Block B - Sciences
    "Facilities": "BLK-C",     # Academic Block C - Management & Humanities
    "Mess": "LAB-CSE",         # Computer Science Labs (High IT / continuous power profile)
    "Library": "LIB",          # Central Library
    "Boys_main": "HST-B",      # Boys Hostel
    "Girls_main": "HST-G",     # Girls Hostel
}


def load_iiitd_power_data() -> pd.DataFrame:
    """Load, parse timestamps, and convert IIIT-D empirical building power readings."""
    file_path = IIITD_RAW_DIR / "all_buildings_power.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"IIITD raw dataset file not found at: {file_path}")

    logger.info("Loading IIIT-Delhi raw energy dataset from %s", file_path)
    df = pd.read_csv(file_path)

    # Convert UNIX timestamp to Asia/Kolkata timezone
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True).dt.tz_convert(CAMPUS["timezone"]).dt.tz_localize(None)

    # Sort and handle duplicates
    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")

    # Resample to 15-minute intervals to match EcoMind simulation cadence
    df.set_index("timestamp", inplace=True)
    df_resampled = df.resample("15min").mean()

    # Fill missing values using time interpolation + backward/forward fill
    df_clean = df_resampled.interpolate(method="time").bfill().ffill()

    # Convert Power (W) to Power (kW) and energy per 15-min interval (kWh = kW * 0.25)
    for col in df_clean.columns:
        df_clean[f"{col}_kw"] = df_clean[col] / 1000.0
        df_clean[f"{col}_kwh"] = df_clean[f"{col}_kw"] * 0.25

    df_clean.reset_index(inplace=True)
    logger.info("Processed %d resampled 15-minute rows from IIIT-D dataset", len(df_clean))
    return df_clean


def build_grounded_telemetry(simulated_df: pd.DataFrame, empirical_df: pd.DataFrame) -> pd.DataFrame:
    """Calibrate simulated telemetry with empirical power metrics from IIIT-D dataset."""
    out = simulated_df.copy()
    logger.info("Grounding simulated telemetry with empirical IIIT-D power distributions...")

    # Calculate empirical mean & std power per building type from IIIT-D
    empirical_stats = {}
    for iiit_col, vfstr_id in IIITD_TO_VFSTR_MAP.items():
        if iiit_col in empirical_df.columns:
            kwh_col = f"{iiit_col}_kwh"
            if kwh_col in empirical_df.columns:
                empirical_stats[vfstr_id] = {
                    "mean_kwh": float(empirical_df[kwh_col].mean()),
                    "std_kwh": float(empirical_df[kwh_col].std()),
                }

    # Calibrate room-level energy to match empirical scale while retaining physical sensor variables
    if empirical_stats:
        for b_id, stats in empirical_stats.items():
            mask = out["building_id"] == b_id
            if mask.any() and stats["mean_kwh"] > 0:
                sim_mean = out.loc[mask, "energy_kwh"].mean()
                if sim_mean > 0:
                    scaling_factor = stats["mean_kwh"] / sim_mean
                    # Smoothly adjust room energy while maintaining physical constraints
                    out.loc[mask, "energy_kwh"] = np.round(out.loc[mask, "energy_kwh"] * (0.6 + 0.4 * scaling_factor), 5)

    return out
