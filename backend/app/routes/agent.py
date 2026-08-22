from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.agent_orchestrator import agent_orchestration_service

router = APIRouter(prefix="/agent", tags=["agent_orchestration"])


class RunPipelineRequest(BaseModel):
    run_id: Optional[str] = None
    stage: Optional[int] = None


@router.get("/runs")
def get_agent_runs():
    return agent_orchestration_service.get_run_history()


@router.post("/run")
def trigger_agent_run(payload: RunPipelineRequest):
    if payload.stage:
        run_id = payload.run_id or "STAGE-MANUAL-RUN"
        return agent_orchestration_service.execute_stage(run_id, payload.stage)
    return agent_orchestration_service.execute_full_pipeline(payload.run_id)
