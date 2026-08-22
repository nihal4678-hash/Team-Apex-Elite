from pydantic import BaseModel


class SnapshotSchema(BaseModel):
    energy_used_today_kwh: float
    energy_saved_month_kwh: float
    energy_cost_today_inr: float
    money_saved_month_inr: float
    carbon_avoided_kg: float
    peak_demand_kw: float
    weekly_change_percent: float
    active_actions_count: int
    resolved_alerts_count: int
