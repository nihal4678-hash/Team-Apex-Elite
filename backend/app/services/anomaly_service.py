from app.repositories.ml_repository import ml_repository
from app.schemas.alert import AlertSchema


def get_alerts_list() -> list[AlertSchema]:
    raw_data = ml_repository.get_alerts()
    return [AlertSchema(**a) for a in raw_data]


def resolve_alert_by_id(alert_id: str) -> dict:
    return ml_repository.resolve_alert(alert_id)
