import json
from pathlib import Path
import pandas as pd
import pickle

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ML_ENGINE_DIR = BASE_DIR / "MLpart" / "ai_engine"
GENERATED_DATA_DIR = ML_ENGINE_DIR / "data" / "generated"
PROCESSED_DATA_DIR = ML_ENGINE_DIR / "data" / "processed"
RAW_DATA_DIR = ML_ENGINE_DIR / "data" / "raw"
MODELS_DIR = ML_ENGINE_DIR / "models"


def get_generated_path(filename: str) -> Path:
    p1 = GENERATED_DATA_DIR / filename
    if p1.exists():
        return p1
    p2 = PROCESSED_DATA_DIR / filename
    if p2.exists():
        return p2
    p3 = RAW_DATA_DIR / filename
    if p3.exists():
        return p3
    return p1


def get_model_path(filename: str) -> Path:
    return MODELS_DIR / filename


def load_buildings_df() -> pd.DataFrame:
    path = get_generated_path("buildings.csv")
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def load_recommendations_json() -> list[dict]:
    path = get_generated_path("recommendations.json")
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_weekly_report_json() -> dict:
    path = get_generated_path("weekly_report.json")
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_forecast_df() -> pd.DataFrame:
    path = get_generated_path("forecast_predictions.csv")
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def load_alerts_df() -> pd.DataFrame:
    path = get_generated_path("alerts.csv")
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def load_model(filename: str):
    path = get_model_path(filename)
    if path.exists():
        with open(path, "rb") as f:
            return pickle.load(f)
    return None
