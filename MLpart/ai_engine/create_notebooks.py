"""Create one Jupyter notebook per Phase 1 stage."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NB_DIR = ROOT / "notebooks"
NB_DIR.mkdir(parents=True, exist_ok=True)


def notebook(cells: list[tuple[str, str]]) -> dict:
    out_cells = []
    for kind, source in cells:
        src = source.strip() + "\n"
        if kind == "md":
            out_cells.append(
                {"cell_type": "markdown", "metadata": {}, "source": [line + "\n" for line in src.split("\n")]}
            )
        else:
            out_cells.append(
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [line + "\n" for line in src.split("\n")],
                }
            )
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "cells": out_cells,
    }


NOTEBOOKS = {
    "01_digital_twin.ipynb": [
        ("md", "# Stage 1 — Campus Digital Twin\nVignan University, Vadlamudi. Run only if `data/generated/buildings.csv` is missing."),
        ("code", "import sys\nfrom pathlib import Path\nROOT = Path.cwd() if (Path.cwd() / 'run_phase1.py').exists() else Path.cwd().parent\nsys.path.insert(0, str(ROOT))\nimport pandas as pd\nfrom src.agents.digital_twin import run_stage1\nfrom src.utils.config import GENERATED_DIR\n\nif not (GENERATED_DIR / 'buildings.csv').exists():\n    print(run_stage1())\nelse:\n    print('Stage 1 artifacts already present')\nbuildings = pd.read_csv(GENERATED_DIR / 'buildings.csv')\nrooms = pd.read_csv(GENERATED_DIR / 'rooms.csv')\ndevices = pd.read_csv(GENERATED_DIR / 'devices.csv')\ndisplay(buildings)\ndisplay(rooms.head())\nprint('rooms', len(rooms), 'devices', len(devices))"),
    ],
    "02_iot_simulation.ipynb": [
        ("md", "# Stage 2 — Live IoT Sensor Simulation\nSynthetic 15-minute campus telemetry (≥250,000 rows)."),
        ("code", "import sys\nfrom pathlib import Path\nROOT = Path.cwd() if (Path.cwd() / 'run_phase1.py').exists() else Path.cwd().parent\nsys.path.insert(0, str(ROOT))\nimport pandas as pd\nfrom src.utils.config import GENERATED_DIR\npath = GENERATED_DIR / 'sensor_readings.csv'\ndf = pd.read_csv(path, parse_dates=['timestamp'])\nprint(len(df), df['timestamp'].min(), df['timestamp'].max())\nprint(df.groupby('category')['energy_kwh'].sum())"),
    ],
    "03_preprocessing.ipynb": [
        ("md", "# Stage 3 — Preprocessing & feature pipeline"),
        ("code", "import sys, joblib\nfrom pathlib import Path\nROOT = Path.cwd() if (Path.cwd() / 'run_phase1.py').exists() else Path.cwd().parent\nsys.path.insert(0, str(ROOT))\nimport pandas as pd\nfrom src.utils.config import PROCESSED_DIR, MODELS_DIR\ndf = pd.read_csv(PROCESSED_DIR / 'processed_sensor_data.csv', parse_dates=['timestamp'])\nprint(df.isna().sum().sum(), df.duplicated(['room_id','timestamp']).sum())\nprint(df.columns.tolist())\npipe = joblib.load(MODELS_DIR / 'feature_pipeline.pkl')\nprint(pipe.keys())"),
    ],
    "04_eda.ipynb": [
        ("md", "# Stage 4 — Exploratory Data Analysis\nFull chart pack is in `reports/stage4_eda_report.pdf`. Every chart has a written observation in `reports/stage4_eda_summary.md`."),
        ("code", "import sys\nfrom pathlib import Path\nROOT = Path.cwd() if (Path.cwd() / 'run_phase1.py').exists() else Path.cwd().parent\nsys.path.insert(0, str(ROOT))\nimport pandas as pd\nimport matplotlib.pyplot as plt\nfrom src.utils.config import PROCESSED_DIR, REPORTS_DIR\n\ndf = pd.read_csv(PROCESSED_DIR / 'processed_sensor_data.csv', parse_dates=['timestamp'])\ndaily = df.groupby(df['timestamp'].dt.date)['energy_kwh'].sum()\nax = daily.plot(figsize=(10,4), title='Daily campus energy (kWh)')\nplt.tight_layout()\nprint((REPORTS_DIR / 'stage4_eda_summary.md').read_text(encoding='utf-8')[:1500])"),
    ],
    "05_forecasting.ipynb": [
        ("md", "# Stage 5 — Demand forecasting\nLinear Regression, Random Forest, XGBoost, and Prophet (if installed). Best model is selected by MAE."),
        ("code", "import sys, json, joblib\nfrom pathlib import Path\nROOT = Path.cwd() if (Path.cwd() / 'run_phase1.py').exists() else Path.cwd().parent\nsys.path.insert(0, str(ROOT))\nimport pandas as pd\nfrom src.utils.config import GENERATED_DIR, MODELS_DIR, REPORTS_DIR\nprint(json.loads((REPORTS_DIR / 'stage5_forecasting.json').read_text())['metrics'])\nfi = pd.read_csv(GENERATED_DIR / 'feature_importance.csv')\ndisplay(fi.sort_values('importance', ascending=False))\npack = joblib.load(MODELS_DIR / 'forecast_model.pkl')\nprint(pack['model_name'], pack['metrics'])"),
    ],
    "06_anomaly_detection.ipynb": [
        ("md", "# Stage 6 — Anomaly detection\nIsolation Forest plus rule overlay for injected operational faults."),
        ("code", "import sys\nfrom pathlib import Path\nROOT = Path.cwd() if (Path.cwd() / 'run_phase1.py').exists() else Path.cwd().parent\nsys.path.insert(0, str(ROOT))\nimport pandas as pd\nfrom src.utils.config import GENERATED_DIR\nalerts = pd.read_csv(GENERATED_DIR / 'alerts.csv')\nprint(alerts['severity'].value_counts())\nprint(alerts[['room_id','severity','confidence','reason','recommended_action']].head(10))"),
    ],
    "07_optimization.ipynb": [
        ("md", "# Stage 7 — Energy optimization recommendations"),
        ("code", "import sys, json\nfrom pathlib import Path\nROOT = Path.cwd() if (Path.cwd() / 'run_phase1.py').exists() else Path.cwd().parent\nsys.path.insert(0, str(ROOT))\nimport pandas as pd\nfrom src.utils.config import GENERATED_DIR\nrecs = json.loads((GENERATED_DIR / 'recommendations.json').read_text())\nprint(len(recs))\nfor r in recs:\n    print(r['priority_score'], r['title'], r['energy_saved_kwh'], 'kWh /', r['money_saved_inr'], 'INR')"),
    ],
    "08_sustainability.ipynb": [
        ("md", "# Stage 8 — Sustainability analytics"),
        ("code", "import sys, json\nfrom pathlib import Path\nROOT = Path.cwd() if (Path.cwd() / 'run_phase1.py').exists() else Path.cwd().parent\nsys.path.insert(0, str(ROOT))\nimport pandas as pd\nfrom src.utils.config import GENERATED_DIR\nscores = pd.read_csv(GENERATED_DIR / 'building_scores.csv')\ndisplay(scores[['leaderboard_rank','building_name','efficiency_score','energy_kwh']])\nprint(json.dumps(json.loads((GENERATED_DIR / 'weekly_report.json').read_text())['monthly_savings'], indent=2))"),
    ],
}


def main() -> None:
    for name, cells in NOTEBOOKS.items():
        path = NB_DIR / name
        path.write_text(json.dumps(notebook(cells), indent=1), encoding="utf-8")
        print("wrote", path)


if __name__ == "__main__":
    main()
