import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.database.database import SessionLocal, init_db
from app.models.db_models import AgentRunDB
from app.services import ml_bridge
from app.services.artifact_ingestion import artifact_ingestion_service

logger = logging.getLogger("ecomind.orchestrator")

STAGE_METADATA = {
    1: {"name": "Digital Twin", "required_files": []},
    2: {"name": "IoT Simulation", "required_files": ["buildings.csv"]},
    3: {"name": "Preprocessing & Feature Pipeline", "required_files": ["sensor_readings.csv"]},
    4: {"name": "EDA & Reporting", "required_files": ["processed_sensor_data.csv"]},
    5: {"name": "Demand Forecasting Model", "required_files": ["processed_sensor_data.csv"]},
    6: {"name": "Anomaly & Leak Detection", "required_files": ["sensor_readings.csv", "forecast_predictions.csv"]},
    7: {"name": "Rule & Optimization Engine", "required_files": ["forecast_predictions.csv", "alerts.csv"]},
    8: {"name": "Sustainability & ESG Analytics", "required_files": ["recommendations.json"]},
}

STAGE_OUTPUT_ARTIFACTS = {
    1: ("buildings", "buildings.csv"),
    2: ("iot_telemetry", "sensor_readings.csv"),
    3: ("processed_data", "processed_sensor_data.csv"),
    4: ("eda_summary", "stage4_eda_summary.md"),
    5: ("forecasts", "forecast_predictions.csv"),
    6: ("alerts", "alerts.csv"),
    7: ("recommendations", "recommendations.json"),
    8: ("sustainability", "weekly_report.json"),
}


class AgentOrchestrationService:
    @staticmethod
    def check_stage_dependencies(stage: int) -> tuple[bool, str]:
        meta = STAGE_METADATA.get(stage)
        if not meta:
            return False, f"Invalid stage number: {stage}"

        missing = []
        for req_file in meta["required_files"]:
            path = ml_bridge.get_generated_path(req_file)
            if not path.exists():
                missing.append(req_file)

        if missing:
            return False, f"Prerequisite upstream files missing for Stage {stage} ({meta['name']}): {missing}"
        return True, "Dependencies satisfied"

    @classmethod
    def execute_stage(
        cls, run_id: str, stage: int, db: Session = None
    ) -> dict:
        init_db()
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True

        meta = STAGE_METADATA.get(stage)
        if not meta:
            return {"run_id": run_id, "stage": stage, "status": "failed", "reason": "Invalid stage number"}

        # 1. Dependency check
        deps_ok, dep_msg = cls.check_stage_dependencies(stage)
        if not deps_ok:
            run_db = AgentRunDB(
                run_id=run_id,
                stage=stage,
                stage_name=meta["name"],
                status="failed",
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                failure_reason=dep_msg,
            )
            db.add(run_db)
            db.commit()
            if close_after:
                db.close()
            return {
                "run_id": run_id,
                "stage": stage,
                "stage_name": meta["name"],
                "status": "failed",
                "failure_reason": dep_msg,
            }

        # 2. Record start of stage execution
        start_t = datetime.now(timezone.utc)
        run_db = AgentRunDB(
            run_id=run_id,
            stage=stage,
            stage_name=meta["name"],
            status="running",
            start_time=start_t,
        )
        db.add(run_db)
        db.commit()

        # 3. Simulate or execute stage step
        try:
            logger.info(f"Executing Stage {stage} ({meta['name']}) for run {run_id}...")

            # Validate output artifact after stage
            art_type, art_file = STAGE_OUTPUT_ARTIFACTS.get(stage, (None, None))
            report_data = {}
            if art_type and art_file:
                ingest_res = artifact_ingestion_service.ingest_artifact(run_id, art_type, art_file, db=db)
                report_data = ingest_res

            end_t = datetime.now(timezone.utc)
            run_db.status = "success"
            run_db.end_time = end_t
            run_db.report_json = json.dumps(report_data)
            db.commit()

            res = {
                "run_id": run_id,
                "stage": stage,
                "stage_name": meta["name"],
                "status": "success",
                "duration_seconds": (end_t - start_t).total_seconds(),
                "output_report": report_data,
            }
        except Exception as e:
            end_t = datetime.now(timezone.utc)
            run_db.status = "failed"
            run_db.end_time = end_t
            run_db.failure_reason = str(e)
            db.commit()
            logger.error(f"Stage {stage} failed: {e}")
            res = {
                "run_id": run_id,
                "stage": stage,
                "stage_name": meta["name"],
                "status": "failed",
                "failure_reason": str(e),
            }
        finally:
            if close_after:
                db.close()

        return res

    @classmethod
    def execute_full_pipeline(cls, run_id: Optional[str] = None, db: Session = None) -> dict:
        if not run_id:
            now_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            run_id = f"PIPELINE-RUN-{now_str}"

        results = {}
        for stage in range(1, 9):
            stage_res = cls.execute_stage(run_id, stage, db=db)
            results[f"stage_{stage}"] = stage_res
            if stage_res["status"] == "failed":
                logger.warning(f"Pipeline run {run_id} blocked at Stage {stage}.")
                break
        return {"run_id": run_id, "stage_results": results}

    @staticmethod
    def get_run_history(db: Session = None) -> list[dict]:
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True
        try:
            runs_db = db.query(AgentRunDB).order_by(AgentRunDB.id.desc()).all()
            return [
                {
                    "id": r.id,
                    "run_id": r.run_id,
                    "stage": r.stage,
                    "stage_name": r.stage_name,
                    "status": r.status,
                    "start_time": r.start_time.isoformat() if r.start_time else None,
                    "end_time": r.end_time.isoformat() if r.end_time else None,
                    "retry_count": r.retry_count,
                    "failure_reason": r.failure_reason,
                    "report": json.loads(r.report_json) if r.report_json else None,
                }
                for r in runs_db
            ]
        finally:
            if close_after:
                db.close()


agent_orchestration_service = AgentOrchestrationService()
