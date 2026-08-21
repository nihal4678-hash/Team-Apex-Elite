from fastapi import APIRouter
from app.models.building import Building
from app.services.energy_service import list_buildings

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("", response_model=list[Building])
def get_buildings() -> list[Building]:
    return list_buildings()
