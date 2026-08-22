# EcoMind AI — Production & Deployment Guide

This guide details operational setup, background execution, database persistence, and production deployment for **EcoMind AI (AI Smart Campus Energy Optimization Platform)**.

---

## 🏛️ System Overview

- **Frontend**: React 18 SPA (Vite)
- **Backend**: FastAPI 0.100+ (Uvicorn / Gunicorn)
- **Database**: SQLite / PostgreSQL (SQLAlchemy 2.0 ORM)
- **ML Engine**: 8-Stage Telemetry, Forecasting & Anomaly Detection Pipeline
- **Grid Carbon Factor**: `0.82 kg CO₂/kWh` (Indian Grid)
- **Campus Tariff**: `₹8.75/kWh` (AP Commercial Tariff)

---

## 🚀 Environment Configuration

Create a `.env` file in `backend/` or configure server environment variables:

```env
ENVIRONMENT=production
DEBUG=false
PORT=8000
DATABASE_URL=sqlite:///./ecomind.db
LOG_LEVEL=INFO
```

---

## 🧪 Running Validation & Unit Tests

Run the full automated backend test suite:

```bash
cd backend
python -m unittest tests/test_suite.py
```

Expected output:
```text
Ran 8 tests in 4.967s
OK
```

---

## 💻 Running the Integrated System

### Option A: Using Master Launcher
```bash
python start_system.py
```
In a second terminal:
```bash
cd frontend
npm run dev
```

### Option B: Production Deployment via Gunicorn / Uvicorn

```bash
# 1. Start Backend with 4 Workers
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 2. Build Frontend for Nginx / Web Server
cd frontend
npm run build
```

---

## 📊 API Monitoring & Health Endpoints

- **Health Probe**: `GET /health` -> `{ "status": "healthy", "service": "ecomind-api", "version": "1.0.0" }`
- **Readiness Probe**: `GET /ready` -> `{ "status": "ready", "ml_artifacts_present": true }`
- **Interactive OpenAPI Docs**: `http://localhost:8000/docs`
- **Next-Month Energy Cost Prediction**: `POST /api/v1/prediction/next-month-cost`
- **Agent Orchestration History**: `GET /api/v1/agent/runs`
- **Human-in-the-Loop Audit Logs**: `GET /api/v1/audit/logs`
