from pydantic import BaseModel, Field


class BuildingSchema(BaseModel):
    id: str
    name: str
    category: str = "academic"
    area_sqm: float = Field(ge=0)
    kw: float = Field(ge=0)
    load: int = Field(ge=0, le=100)
    status: str = "normal"
