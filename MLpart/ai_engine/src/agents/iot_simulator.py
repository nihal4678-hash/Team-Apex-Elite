"""Stage 2 — Vectorized live IoT sensor simulation for the campus digital twin."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.utils.config import (
    CAMPUS,
    DEVICE_LOADS_W,
    GENERATED_DIR,
    RANDOM_SEED,
    SIMULATION,
    WEATHER,
    WORKING_HOURS,
)
from src.utils.io import load_csv, save_csv, save_json
from src.utils.logging_utils import get_logger
from src.utils.validation import ValidationResult

logger = get_logger("ecomind.iot")


def _occupancy_fraction(
    category: np.ndarray,
    hour: np.ndarray,
    is_weekend: np.ndarray,
    is_exam: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return occupancy as a fraction of room capacity."""
    frac = np.zeros(len(category), dtype=np.float32)
    working = (hour >= WORKING_HOURS[0]) & (hour < WORKING_HOURS[1])
    lunch = (hour >= 12) & (hour < 14)
    night = (hour >= 21) | (hour < 6)
    evening = (hour >= 18) & (hour < 22)

    academic = np.isin(category, ["academic", "computer_lab"])
    frac[academic & working & ~is_weekend] = 0.55
    frac[academic & lunch & ~is_weekend] = 0.22
    frac[academic & working & is_weekend] = 0.08
    frac[academic & ~working] = 0.02
    frac[academic & is_exam & working] = 0.18  # classes thin out during exams

    lab = category == "computer_lab"
    frac[lab & working & ~is_weekend] = 0.72
    frac[lab & is_exam & working] = 0.85

    library = category == "library"
    frac[library & working] = 0.45
    frac[library & evening] = 0.55
    frac[library & is_exam] = np.maximum(frac[library & is_exam], 0.78)
    frac[library & is_weekend & working] = 0.35
    frac[library & night] = 0.04

    hostel = category == "hostel"
    frac[hostel & night] = 0.88
    frac[hostel & evening] = 0.70
    frac[hostel & working & ~is_weekend] = 0.28
    frac[hostel & is_weekend] = 0.62
    frac[hostel & lunch] = 0.40

    admin = category == "admin"
    frac[admin & working & ~is_weekend] = 0.80
    frac[admin & working & is_weekend] = 0.12
    frac[admin & ~working] = 0.02

    cafe = category == "cafeteria"
    frac[cafe & lunch] = 0.85
    frac[cafe & (hour >= 7) & (hour < 10)] = 0.55
    frac[cafe & (hour >= 19) & (hour < 21)] = 0.60
    frac[cafe & working & ~lunch] = 0.25
    frac[cafe & is_weekend] = np.maximum(frac[cafe & is_weekend] * 0.7, 0.15)
    frac[cafe & night] = 0.02

    noise = rng.normal(0.0, 0.08, size=len(frac)).astype(np.float32)
    return np.clip(frac + noise, 0.0, 1.0)


