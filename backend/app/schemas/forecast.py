from pydantic import BaseModel


class ForecastSchema(BaseModel):
    actual: list[float]
    forecast: list[float]
