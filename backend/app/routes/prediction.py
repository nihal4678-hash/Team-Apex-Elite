from fastapi import APIRouter
from app.schemas.cost_prediction import (
    CostPredictionRequestSchema,
    CostPredictionResponseSchema,
)
from app.services.cost_prediction_service import cost_prediction_service

router = APIRouter(prefix="/prediction", tags=["cost_prediction"])


@router.post("/next-month-cost", response_model=CostPredictionResponseSchema)
def predict_next_month_cost(payload: CostPredictionRequestSchema) -> CostPredictionResponseSchema:
    return cost_prediction_service.predict_next_month_cost(payload)


@router.get("/next-month-cost", response_model=CostPredictionResponseSchema)
def get_next_month_cost_prediction() -> CostPredictionResponseSchema:
    # Service call with default Vignan University campus parameters
    default_req = CostPredictionRequestSchema()
    return cost_prediction_service.predict_next_month_cost(default_req)
