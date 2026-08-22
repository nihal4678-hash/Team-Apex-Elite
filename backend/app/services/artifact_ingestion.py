import hashlib
import json
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.database.database import SessionLocal, init_db
from app.models.db_models import ArtifactIngestDB
from app.services import ml_bridge

logger = logging.getLogger("ecomind.ingestion")

REQUIRED_SCHEMAS = {
    "buildings": ["building_id", "building_name", "category", "area_sqm"],
    "forecasts": ["timestamp", "building_id", "predicted_energy_kwh"],
    "alerts": ["timestamp", "building_id", "severity", "reason"],
    "recommendations": ["recommendation_id", "category", "title", "energy_saved_kwh"],
    "sustainability": ["campus", "weekly", "monthly_savings"],
}


def compute_file_hash(filepath: Path) -> str:
    if not filepath.exists():
        return ""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


class ArtifactIngestionService:
    @staticmethod
    def validate_artifact_schema(artifact_type: str, file_path: Path) -> tuple[bool, str, int]:
        if not file_path.exists():
            return False, f"File {file_path.name} does not exist.", 0

        required_cols = REQUIRED_SCHEMAS.get(artifact_type, [])

        if file_path.suffix == ".csv":
            try:
                df = pd.read_csv(file_path, nrows=10)
                missing = [col for col in required_cols if col not in df.columns]
                if missing:
                    return False, f"CSV missing required columns: {missing}", 0
                full_df = pd.read_csv(file_path)
                return True, "Valid CSV schema", len(full_df)
            except Exception as e:
                return False, f"Corrupted CSV file: {str(e)}", 0

        elif file_path.suffix == ".json":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list):
                    if len(data) > 0 and isinstance(data[0], dict):
                        first_item = data[0]
                        missing = [col for col in required_cols if col not in first_item]
                        if missing:
                            return False, f"JSON list missing required keys in items: {missing}", 0
                    return True, "Valid JSON list schema", len(data)

                elif isinstance(data, dict):
                    missing = [col for col in required_cols if col not in data]
                    if missing:
                        return False, f"JSON dict missing required top-level keys: {missing}", 0
                    return True, "Valid JSON object schema", len(data)

                return False, "Invalid JSON structure", 0
            except Exception as e:
                return False, f"Corrupted JSON file: {str(e)}", 0

        return False, "Unsupported file format", 0

    @classmethod
    def ingest_artifact(
        cls, run_id: str, artifact_type: str, filename: str, db: Session = None
    ) -> dict:
        init_db()
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True

        file_path = ml_bridge.get_generated_path(filename)
        file_hash = compute_file_hash(file_path)

        is_valid, msg, rec_count = cls.validate_artifact_schema(artifact_type, file_path)

        status_str = "ingested" if is_valid else "rejected"

        ingest_record = ArtifactIngestDB(
            run_id=run_id,
            artifact_type=artifact_type,
            file_path=str(file_path),
            file_hash=file_hash,
            schema_valid=is_valid,
            status=status_str,
            record_count=rec_count,
            error_message=None if is_valid else msg,
        )

        try:
            db.add(ingest_record)
            db.commit()
            logger.info(f"Artifact {artifact_type} ({filename}) status: {status_str} (run {run_id})")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record artifact ingestion: {e}")
        finally:
            if close_after:
                db.close()

        return {
            "run_id": run_id,
            "artifact_type": artifact_type,
            "filename": filename,
            "schema_valid": is_valid,
            "status": status_str,
            "record_count": rec_count,
            "message": msg,
        }

    @classmethod
    def ingest_all_phase1_artifacts(cls, run_id: str = "RUN-PHASE1-LATEST") -> dict:
        results = {}
        artifacts_map = {
            "buildings": "buildings.csv",
            "forecasts": "forecast_predictions.csv",
            "alerts": "alerts.csv",
            "recommendations": "recommendations.json",
            "sustainability": "weekly_report.json",
        }
        for art_type, filename in artifacts_map.items():
            results[art_type] = cls.ingest_artifact(run_id, art_type, filename)
        return results


artifact_ingestion_service = ArtifactIngestionService()
