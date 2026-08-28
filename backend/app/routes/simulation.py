from fastapi import APIRouter, HTTPException
from app.repositories.ml_repository import ml_repository
from app.schemas.simulation import (
    SimulationRequestSchema,
    SimulationResponseSchema,
    LoopSimulationRequestSchema,
    LoopSimulationResponseSchema,
    ScenarioListItemSchema,
    ScenarioDetailSchema,
    SimulationProgressSchema,
)
from app.services.loop_simulation_service import loop_simulation_service

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("", response_model=SimulationResponseSchema)
def run_simulation(payload: SimulationRequestSchema) -> SimulationResponseSchema:
    raw_result = ml_repository.run_simulation(
        payload.building_id,
        payload.temperature_delta,
        payload.duration_minutes
    )
    return SimulationResponseSchema(**raw_result)


@router.post("/loop/run", response_model=LoopSimulationResponseSchema)
def run_loop_simulation(payload: LoopSimulationRequestSchema) -> LoopSimulationResponseSchema:
    """Execute loop-based simulation workflow across requested single or multiple months."""
    try:
        return loop_simulation_service.run_loop_simulation(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/loop/start")
def start_controlled_simulation(payload: LoopSimulationRequestSchema) -> dict:
    """Start controlled simulation run in background and return scenario ID."""
    try:
        return loop_simulation_service.start_controlled_simulation_job(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/loop/stop")
def stop_controlled_simulation(scenario_id: str) -> dict:
    """Safely request stop/cancellation for running simulation scenario."""
    try:
        return loop_simulation_service.stop_controlled_simulation(scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loop/progress/{scenario_id}", response_model=SimulationProgressSchema)
def get_simulation_progress(scenario_id: str) -> SimulationProgressSchema:
    """Poll real-time simulation progress counters, current timestamp, and status."""
    try:
        return loop_simulation_service.get_simulation_progress(scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loop/scenarios", response_model=list[ScenarioListItemSchema])
def get_loop_scenarios() -> list[ScenarioListItemSchema]:
    """Retrieve list of executed simulation scenarios stored in the database."""
    return loop_simulation_service.get_scenarios()


@router.get("/loop/scenario/{scenario_id}", response_model=ScenarioDetailSchema)
def get_loop_scenario_detail(scenario_id: str) -> ScenarioDetailSchema:
    """Retrieve detailed preprocessed reading metrics & breakdown for a scenario ID."""
    try:
        return loop_simulation_service.get_scenario_detail(scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/loop/cleanup")
def cleanup_simulated_records(scenario_id: str = None) -> dict:
    """Safely delete simulation records from DB & Supabase (strictly scoped to data_source='simulated')."""
    try:
        return loop_simulation_service.cleanup_simulated_records(scenario_id=scenario_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
