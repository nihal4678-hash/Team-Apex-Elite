"""Phase 1 orchestrator — run validated stages in order."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.agents.digital_twin import run_stage1
from src.agents.eda import run_stage4
from src.agents.iot_simulator import run_stage2
from src.anomaly_detection.detector import run_stage6
from src.forecasting.trainer import run_stage5
from src.preprocessing.pipeline import run_stage3
from src.recommendation.engine import run_stage7
from src.sustainability.metrics import run_stage8
from src.utils.io import save_json
from src.utils.logging_utils import get_logger

logger = get_logger("ecomind.pipeline")

STAGES = {
    1: run_stage1,
    2: run_stage2,
    3: run_stage3,
    4: run_stage4,
    5: run_stage5,
    6: run_stage6,
    7: run_stage7,
    8: run_stage8,
}


def run_from(start: int = 1, end: int = 8) -> dict:
    reports = {}
    for stage in range(start, end + 1):
        logger.info("===== START STAGE %s =====", stage)
        reports[f"stage_{stage}"] = STAGES[stage]()
        logger.info("===== STAGE %s PASSED =====", stage)
    save_json(ROOT / "reports" / "phase1_pipeline.json", reports)
    return reports


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EcoMind AI Phase 1 pipeline")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=8)
    args = parser.parse_args()
    run_from(args.start, args.end)
