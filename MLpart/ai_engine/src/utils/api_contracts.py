"""Phase-2 FastAPI contract (not implemented in Phase 1).

These dataclasses document the payloads the backend should expose.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class ForecastRequest:
    building_id: str | None = None
    horizon_hours: int = 24


@dataclass
class AnomalyQuery:
    min_severity: str = "medium"
    building_id: str | None = None
    limit: int = 100


@dataclass
class RecommendationQuery:
    min_priority: int = 70


def example_routes() -> dict[str, Any]:
    return {
        "GET /ai/health": "engine version + last pipeline timestamp",
        "GET /ai/campus": "campus_metadata.json",
        "GET /ai/forecast": asdict(ForecastRequest()),
        "GET /ai/anomalies": asdict(AnomalyQuery()),
        "GET /ai/recommendations": asdict(RecommendationQuery()),
        "GET /ai/sustainability": "weekly_report.json + building_scores.csv",
        "POST /ai/simulate/tick": "advance IoT simulator one interval (Phase 2)",
    }
