from pydantic import BaseModel


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
