from fastapi import APIRouter
from app.services.energy_service import campus_snapshot

router = APIRouter(prefix="/sustainability", tags=["sustainability"])


@router.get("")
def get_sustainability() -> dict[str, float | str]:
    snapshot = campus_snapshot()
    return {"carbon_avoided_kg": snapshot["carbon_avoided_kg"], "energy_intensity": "12.4% below baseline"}
