from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.logging import setup_logging
from app.routes.agent import router as agent_router
from app.routes.alerts import router as alerts_router
from app.routes.analytics import router as analytics_router
from app.routes.audit import router as audit_router
from app.routes.auth import router as auth_router
from app.routes.buildings import router as buildings_router
from app.routes.forecast import router as forecast_router
from app.routes.gemini import router as gemini_router
from app.routes.health import router as health_router
from app.routes.prediction import router as prediction_router
from app.routes.recommendations import router as recommendations_router
from app.routes.simulation import router as simulation_router
from app.routes.sustainability import router as sustainability_router
from app.schemas.snapshot import SnapshotSchema
from app.services.db_seed import seed_database
from app.services.energy_service import campus_snapshot

# Initialize structured logging
setup_logging()


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # Startup: Seed database from ML artifacts if needed
    seed_database()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Professional Service Layer & AI Optimization Engine for Vignan University",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Exception handlers
setup_exception_handlers(app)

# CORS middleware supporting Render & local development
origins = settings.CORS_ORIGINS
has_wildcard = "*" in origins
explicit_origins = [o for o in origins if o != "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=explicit_origins if explicit_origins else ["*"],
    allow_origin_regex=r"https://.*\.onrender\.com|https://.*\.vercel\.app|http://localhost:.*|http://127\.0\.0\.1:.*",
    allow_credentials=not has_wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health & readiness checks at root level
app.include_router(health_router)

# Versioned API routes (/api/v1)
app.include_router(buildings_router, prefix=settings.API_V1_STR)
app.include_router(alerts_router, prefix=settings.API_V1_STR)
app.include_router(forecast_router, prefix=settings.API_V1_STR)
app.include_router(sustainability_router, prefix=settings.API_V1_STR)
app.include_router(simulation_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(recommendations_router, prefix=settings.API_V1_STR)
app.include_router(agent_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(prediction_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(gemini_router, prefix=settings.API_V1_STR)

# Backward-compatible API routes (/api for legacy frontend binding)
app.include_router(buildings_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(forecast_router, prefix="/api")
app.include_router(sustainability_router, prefix="/api")
app.include_router(simulation_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(agent_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(prediction_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(gemini_router, prefix="/api")


@app.get("/", tags=["root"])
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }


@app.get("/api/snapshot", response_model=SnapshotSchema, tags=["snapshot"])
@app.get("/api/v1/snapshot", response_model=SnapshotSchema, tags=["snapshot"])
def get_snapshot() -> SnapshotSchema:
    return campus_snapshot()