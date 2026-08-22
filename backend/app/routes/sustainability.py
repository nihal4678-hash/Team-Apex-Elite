from fastapi import APIRouter
from app.repositories.ml_repository import ml_repository
from app.schemas.sustainability import SustainabilitySchema

router = APIRouter(prefix="/sustainability", tags=["sustainability"])


@router.get("", response_model=SustainabilitySchema)
def get_sustainability() -> SustainabilitySchema:
    raw_data = ml_repository.get_sustainability_data()
    return SustainabilitySchema(**raw_data)
