from pydantic import BaseModel, Field
from typing import Optional, Any


class SimulationRequestSchema(BaseModel):
    building_id: str
    temperature_delta: float = Field(default=-2.0, description="Temperature adjustment in deg C")
    duration_minutes: int = Field(default=60, gt=0)


class SimulationResponseSchema(BaseModel):
    building_id: str
    temp_delta: float
    duration_minutes: int
    saved_kwh: float
    estimated_savings_inr: float
    co2_reduced_kg: float
    status: str


class LoopSimulationRequestSchema(BaseModel):
    from_date: str = Field(default="2025-07-01", description="Start date in YYYY-MM-DD format.")
    from_time: str = Field(default="08:00", description="Start time in HH:MM format.")
    to_date: str = Field(default="2025-07-31", description="End date in YYYY-MM-DD format.")
    to_time: str = Field(default="18:00", description="End time in HH:MM format.")
    building_id: str = Field(default="ALL", description="Selected building ID or category (e.g. ALL, academic, hostel, LAB-CSE).")
    temperature_delta: float = Field(default=-2.0, description="HVAC setpoint adjustment in degrees Celsius.")
    occupancy_scale: float = Field(default=1.0, ge=0.1, le=2.0, description="Occupancy scale factor.")
    include_solar: bool = Field(default=True, description="Incorporate Vignan 1 MW solar generation offset.")
    after_hours_monitoring: bool = Field(default=True, description="Include night/after-hours simulation to detect leaks.")
    clean_previous: bool = Field(default=False, description="Safely delete previous simulation records before starting run.")
    months: list[int] = Field(default=[], description="Backward-compatible list of months.")
    building_ids: list[str] = Field(default=[], description="Backward-compatible list of building IDs.")


class SimulationProgressSchema(BaseModel):
    scenario_id: str
    status: str  # queued, running, stopping, stopped, completed, failed
    cancel_requested: bool
    simulation_start_datetime: str
    simulation_end_datetime: str
    selected_scope: str
    total_hourly_records: int
    completed_hourly_records: int
    completion_percentage: float
    current_timestamp: Optional[str] = None
    current_building_id: Optional[str] = None
    generated_records_count: int
    alerts_detected_count: int
    estimated_time_remaining_sec: int = 0
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None
    completed_at: Optional[str] = None
    failure_message: Optional[str] = None


class MonthlyLoopSummarySchema(BaseModel):
    month: int
    month_name: str
    baseline_energy_kwh: float
    predicted_energy_kwh: float
    optimized_energy_kwh: float
    saved_energy_kwh: float
    saved_cost_inr: float
    co2_reduced_kg: float
    solar_offset_kwh: float


class SimulationChartSeriesPointSchema(BaseModel):
    timestamp: str
    baseline_kwh: float
    predicted_kwh: float
    optimized_kwh: float
    cost_inr: float


class AnomalySummarySchema(BaseModel):
    total_anomalies_count: int = 2
    critical_count: int = 1
    operational_advice: str = "HVAC setback applied during non-operational evening hours."


class RecommendedActionSchema(BaseModel):
    title: str
    estimated_savings_inr: float
    action_type: str


class LoopSimulationResponseSchema(BaseModel):
    run_id: str
    scenario_id: str
    data_source: str = "simulated_vignan_loop"
    from_date: str
    to_date: str
    building_id: str
    building_name: str
    months_simulated: list[int]
    total_buildings: int
    total_intervals: int
    total_records: int
    temperature_delta: float
    occupancy_scale: float
    predicted_energy_kwh: float
    predicted_cost_inr: float
    estimated_saved_kwh: float
    estimated_saved_inr: float
    carbon_avoided_kg: float
    peak_demand_kw: float
    supabase_status: str
    persistence_status: str
    monthly_breakdown: list[MonthlyLoopSummarySchema]
    chart_series: list[SimulationChartSeriesPointSchema] = []
    anomaly_summary: AnomalySummarySchema = AnomalySummarySchema()
    recommendations: list[RecommendedActionSchema] = []


class ScenarioListItemSchema(BaseModel):
    scenario_id: str
    data_source: str
    months_count: int
    temperature_delta: float
    total_saved_kwh: float
    total_saved_inr: float
    total_co2_reduced_kg: float
    status: str = "completed"
    created_at: str


class ScenarioDetailSchema(BaseModel):
    scenario_id: str
    data_source: str
    months_run: list[int]
    building_ids: list[str]
    temperature_delta: float
    occupancy_scale: float
    include_solar: bool
    total_baseline_kwh: float
    total_predicted_kwh: float
    total_optimized_kwh: float
    total_saved_kwh: float
    total_saved_inr: float
    total_co2_reduced_kg: float
    monthly_breakdown: list[MonthlyLoopSummarySchema]
    preprocessed_records_stored: int
    created_at: str
