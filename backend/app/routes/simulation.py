from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/simulation", tags=["simulation"])


class SimulationRequest(BaseModel):
    building_id: str
    temperature_delta: float = -2
    duration_minutes: int = 60


@router.post("")
def run_simulation(payload: SimulationRequest) -> dict[str, float | str]:
    return {"building_id": payload.building_id, "estimated_savings": 38, "status": "ready_for_approval"}
