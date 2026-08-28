from fastapi import APIRouter
from app.schemas.alert import AlertSchema, AlertsDashboardResponseSchema, AlertFeedbackRequestSchema
from app.services.anomaly_service import get_alerts_list, resolve_alert_by_id, ContextAwareAnomalyEngine

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertSchema])
def get_alerts() -> list[AlertSchema]:
    """Backward compatible alerts fetcher."""
    return get_alerts_list()


@router.get("/dashboard", response_model=AlertsDashboardResponseSchema)
def get_alerts_dashboard() -> AlertsDashboardResponseSchema:
    """Context-aware anomaly and energy leak detection dashboard payload."""
    return ContextAwareAnomalyEngine.generate_context_aware_alerts()


@router.post("/{alert_id}/feedback")
def submit_alert_feedback(alert_id: str, payload: AlertFeedbackRequestSchema):
    """Submit learning loop feedback (genuine_anomaly, expected_usage, false_positive)."""
    return ContextAwareAnomalyEngine.process_user_feedback(alert_id, payload)


@router.post("/{alert_id}/approve")
def approve_alert(alert_id: str):
    return resolve_alert_by_id(alert_id)


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: str):
    return resolve_alert_by_id(alert_id)
