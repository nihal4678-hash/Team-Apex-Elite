from pydantic import BaseModel


class HealthSchema(BaseModel):
    status: str
    service: str
    version: str
    environment: str


class ReadinessSchema(BaseModel):
    status: str
    ml_artifacts_present: bool
    data_directory_exists: bool
