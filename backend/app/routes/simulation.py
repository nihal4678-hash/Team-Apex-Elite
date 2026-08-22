from fastapi import APIRouter
from app.repositories.ml_repository import ml_repository
from app.schemas.simulation import (
    SimulationRequestSchema,
    SimulationResponseSchema,
)

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("", response_model=SimulationResponseSchema)
def run_simulation(payload: SimulationRequestSchema) -> SimulationResponseSchema:
    raw_result = ml_repository.run_simulation(
        payload.building_id,
        payload.temperature_delta,
        payload.duration_minutes
    )
    return SimulationResponseSchema(**raw_result)
