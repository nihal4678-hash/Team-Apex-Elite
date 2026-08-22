#!/usr/bin/env python3
"""
EcoMind AI — Integrated System Launcher & Closed-Loop Engine Orchestrator
Connects React Frontend, FastAPI Backend, and Phase 1 ML Engine
"""

import os
import sys
import time
import subprocess
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent

# Check if repo is in current folder or child folder
if (CURRENT_DIR / "backend").exists():
    ROOT_DIR = CURRENT_DIR
elif (CURRENT_DIR / "AI Smart Campus Energy Optimization Agent" / "backend").exists():
    ROOT_DIR = CURRENT_DIR / "AI Smart Campus Energy Optimization Agent"
else:
    ROOT_DIR = CURRENT_DIR

BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
ML_DIR = ROOT_DIR / "MLpart" / "ai_engine"
GENERATED_DATA_DIR = ML_DIR / "data" / "generated"


def check_ml_artifacts():
    print(f"[1/3] Checking ML Engine generated artifacts in {ML_DIR}...")
    required_files = ["buildings.csv", "recommendations.json", "forecast_predictions.csv", "alerts.csv"]
    missing = [f for f in required_files if not (GENERATED_DATA_DIR / f).exists()]
    
    if missing:
        print(f"⚠️ Missing ML artifacts: {missing}. Running Phase 1 ML pipeline...")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ML_DIR)
        res = subprocess.run([sys.executable, "run_phase1.py"], cwd=str(ML_DIR), env=env)
        if res.returncode != 0:
            print("❌ Error generating ML artifacts. Please check MLpart pipeline.")
            sys.exit(1)
        print("✅ ML pipeline completed successfully.")
    else:
        print("✅ All ML Engine artifacts and model files present.")


def start_backend():
    print(f"[2/3] Starting FastAPI Backend Service from {BACKEND_DIR} (http://localhost:8000)...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)
    
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    proc = subprocess.Popen(cmd, cwd=str(BACKEND_DIR), env=env)
    
    # Wait for server to respond
    print("Waiting for backend API initialization...")
    time.sleep(3)
    return proc


def print_frontend_instructions():
    rel_frontend = os.path.relpath(FRONTEND_DIR, os.getcwd())
    print("\n[3/3] Integrated System Ready!")
    print("=" * 60)
    print("🚀 BACKEND API: http://localhost:8000")
    print("📚 API DOCS:   http://localhost:8000/docs")
    print("🎨 FRONTEND UI: http://localhost:5173")
    print("=" * 60)
    print("To launch the frontend interface, run in a separate terminal:")
    print(f"  cd \"{rel_frontend}\"")
    print("  npm run dev")
    print("=" * 60)


if __name__ == "__main__":
    check_ml_artifacts()
    backend_proc = start_backend()
    print_frontend_instructions()
    
    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping backend server...")
        backend_proc.terminate()
        sys.exit(0)
