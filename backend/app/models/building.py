from pydantic import BaseModel, Field


class Building(BaseModel):
    id: str
    name: str
    building_type: str
    area_sq_ft: int = Field(gt=0)
    current_load_kw: float = Field(ge=0)
    load_percent: int = Field(ge=0, le=100)
