from datetime import datetime, timezone
from fastapi import APIRouter
from app.models.alert import Alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[Alert])
def get_alerts() -> list[Alert]:
    return [
        Alert(id="hvac-load", title="Unusual HVAC load detected", building="Innovation Hall", severity="review", status="open", created_at=datetime.now(timezone.utc)),
        Alert(id="demand-response", title="Demand response target met", building="Campus-wide", severity="info", status="resolved", created_at=datetime.now(timezone.utc)),
    ]
