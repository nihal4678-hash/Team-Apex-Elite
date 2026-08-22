from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthSchema, ReadinessSchema

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
    return ReadinessSchema(
        status="ready" if ml_artifacts else "degraded",
        ml_artifacts_present=ml_artifacts,
        data_directory_exists=settings.GENERATED_DATA_DIR.exists(),
    )
