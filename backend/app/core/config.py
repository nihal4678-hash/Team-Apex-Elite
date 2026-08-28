import os
from pathlib import Path
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = BASE_DIR / "backend" / ".env"

# Auto-load .env file into os.environ if present
if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()


def parse_cors_origins() -> list[str]:
    raw_cors = os.getenv("CORS_ORIGINS", "")
    defaults = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    if not raw_cors:
        return defaults + ["*"]

    custom_list = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]
    merged = list(dict.fromkeys(defaults + custom_list))
    return merged


class Settings(BaseModel):
    PROJECT_NAME: str = "EcoMind AI Smart Campus Energy Optimization Engine"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_API_KEYS: str = os.getenv("GEMINI_API_KEYS", os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_ANON_KEY", "")))
    
    BASE_DIR: Path = BASE_DIR
    ML_ENGINE_DIR: Path = BASE_DIR / "MLpart" / "ai_engine"
    GENERATED_DATA_DIR: Path = ML_ENGINE_DIR / "data" / "generated"
    MODELS_DIR: Path = ML_ENGINE_DIR / "models"
    
    CORS_ORIGINS: list[str] = Field(default_factory=parse_cors_origins)


settings = Settings()
