"""Master Pipeline Orchestrator — EcoMind AI End-to-End 8-Stage Execution."""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logging_utils import get_logger
from src.agents.digital_twin import run_stage1
from src.agents.iot_simulator import run_stage2
from src.preprocessing.pipeline import run_stage3
from src.agents.eda import run_stage4
from src.forecasting.trainer import run_stage5
from src.anomaly_detection.detector import run_stage6
from src.recommendation.optimizer import run_stage7
from src.sustainability.reporter import run_stage8

logger = get_logger("ecomind.master_pipeline")


def run_pipeline() -> dict[int, dict]:
    """Execute all 8 stages sequentially with strict validation gating at every stage."""
    start_time = time.time()
    logger.info("=========================================================")
    logger.info("  Starting EcoMind AI Master Pipeline (8 Stages) ")
    logger.info("  Campus: VFSTR Vadlamudi | Empirical: IIIT-Delhi ")
    logger.info("=========================================================")

    results = {}

    stages = [
        (1, "Digital Twin Generator", run_stage1),
        (2, "IoT Sensor Simulator & Grounding", run_stage2),
        (3, "Cleaning & Feature Engineering", run_stage3),
        (4, "Exploratory Data Analysis Agent", run_stage4),
        (5, "Demand Forecasting Agent", run_stage5),
        (6, "Anomaly Detection Agent", run_stage6),
        (7, "Optimization & Recommendation Agent", run_stage7),
        (8, "Sustainability & GHG Audit Agent", run_stage8),
    ]

    for stage_num, stage_name, stage_fn in stages:
        t0 = time.time()
        logger.info("\n---------------------------------------------------------")
        logger.info("  Running Stage %d: %s", stage_num, stage_name)
        logger.info("---------------------------------------------------------")

        report = stage_fn()
        elapsed = time.time() - t0

        validation = report.get("validation", {})
        passed = validation.get("passed", False)

        if not passed:
            logger.error("Stage %d FAILED validation! Halting pipeline execution.", stage_num)
            logger.error("Pending issues: %s", report.get("pending_issues"))
            sys.exit(1)

        logger.info("Stage %d PASSED in %.2f seconds", stage_num, elapsed)
        results[stage_num] = report

    total_time = time.time() - start_time
    logger.info("\n=========================================================")
    logger.info("  ALL 8 STAGES COMPLETED SUCCESSFULLY in %.2f seconds! ", total_time)
    logger.info("=========================================================")
    return results


if __name__ == "__main__":
    run_pipeline()
