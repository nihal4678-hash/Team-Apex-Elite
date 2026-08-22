"""Global configuration for EcoMind AI (Vignan University, Vadlamudi)."""

from __future__ import annotations

from pathlib import Path

RANDOM_SEED = 42

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
GENERATED_DIR = DATA_DIR / "generated"
EXTERNAL_DIR = DATA_DIR / "external"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
MLRUNS_DIR = PROJECT_ROOT / "mlruns"
IIITD_RAW_DIR = RAW_DIR / "iiitd_dataset" / "energy_dataset"

CAMPUS = {
    "name": "Vignan University",
    "legal_name": "Vignan's Foundation for Science, Technology & Research",
    "location": "Vadlamudi, Guntur District, Andhra Pradesh, India",
    "latitude": 16.2347,
    "longitude": 80.5516,
    "timezone": "Asia/Kolkata",
    "grid_voltage_v": 230.0,
    "grid_frequency_hz": 50.0,
    "tariff_inr_per_kwh": 8.75,
    "grid_carbon_kg_per_kwh": 0.82,
}

# VFSTR 2024-25 Carbon Audit Official Grounding Targets
VFSTR_AUDIT = {
    "annual_electricity_kwh": 2_500_000.0,
    "solar_generation_kwh": 975_000.0,
    "grid_electricity_kwh": 1_525_000.0,
    "renewable_share_pct": 39.0,
    "grid_share_pct": 61.0,
    "solar_pv_capacity_mw": 1.0,
    "total_built_up_area_sqm": 111_916.33,
    "total_campus_area_sqm": 137_898.9,
    "smart_building_area_share_pct": 81.15,
    "led_lamp_count": 10_000,
    "led_lamp_efficient_count": 8_500,
    "led_adoption_pct": 85.0,
    "fan_count": 2_100,
    "fan_efficient_count": 1_575,
    "fan_efficiency_pct": 75.0,
    "diesel_consumption_litres": 18_000.0,
    "scope1_dg_emissions_tco2": 48.2,
    "scope2_grid_emissions_tco2": 2131.1,
    "total_carbon_footprint_tco2": 2179.1,
    "solar_avoided_emissions_tco2": 799.5,
    "per_capita_carbon_footprint_tco2": 0.541,
}

# Andhra Pradesh tropical climate priors (Vadlamudi / Guntur)
WEATHER = {
    "mean_temp_c": 31.5,
    "daily_amplitude_c": 6.5,
    "seasonal_amplitude_c": 4.0,
    "mean_humidity_pct": 68.0,
}

SIMULATION = {
    "start": "2025-07-01 00:00:00",
    "end": "2025-08-08 23:45:00",
    "freq": "15min",
    "exam_start": "2025-07-28",
    "exam_end": "2025-08-08",
}

WORKING_HOURS = (8, 18)  # inclusive start, exclusive end in local time
TARIFF_PEAK_HOURS = (18, 22)

DEVICE_LOADS_W = {
    "light": 28.0,
    "fan": 75.0,
    "ac": 1650.0,
    "computer": 180.0,
    "projector": 260.0,
}

