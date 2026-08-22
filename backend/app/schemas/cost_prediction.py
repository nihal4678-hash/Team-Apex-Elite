from typing import Optional
from pydantic import BaseModel, Field


class CostPredictionRequestSchema(BaseModel):
    previous_month_cost_inr: float = Field(default=55536.51, gt=0, description="Last month's energy bill in ₹ INR")
    previous_month_kwh: float = Field(default=6347.03, gt=0, description="Last month's total energy consumption in kWh")
    target_month: str = Field(default="September 2026", description="Target prediction month")
    expected_temperature_c: float = Field(default=33.5, description="Expected average outdoor temperature in °C")
    expected_humidity_pct: float = Field(default=68.0, description="Expected humidity percentage")
    occupancy_ratio: float = Field(default=0.85, ge=0.0, le=1.0, description="Campus student/staff occupancy ratio")
    is_exam_season: bool = Field(default=True, description="Whether target month includes major university examinations")
    tariff_inr_per_kwh: float = Field(default=8.75, gt=0, description="Electricity tariff in ₹/kWh")


class DriverImpactSchema(BaseModel):
    driver: str
    impact_percent: float
    description: str


class ConfidenceRangeSchema(BaseModel):
    min_cost_inr: float
    max_cost_inr: float


class ScenariosSchema(BaseModel):
    optimistic_inr: float
    baseline_inr: float
    pessimistic_inr: float


class RecommendedSavingsActionSchema(BaseModel):
    title: str
    estimated_savings_inr: float
    action_type: str


class CostPredictionResponseSchema(BaseModel):
    target_month: str
    predicted_cost_inr: float
    predicted_energy_kwh: float
    confidence_range_inr: ConfidenceRangeSchema
    mom_change_percent: float
    top_cost_drivers: list[DriverImpactSchema]
    scenarios: ScenariosSchema
    recommended_savings_actions: list[RecommendedSavingsActionSchema]
