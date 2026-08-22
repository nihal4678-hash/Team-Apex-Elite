from fastapi import APIRouter
from app.repositories.ml_repository import ml_repository
from app.schemas.recommendation import (
    ApplyActionRequestSchema,
    ApplyActionResponseSchema,
    RecommendationSchema,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=list[RecommendationSchema])
def get_recommendations() -> list[RecommendationSchema]:
    raw_data = ml_repository.get_recommendations()
    return [RecommendationSchema(**r) for r in raw_data]


@router.post("/apply", response_model=ApplyActionResponseSchema)
def apply_recommendation(payload: ApplyActionRequestSchema) -> ApplyActionResponseSchema:
    raw_result = ml_repository.apply_action(payload.action_id, payload.params)
    return ApplyActionResponseSchema(**raw_result)
