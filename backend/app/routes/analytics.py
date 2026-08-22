from fastapi import APIRouter
from app.repositories.db_repository import db_repository
from app.services.agent_orchestrator import agent_orchestration_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def get_analytics_summary():
    snapshot = db_repository.get_snapshot()
    buildings = db_repository.get_buildings()
    alerts = db_repository.get_alerts()
    recs = db_repository.get_recommendations()
    forecast = db_repository.get_forecast()
    agent_runs = agent_orchestration_service.get_run_history()

    # Calculate alert severity breakdown
    sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for a in alerts:
        s = a.get("severity", "medium").lower()
        sev_counts[s] = sev_counts.get(s, 0) + 1

    # Total potential savings across all recommendations
    total_rec_kwh = sum(r.get("energy_saved_kwh", 0) for r in recs)
    total_rec_inr = sum(r.get("money_saved_inr", 0) for r in recs)

    return {
        "snapshot": snapshot,
        "building_count": len(buildings),
        "buildings_summary": buildings,
        "forecast_data": forecast,
        "alert_severity_breakdown": sev_counts,
        "total_recommendation_savings": {
            "kwh": round(total_rec_kwh, 2),
            "inr": round(total_rec_inr, 2),
        },
        "top_recommendations": recs[:5],
        "recent_agent_runs": agent_runs[:8],
    }
