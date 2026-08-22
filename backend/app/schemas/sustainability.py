from pydantic import BaseModel


class SustainabilitySchema(BaseModel):
    carbon_avoided_kg: float
    energy_saved_month_kwh: float
    money_saved_month_inr: float
    energy_intensity: str
    campus_info: dict
    green_leaderboard: list[dict]
    weekly_history: list[dict]
