from fastapi import APIRouter
from app.schemas.alert import AlertSchema
from app.services.anomaly_service import get_alerts_list, resolve_alert_by_id

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertSchema])
def get_alerts() -> list[AlertSchema]:
    return get_alerts_list()


@router.post("/{alert_id}/approve")
def approve_alert(alert_id: str):
    return resolve_alert_by_id(alert_id)


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: str):
    return resolve_alert_by_id(alert_id)
