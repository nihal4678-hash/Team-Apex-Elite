from pydantic import BaseModel
from typing import Optional


class HealthSchema(BaseModel):
    status: str
    service: str
    version: str
    environment: str


class ReadinessSchema(BaseModel):
    status: str
    ml_artifacts_present: bool
    data_directory_exists: bool
    supabase_configured: bool
    gemini_configured: bool
    gemini_reachable: bool
    gemini_model: str
    environment: str
