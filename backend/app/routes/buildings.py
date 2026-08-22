from fastapi import APIRouter
from app.schemas.building import BuildingSchema
from app.services.energy_service import list_buildings

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("", response_model=list[BuildingSchema])
def get_buildings() -> list[BuildingSchema]:
    return list_buildings()
