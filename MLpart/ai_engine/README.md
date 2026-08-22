# EcoMind AI — Phase 1 AI/ML Engine

Smart-campus energy optimization stack for **Vignan University (VFSTR), Vadlamudi, Guntur District, Andhra Pradesh**.

Phase 1 delivers the digital twin, IoT simulation, preprocessing, EDA, forecasting, anomaly detection, recommendations, and sustainability analytics. Phase 2 will wrap these modules in FastAPI.

## Quick start

```bash
cd ai_engine
python -m pip install -r requirements.txt
python run_phase1.py
```

Resume from a stage (previous artifacts must already exist and have passed validation):

```bash
python run_phase1.py --start 5 --end 8
```

## Layout

```
ai_engine/
├── data/generated/     digital twin + sensor + model outputs
├── data/processed/     processed_sensor_data.csv
├── models/             feature_pipeline.pkl, forecast_model.pkl, anomaly_model.pkl
├── notebooks/          one notebook per stage
├── reports/            validation JSON, EDA PDF, markdown
├── mlruns/             MLflow tracking
└── src/                reusable agents
```

## Stage map

| Stage | Agent | Primary outputs |
|------:|-------|-----------------|
| 1 | Digital twin | `buildings.csv`, `rooms.csv`, `devices.csv`, `campus_metadata.json` |
| 2 | IoT simulator | `sensor_readings.csv` (≥250k rows, 15-min) |
| 3 | Preprocessing | `processed_sensor_data.csv`, `feature_pipeline.pkl` |
| 4 | EDA | `stage4_eda_report.pdf`, `stage4_eda_summary.md` |
| 5 | Forecasting | `forecast_model.pkl`, `forecast_predictions.csv`, `feature_importance.csv` |
| 6 | Anomaly detection | `anomaly_model.pkl`, `anomaly_predictions.csv`, `alerts.csv` |
| 7 | Optimization | `recommendations.json`, `optimization_summary.csv` |
| 8 | Sustainability | `sustainability_metrics.csv`, `building_scores.csv`, `weekly_report.json` |

## Economics & carbon

- Tariff: **₹8.75 / kWh** (AP commercial-style campus assumption)
- Grid carbon: **0.82 kg CO₂ / kWh** (Indian grid factor)

## Reproducibility

All generators use `RANDOM_SEED = 42` (`src/utils/config.py`).
