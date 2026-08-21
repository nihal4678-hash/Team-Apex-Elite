from fastapi import APIRouter
from app.services.forecast_service import get_load_forecast

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("")
def get_forecast() -> dict[str, list[int]]:
    return get_load_forecast()
