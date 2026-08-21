from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="EcoMind AI API",
    description="Smart Campus Energy Optimization Backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "EcoMind AI Backend is running"
    }


@app.get("/api/buildings")
def get_buildings():
    return [
        {
            "id": "lib",
            "name": "Central Library",
            "load": 78,
            "kw": 142,
            "occ": 61,
            "status": "normal"
        },
        {
            "id": "blockA",
            "name": "A Block",
            "load": 91,
            "kw": 205,
            "occ": 88,
            "status": "high"
        },
        {
            "id": "blockB",
            "name": "H Block",
            "load": 54,
            "kw": 118,
            "occ": 72,
            "status": "normal"
        }
    ]


@app.get("/api/alerts")
def get_alerts():
    return [
        {
            "id": 1,
            "building": "N Block",
            "type": "Spike",
            "severity": "critical",
            "message": "Load 42% above baseline",
            "status": "pending"
        }
    ]


@app.post("/api/alerts/{alert_id}/approve")
def approve_alert(alert_id: int):
    return {
        "success": True,
        "alert_id": alert_id,
        "status": "approved"
    }