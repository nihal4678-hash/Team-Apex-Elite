from pydantic import BaseModel, Field
from typing import Optional, Any


class AlertSchema(BaseModel):
    id: str
    building_id: str
    building: str
    type: str
    severity: str
    message: str
    recommended_action: str
    estimated_waste_kwh: float
    estimated_cost_inr: float
    status: str


class ContextAwareAlertSchema(BaseModel):
    alert_id: str
    scenario_id: Optional[str] = None
    building_id: str
    building_name: str
    building_category: str  # academic, computer_lab, library, hostel, admin
    timestamp: str
    day_type: str  # working_day, sunday, holiday
    time_window: str  # academic_hours, after_hours, night, hostel_evening_peak, hostel_night
    observed_kwh: float
    expected_kwh: float
    allowed_essential_kwh: float
    deviation_kwh: float
    deviation_ratio: float
    severity: str  # normal, warning, anomaly, critical
    anomaly_type: str
    probable_cause: str
    recommended_action: str
    status: str  # new, acknowledged, investigating, resolved
    user_feedback: Optional[str] = None  # genuine_anomaly, expected_usage, false_positive
    confidence_score: float
    data_source: str  # simulated or actual
    created_at: str


class AlertsKpisSchema(BaseModel):
    critical_alerts_count: int
    active_anomalies_count: int
    estimated_wasted_kwh: float
    estimated_avoidable_cost_inr: float
    high_risk_buildings_count: int


class AlertFeedbackRequestSchema(BaseModel):
    user_feedback: str  # 'genuine_anomaly', 'expected_usage', 'false_positive'
    notes: Optional[str] = ""


class HeatmapCellSchema(BaseModel):
    building_id: str
    building_name: str
    hour: int
    anomaly_count: int
    severity_max: str


class HourlyTrendPointSchema(BaseModel):
    timestamp: str
    observed_kwh: float
    expected_kwh: float
    allowed_essential_kwh: float


class AlertsDashboardResponseSchema(BaseModel):
    executive_title: str
    last_evaluated: str
    kpis: AlertsKpisSchema
    alerts: list[ContextAwareAlertSchema]
    hourly_trends: list[HourlyTrendPointSchema]
    heatmap_matrix: list[HeatmapCellSchema]
    configurable_holidays: list[str]
