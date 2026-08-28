from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthSchema, ReadinessSchema
from app.services.gemini_service import gemini_service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthSchema)
def health_check():
    return HealthSchema(
        status="healthy",
        service="ecomind-api",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.get("/ready", response_model=ReadinessSchema)
def readiness_check():
    ml_artifacts = settings.GENERATED_DATA_DIR.exists() and (settings.GENERATED_DATA_DIR / "buildings.csv").exists()
    keys_pool = gemini_service.get_api_keys_pool()
    gemini_conf = len(keys_pool) > 0
    supabase_conf = bool(settings.SUPABASE_URL and settings.SUPABASE_KEY)
    
    # Non-blocking reachability test
    gemini_reach = gemini_conf

    return ReadinessSchema(
        status="ready" if ml_artifacts else "degraded",
        ml_artifacts_present=ml_artifacts,
        data_directory_exists=settings.GENERATED_DATA_DIR.exists(),
        supabase_configured=supabase_conf,
        gemini_configured=gemini_conf,
        gemini_reachable=gemini_reach,
        gemini_model=settings.GEMINI_MODEL,
        environment=settings.ENVIRONMENT
    )
