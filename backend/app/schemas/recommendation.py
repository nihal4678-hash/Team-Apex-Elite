from typing import Optional
from pydantic import BaseModel


class RecommendationSchema(BaseModel):
    recommendation_id: str
    category: str
    title: str
    description: str
    priority_score: int
    buildings: list[str]
    energy_saved_kwh: float
    money_saved_inr: float
    co2_reduced_kg: float
    applied: bool = False
    applied_at: Optional[str] = None


class ApplyActionRequestSchema(BaseModel):
    action_id: str
    params: dict = {}


class ApplyActionResponseSchema(BaseModel):
    success: bool
    action_id: str
    status: str
    saved_kwh: float
    saved_inr: float
    saved_co2_kg: float
    applied_at: str
