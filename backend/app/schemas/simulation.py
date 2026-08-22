from pydantic import BaseModel, Field


class SimulationRequestSchema(BaseModel):
    building_id: str
    temperature_delta: float = Field(default=-2.0, description="Temperature adjustment in deg C")
    duration_minutes: int = Field(default=60, gt=0)


class SimulationResponseSchema(BaseModel):
    building_id: str
    temp_delta: float
    duration_minutes: int
    saved_kwh: float
    estimated_savings_inr: float
    co2_reduced_kg: float
    status: str
