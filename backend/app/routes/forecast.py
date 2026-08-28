from fastapi import APIRouter
from app.schemas.forecast import ForecastSchema, ForecastDashboardResponseSchema
from app.services.forecast_service import get_load_forecast, get_forecast_dashboard_analytics

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("", response_model=ForecastSchema)
def get_forecast() -> ForecastSchema:
    """Backward compatible basic load forecast."""
    return get_load_forecast()


@router.get("/dashboard", response_model=ForecastDashboardResponseSchema)
def get_forecast_dashboard() -> ForecastDashboardResponseSchema:
    """Structured Forecast Analytics Dashboard payload built via loop-oriented data transformations."""
    return get_forecast_dashboard_analytics()
