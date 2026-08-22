from datetime import datetime
from pydantic import BaseModel


class Alert(BaseModel):
    id: str
    title: str
    building: str
    severity: str
    status: str
    created_at: datetime
