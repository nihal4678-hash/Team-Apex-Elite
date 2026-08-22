from app.repositories.ml_repository import ml_repository
from app.schemas.forecast import ForecastSchema


def get_load_forecast() -> ForecastSchema:
    raw_data = ml_repository.get_forecast()
    return ForecastSchema(**raw_data)
