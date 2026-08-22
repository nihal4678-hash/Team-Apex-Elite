import json
from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.db_models import AuditLogDB

router = APIRouter(prefix="/audit", tags=["audit_logs"])


@router.get("/logs")
def get_audit_logs(limit: int = 50):
    db: Session = SessionLocal()
    try:
        logs_db = db.query(AuditLogDB).order_by(AuditLogDB.id.desc()).limit(limit).all()
        return [
            {
                "id": l.id,
                "user_id": l.user_id,
                "action": l.action,
                "target_type": l.target_type,
                "target_id": l.target_id,
                "details": json.loads(l.details_json) if l.details_json else {},
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs_db
        ]
    finally:
        db.close()


@router.get("/summary")
def get_audit_summary():
    db: Session = SessionLocal()
    try:
        total_logs = db.query(AuditLogDB).count()
        applied_recs = db.query(AuditLogDB).filter(AuditLogDB.action == "apply_recommendation").count()
        resolved_alerts = db.query(AuditLogDB).filter(AuditLogDB.action == "resolve_alert").count()
        simulations = db.query(AuditLogDB).filter(AuditLogDB.action == "run_simulation").count()

        return {
            "total_audit_events": total_logs,
            "applied_recommendations_count": applied_recs,
            "resolved_alerts_count": resolved_alerts,
            "simulations_count": simulations,
        }
    finally:
        db.close()
