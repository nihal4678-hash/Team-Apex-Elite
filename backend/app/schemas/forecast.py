from pydantic import BaseModel, Field
from typing import Optional, Any


class ForecastSchema(BaseModel):
    actual: list[float]
    forecast: list[float]


class ForecastKpisSchema(BaseModel):
    predicted_energy_24h_kwh: float
    predicted_cost_inr: float
    predicted_peak_demand_kw: float
    peak_demand_time_window: str
    model_accuracy_pct: float
    mape_pct: float
    savings_opportunity_inr: float
    carbon_impact_co2_kg: float
    high_demand_buildings_count: int
    weather_impact_score: str
    weather_impact_pct: float


class BuildingForecastSummarySchema(BaseModel):
    building_id: str
    name: str
    category: str
    predicted_kw: float
    load_percent: float
    status: str
    daily_cost_inr: float
    building_area_sqm: float
    area_share_pct: float


class FeatureImportanceSchema(BaseModel):
    feature_name: str
    importance_pct: float
    description: str


class ScenarioPointSchema(BaseModel):
    name: str
    title: str
    cost_inr: float
    energy_kwh: float
    variance_pct: float
    description: str


class ForecastRecommendationSchema(BaseModel):
    id: str
    category: str
    title: str
    description: str
    estimated_savings_inr: float
    priority: str


class HourlyForecastRowSchema(BaseModel):
    hour: int
    timestamp: str
    record_type: str  # 'actual' or 'forecast'
    actual_kwh: Optional[float] = None
    predicted_kwh: float
    variance_pct: Optional[float] = None
    cost_inr: float
    building_status: str


class ForecastDashboardResponseSchema(BaseModel):
    executive_title: str
    model_name: str
    horizon: str
    last_updated: str
    kpis: ForecastKpisSchema
    actual_series: list[float]
    forecast_series: list[float]
    time_labels: list[str]
    building_summaries: list[BuildingForecastSummarySchema]
    feature_importances: list[FeatureImportanceSchema]
    scenario_comparisons: list[ScenarioPointSchema]
    recommendations: list[ForecastRecommendationSchema]
    hourly_rows: list[HourlyForecastRowSchema]
    cost_explanation: Optional[dict[str, Any]] = None