def simulate_sensor_stream(rooms: pd.DataFrame, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    timestamps = pd.date_range(SIMULATION["start"], SIMULATION["end"], freq=SIMULATION["freq"])
    n_ts = len(timestamps)
    n_rooms = len(rooms)
    logger.info("Simulating %s timestamps × %s rooms = %s rows", n_ts, n_rooms, n_ts * n_rooms)

    ts = np.repeat(timestamps.to_numpy(), n_rooms)
    room_idx = np.tile(np.arange(n_rooms), n_ts)

    ts_utc = pd.to_datetime(ts)
    hour = ts_utc.hour.to_numpy()
    minute = ts_utc.minute.to_numpy()
    dow = ts_utc.dayofweek.to_numpy()
    is_weekend = dow >= 5
    exam_start = pd.Timestamp(SIMULATION["exam_start"])
    exam_end = pd.Timestamp(SIMULATION["exam_end"])
    is_exam = np.asarray((ts_utc.normalize() >= exam_start) & (ts_utc.normalize() <= exam_end))

    day_of_year = ts_utc.dayofyear.to_numpy()
    hour_frac = hour + minute / 60.0
    outdoor_temp = (
        WEATHER["mean_temp_c"]
        + WEATHER["seasonal_amplitude_c"] * np.sin(2 * np.pi * (day_of_year - 200) / 365.0)
        + WEATHER["daily_amplitude_c"] * np.sin(2 * np.pi * (hour_frac - 15) / 24.0)
        + rng.normal(0, 0.6, size=len(ts))
    )
    humidity = np.clip(
        WEATHER["mean_humidity_pct"]
        - 0.8 * (outdoor_temp - WEATHER["mean_temp_c"])
        + rng.normal(0, 3.0, size=len(ts)),
        35,
        95,
    )

    category = rooms["category"].to_numpy()[room_idx]
    capacity = rooms["capacity"].to_numpy()[room_idx].astype(np.int32)
    hvac = rooms["hvac_available"].to_numpy()[room_idx].astype(bool)
    n_lights = rooms["lighting_count"].to_numpy()[room_idx]
    n_fans = rooms["fan_count"].to_numpy()[room_idx]
    n_ac = rooms["ac_count"].to_numpy()[room_idx]
    n_computers = rooms["computer_count"].to_numpy()[room_idx]
    n_projectors = rooms["projector_count"].to_numpy()[room_idx]

    occ_frac = _occupancy_fraction(category, hour, is_weekend, is_exam, rng)
    occupancy = np.minimum(capacity, np.round(occ_frac * capacity).astype(np.int32))
    occupied = occupancy > 0

    lights_on = occupied | ((category == "hostel") & ((hour >= 18) | (hour < 6)))
    # leftover lights in empty academic rooms (wastage signal, still physically valid)
    leftover = (~occupied) & np.isin(category, ["academic", "computer_lab", "admin"]) & (hour >= 8) & (hour < 20)
    lights_on = lights_on | (leftover & (rng.random(len(ts)) < 0.04))

    hot = outdoor_temp >= 29.5
    fans_on = occupied & ((~hvac) | hot | (category == "hostel"))
    ac_on = hvac & occupied & (outdoor_temp >= 28.0) & (hour >= 8) & (hour < 20)
    ac_on = ac_on | (hvac & occupied & (category == "computer_lab") & (hour >= 8) & (hour < 21))
    projector_on = occupied & (n_projectors > 0) & (hour >= 9) & (hour < 17) & ~is_weekend & (rng.random(len(ts)) < 0.45)
    computer_usage = np.where(
        n_computers > 0,
        np.clip(occupancy / np.maximum(capacity, 1) * rng.uniform(0.6, 1.05, size=len(ts)), 0, 1),
        0.0,
    )
    computer_usage = np.where(n_computers > 0, np.minimum(computer_usage, 1.0), 0.0)
    computers_active = np.round(computer_usage * n_computers).astype(np.int32)

    indoor_temp = outdoor_temp - 1.8 + rng.normal(0, 0.4, size=len(ts))
    indoor_temp = np.where(ac_on, indoor_temp - 5.5, indoor_temp)
    indoor_temp = np.where(fans_on & ~ac_on, indoor_temp - 1.2, indoor_temp)
    indoor_temp = np.where(~occupied, outdoor_temp - 0.4, indoor_temp)

    lights_active = np.where(lights_on, n_lights, 0)
    fans_active = np.where(fans_on, n_fans, 0)
    ac_active = np.where(ac_on, n_ac, 0)
    proj_active = np.where(projector_on, n_projectors, 0)

    power_w = (
        lights_active * DEVICE_LOADS_W["light"]
        + fans_active * DEVICE_LOADS_W["fan"]
        + ac_active * DEVICE_LOADS_W["ac"]
        + computers_active * DEVICE_LOADS_W["computer"]
        + proj_active * DEVICE_LOADS_W["projector"]
    )
    # standby + corridor/always-on load
    power_w = power_w + 40.0 + rng.normal(0, 8.0, size=len(ts))
    power_w = np.clip(power_w, 15.0, None)

    voltage = CAMPUS["grid_voltage_v"] + rng.normal(0, 2.2, size=len(ts))
    frequency = CAMPUS["grid_frequency_hz"] + rng.normal(0, 0.04, size=len(ts))
    power_factor = np.clip(0.92 - 0.04 * ac_on.astype(float) + rng.normal(0, 0.015, size=len(ts)), 0.75, 0.99)
    current = power_w / (np.maximum(voltage, 1.0) * power_factor * np.sqrt(3) * 0.6 + 1e-6)
    # treat as single-phase campus branch: I = P / (V * PF)
    current = power_w / (np.maximum(voltage, 1.0) * np.maximum(power_factor, 0.7))

    interval_h = pd.Timedelta(SIMULATION["freq"]).total_seconds() / 3600.0
    energy_kwh = (power_w / 1000.0) * interval_h

    df = pd.DataFrame(
        {
            "timestamp": ts_utc,
            "building_id": rooms["building_id"].to_numpy()[room_idx],
            "building_name": rooms["building_name"].to_numpy()[room_idx],
            "room_id": rooms["room_id"].to_numpy()[room_idx],
            "category": category,
            "occupancy": occupancy,
            "room_capacity": capacity,
            "indoor_temperature_c": np.round(indoor_temp, 2),
            "outdoor_temperature_c": np.round(outdoor_temp, 2),
            "humidity_pct": np.round(humidity, 2),
            "lights_status": lights_on.astype(np.int8),
            "fans_status": fans_on.astype(np.int8),
            "ac_status": ac_on.astype(np.int8),
            "projector_status": projector_on.astype(np.int8),
            "computer_usage": np.round(computer_usage, 3),
            "computers_active": computers_active,
            "voltage_v": np.round(voltage, 2),
            "current_a": np.round(current, 3),
            "power_factor": np.round(power_factor, 3),
            "frequency_hz": np.round(frequency, 3),
            "power_w": np.round(power_w, 2),
            "energy_kwh": np.round(energy_kwh, 5),
        }
    )
    return df


def validate_sensor_readings(df: pd.DataFrame) -> ValidationResult:
    result = ValidationResult(stage="stage2_iot_simulation", passed=True)
    result.add("min_records", len(df) >= 250_000, f"n={len(df)}")
    ts = pd.to_datetime(df["timestamp"], errors="coerce")
    result.add("timestamps_parseable", ts.notna().all(), f"nulls={int(ts.isna().sum())}")
    result.add("no_future_clock_errors", (ts.dt.year >= 2024).all() and (ts.dt.year <= 2027).all(), "")
    result.add("energy_positive", (df["energy_kwh"] > 0).all(), f"min={df['energy_kwh'].min()}")
    result.add(
        "occupancy_le_capacity",
        (df["occupancy"] <= df["room_capacity"]).all(),
        f"violations={int((df['occupancy'] > df['room_capacity']).sum())}",
    )
    result.add("occupancy_non_negative", (df["occupancy"] >= 0).all(), "")
    return result


def run_stage2() -> dict[str, Any]:
    rooms = load_csv(GENERATED_DIR / "rooms.csv")
    df = simulate_sensor_stream(rooms)
    
    # Check if IIIT-Delhi dataset is available for empirical calibration
    try:
        from src.preprocessing.dataset_adapter import load_iiitd_power_data, build_grounded_telemetry
        iiitd_df = load_iiitd_power_data()
        df = build_grounded_telemetry(df, iiitd_df)
        logger.info("Stage 2 telemetry successfully grounded with empirical IIIT-D energy data.")
    except Exception as exc:
        logger.warning("Empirical dataset grounding skipped or failed (%s). Proceeding with simulated stream.", exc)

    path = save_csv(df, GENERATED_DIR / "sensor_readings.csv")
    validation = validate_sensor_readings(df)
    report = {
        "stage": 2,
        "name": "Live IoT Sensor Simulation Agent",
        "validation": validation.to_dict(),
        "paths": {"sensor_readings": str(path)},
        "summary": {
            "rows": int(len(df)),
            "rooms": int(df["room_id"].nunique()),
            "start": str(df["timestamp"].min()),
            "end": str(df["timestamp"].max()),
            "total_energy_kwh": float(df["energy_kwh"].sum()),
        },
        "pending_issues": validation.pending_issues,
    }
    save_json(GENERATED_DIR.parent.parent / "reports" / "stage2_iot_simulation.json", report)
    if not validation.passed:
        raise RuntimeError(f"Stage 2 validation failed: {validation.pending_issues}")
    logger.info("Stage 2 complete: %s rows", len(df))
    return report
