import json
import uuid
import time
import calendar
import logging
import threading
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from app.database.database import SessionLocal, init_db
from app.models.db_models import SimulatedReadingDB, SimulationScenarioRunDB, BuildingDB, AlertDB
from app.schemas.simulation import (
    LoopSimulationRequestSchema, LoopSimulationResponseSchema,
    MonthlyLoopSummarySchema, ScenarioListItemSchema, ScenarioDetailSchema,
    SimulationChartSeriesPointSchema, AnomalySummarySchema, RecommendedActionSchema,
    SimulationProgressSchema
)
from app.services.supabase_service import supabase_service
from app.services.anomaly_service import ContextAwareAnomalyEngine

try:
    from src.utils.config import CAMPUS, VFSTR_AUDIT, WEATHER, WORKING_HOURS
    from src.preprocessing.dataset_adapter import load_iiitd_power_data
except ImportError:
    CAMPUS = {
        "name": "Vignan University",
        "tariff_inr_per_kwh": 8.75,
        "grid_carbon_kg_per_kwh": 0.82,
    }
    VFSTR_AUDIT = {
        "annual_electricity_kwh": 2_500_000.0,
        "solar_generation_kwh": 975_000.0,
    }
    WEATHER = {
        "mean_temp_c": 31.5,
        "daily_amplitude_c": 6.5,
    }
    WORKING_HOURS = (8, 18)

logger = logging.getLogger("ecomind.loop_simulation")


class LoopSimulationService:
    """Live controlled loop simulation engine with real-time alert processing & cancellation capability."""

    TOTAL_BUILTUP_AREA_SQM = 111916.33

    DEFAULT_BUILDINGS = [
        {"id": "BLK-A", "name": "Academic Block A - Engineering", "category": "academic", "area_sqm": 14030.25, "base_kw": 218.0},
        {"id": "BLK-B", "name": "Academic Block B - Sciences", "category": "academic", "area_sqm": 10490.70, "base_kw": 182.0},
        {"id": "BLK-C", "name": "Academic Block C - Management", "category": "admin", "area_sqm": 9936.96, "base_kw": 145.0},
        {"id": "BLK-D", "name": "Main Complex Block D", "category": "academic", "area_sqm": 39460.53, "base_kw": 450.0},
        {"id": "LAB-CSE", "name": "Computer Science Laboratories", "category": "computer_lab", "area_sqm": 6943.33, "base_kw": 195.0},
        {"id": "LIB", "name": "Central Library (NTR)", "category": "library", "area_sqm": 4722.08, "base_kw": 135.0},
        {"id": "HST-G", "name": "Priyadarsini Girls Hostel Complex", "category": "hostel", "area_sqm": 10747.75, "base_kw": 210.0},
        {"id": "HST-B", "name": "Vignan Vihar Boys Hostel Complex", "category": "hostel", "area_sqm": 12889.91, "base_kw": 240.0},
    ]

    VIGNAN_MONTHLY_AUDIT = {
        1: {"solar_kwh": 95000.0, "grid_kwh": 115000.0, "total_kwh": 210000.0},
        2: {"solar_kwh": 92000.0, "grid_kwh": 108000.0, "total_kwh": 200000.0},
        3: {"solar_kwh": 90000.0, "grid_kwh": 110000.0, "total_kwh": 200000.0},
        4: {"solar_kwh": 88000.0, "grid_kwh": 112000.0, "total_kwh": 200000.0},
        5: {"solar_kwh": 85000.0, "grid_kwh": 115000.0, "total_kwh": 200000.0},
        6: {"solar_kwh": 70000.0, "grid_kwh": 130000.0, "total_kwh": 200000.0},
        7: {"solar_kwh": 65000.0, "grid_kwh": 135000.0, "total_kwh": 200000.0},
        8: {"solar_kwh": 70000.0, "grid_kwh": 130000.0, "total_kwh": 200000.0},
        9: {"solar_kwh": 75000.0, "grid_kwh": 125000.0, "total_kwh": 200000.0},
        10: {"solar_kwh": 80000.0, "grid_kwh": 120000.0, "total_kwh": 200000.0},
        11: {"solar_kwh": 82000.0, "grid_kwh": 118000.0, "total_kwh": 200000.0},
        12: {"solar_kwh": 83000.0, "grid_kwh": 117000.0, "total_kwh": 200000.0},
    }

    MONTH_NAMES = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    @staticmethod
    def _get_target_buildings(building_id: str, building_ids_fallback: list[str], db: Session) -> list[dict]:
        all_buildings = []
        db_buildings = db.query(BuildingDB).all()
        if db_buildings:
            all_buildings = [
                {
                    "id": b.id,
                    "name": b.name,
                    "category": b.category,
                    "area_sqm": b.area_sqm,
                    "base_kw": b.current_kw,
                }
                for b in db_buildings
            ]
        else:
            all_buildings = LoopSimulationService.DEFAULT_BUILDINGS

        if building_id:
            b_upper = building_id.upper()
            if b_upper == "ALL":
                return all_buildings
            elif b_upper == "ACADEMIC":
                return [b for b in all_buildings if b["category"] == "academic"]
            elif b_upper == "HOSTEL":
                return [b for b in all_buildings if b["category"] == "hostel"]

            filtered = [b for b in all_buildings if b["id"] == building_id or b["category"] == building_id]
            if filtered:
                return filtered

        if building_ids_fallback:
            filtered = [b for b in all_buildings if b["id"] in building_ids_fallback]
            if filtered:
                return filtered

        return all_buildings

    @staticmethod
    def start_controlled_simulation_job(req: LoopSimulationRequestSchema) -> dict:
        """Initialize controlled simulation run in database and start asynchronous background worker."""
        init_db()
        db = SessionLocal()

        try:
            if req.clean_previous:
                LoopSimulationService.cleanup_simulated_records(db=db)

            # Combine date and time
            start_str = f"{req.from_date} {req.from_time or '00:00'}:00"
            end_str = f"{req.to_date} {req.to_time or '23:00'}:00"

            try:
                start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
                end_dt = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                start_dt = datetime.strptime(f"{req.from_date} 00:00:00", "%Y-%m-%d %H:%M:%S")
                end_dt = datetime.strptime(f"{req.to_date} 23:00:00", "%Y-%m-%d %H:%M:%S")

            if end_dt <= start_dt:
                raise ValueError("Simulation end date-time must be strictly after start date-time.")

            target_buildings = LoopSimulationService._get_target_buildings(req.building_id, req.building_ids, db)
            date_range = pd.date_range(start_dt, end_dt, freq="1h")
            total_hours = len(date_range)
            total_planned_records = total_hours * len(target_buildings)

            scenario_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"

            logger.info("PLANNING STAGE: %d selected buildings (%s), planned records: %d", len(target_buildings), [b['id'] for b in target_buildings], total_planned_records)

            run_record = SimulationScenarioRunDB(
                scenario_id=scenario_id,
                data_source="simulated_vignan_loop",
                status="running",
                cancel_requested=False,
                simulation_start_datetime=start_str,
                simulation_end_datetime=end_str,
                after_hours_monitoring=req.after_hours_monitoring,
                total_hourly_records=total_planned_records,
                completed_hourly_records=0,
                generated_records_count=0,
                alerts_detected_count=0,
                started_at=datetime.now(timezone.utc).isoformat(),
                months_run=json.dumps(list(set([dt.month for dt in date_range]))),
                building_ids=json.dumps([b["id"] for b in target_buildings]),
                building_snapshot_json=json.dumps(target_buildings),
                temperature_delta=req.temperature_delta,
                occupancy_scale=req.occupancy_scale,
                include_solar=req.include_solar,
            )
            db.add(run_record)
            db.commit()

            # Launch background worker thread
            thread = threading.Thread(
                target=LoopSimulationService._execute_controlled_loop_worker,
                args=(scenario_id, start_str, end_str, req, target_buildings),
                daemon=True
            )
            thread.start()

            return {
                "success": True,
                "scenario_id": scenario_id,
                "status": "running",
                "total_planned_records": total_planned_records,
                "message": f"Controlled simulation run launched for {total_planned_records} planned hourly records."
            }

        except Exception as e:
            db.rollback()
            logger.error("Failed to start controlled simulation job: %s", e)
            raise e
        finally:
            db.close()

    @staticmethod
    def _execute_controlled_loop_worker(scenario_id: str, start_str: str, end_str: str, req: LoopSimulationRequestSchema, target_buildings: list[dict]):
        """Background worker thread executing live hourly simulation loop with alert processing and cancel checks."""
        init_db()
        db = SessionLocal()

        try:
            if not target_buildings:
                target_buildings = LoopSimulationService.DEFAULT_BUILDINGS

            date_range = pd.date_range(start_str, end_str, freq="1h")
            total_planned_records = len(date_range) * len(target_buildings)
            logger.info("WORKER STAGE: %d selected buildings (%s), planned records: %d", len(target_buildings), [b['id'] for b in target_buildings], total_planned_records)

            rng = np.random.default_rng(seed=42)

            tariff = CAMPUS.get("tariff_inr_per_kwh", 8.75)
            carbon_factor = CAMPUS.get("grid_carbon_kg_per_kwh", 0.82)

            completed_count = 0
            alerts_count = 0
            accumulated_readings = []

            tot_baseline_kwh = 0.0
            tot_predicted_kwh = 0.0
            tot_optimized_kwh = 0.0
            max_peak_kw = 0.0

            for dt in date_range:
                dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                month = dt.month
                hour = dt.hour

                for b in target_buildings:
                    time.sleep(0.01)  # Simulate real-time hourly telemetry processing cadence
                    # Check cancellation signal from database using independent session
                    with SessionLocal() as check_db:
                        sc_check = check_db.query(SimulationScenarioRunDB).filter(SimulationScenarioRunDB.scenario_id == scenario_id).first()
                        if sc_check and sc_check.cancel_requested:
                            logger.info("Cancellation requested for scenario '%s'. Halting loop safely.", scenario_id)
                            sc_check.status = "stopped"
                            sc_check.stopped_at = datetime.now(timezone.utc).isoformat()
                            check_db.commit()

                            if accumulated_readings:
                                supabase_service.store_simulated_readings(scenario_id, accumulated_readings)
                            return

                    category = b.get("category", "academic")
                    base_kw = b.get("base_kw", 150.0)
                    b_id = b["id"]

                    day_type, time_window = ContextAwareAnomalyEngine._classify_day_and_window(dt.to_pydatetime(), category)
                    outdoor_temp = WEATHER["mean_temp_c"] + np.sin(2 * np.pi * (hour - 15) / 24.0) * WEATHER["daily_amplitude_c"] + rng.normal(0, 0.4)
                    occ_ratio = float(np.clip(0.65 * req.occupancy_scale + rng.normal(0, 0.03), 0.05, 1.0))

                    # Calibrated hourly energy calculation
                    expected_kwh, allowed_essential = ContextAwareAnomalyEngine._calculate_expected_kwh(
                        category=category, base_kw=base_kw, day_type=day_type, time_window=time_window,
                        hour=hour, occupancy=occ_ratio, temp_c=outdoor_temp
                    )

                    # Simulated raw kWh (inject realistic spike on night if after-hours monitoring active)
                    simulated_raw_kwh = expected_kwh * (1.65 if (req.after_hours_monitoring and hour == 22 and b_id == "BLK-D") else 1.05)
                    simulated_raw_kwh = round(float(simulated_raw_kwh), 2)

                    # Downstream prediction & setpoint optimization
                    predicted_kwh = round(simulated_raw_kwh * (1.0 + 0.015 * max(0.0, outdoor_temp - 30.0)), 2)
                    saving_pct = abs(req.temperature_delta) * 0.06
                    optimized_kwh = round(predicted_kwh * (1.0 - saving_pct), 2)

                    tot_baseline_kwh += simulated_raw_kwh
                    tot_predicted_kwh += predicted_kwh
                    tot_optimized_kwh += optimized_kwh
                    if simulated_raw_kwh > max_peak_kw:
                        max_peak_kw = simulated_raw_kwh

                    # Real-time Anomaly Detection for this hourly reading
                    deviation_kwh = max(0.0, round(simulated_raw_kwh - expected_kwh, 2))
                    deviation_ratio = round(deviation_kwh / max(expected_kwh, 5.0), 2)

                    if deviation_ratio >= 0.50:
                        severity = "critical" if deviation_ratio >= 1.0 else "anomaly"
                        alerts_count += 1
                        alert_entry = AlertDB(
                            id=f"ALT-SIM-{uuid.uuid4().hex[:6].upper()}",
                            scenario_id=scenario_id,
                            data_source="simulated",
                            building_id=b_id,
                            building=b["name"],
                            type="Context-Aware Simulated Energy Leak",
                            severity=severity,
                            message=f"[{b['name']}] Elevated night load detected ({simulated_raw_kwh} kWh vs expected {expected_kwh} kWh).",
                            recommended_action="Inspect after-hours HVAC and lighting setpoint.",
                            estimated_waste_kwh=deviation_kwh,
                            estimated_cost_inr=round(deviation_kwh * tariff, 2),
                            status="pending"
                        )
                        db.add(alert_entry)

                    # Prepare hourly reading record
                    reading_dict = {
                        "building_id": b_id,
                        "timestamp": dt_str,
                        "month": month,
                        "occupancy_ratio": occ_ratio,
                        "temperature_diff_c": round(outdoor_temp - 24.0, 2),
                        "active_device_count": int(occ_ratio * 10 + 2),
                        "cooling_load_index": round(max(0.0, outdoor_temp - 24.0), 2),
                        "simulated_kwh": simulated_raw_kwh,
                        "predicted_kwh": predicted_kwh,
                    }
                    accumulated_readings.append(reading_dict)

                    db_reading = SimulatedReadingDB(
                        scenario_id=scenario_id,
                        data_source="simulated",
                        building_id=b_id,
                        timestamp=dt_str,
                        month=month,
                        occupancy_ratio=occ_ratio,
                        temperature_diff_c=reading_dict["temperature_diff_c"],
                        active_device_count=reading_dict["active_device_count"],
                        cooling_load_index=reading_dict["cooling_load_index"],
                        simulated_kwh=simulated_raw_kwh,
                        predicted_kwh=predicted_kwh,
                    )
                    db.add(db_reading)

                    completed_count += 1

                    # Batch flush to Supabase every 50 records
                    if len(accumulated_readings) >= 50:
                        supabase_service.store_simulated_readings(scenario_id, accumulated_readings)
                        accumulated_readings = []

                    # Update live progress DB counters
                    run_entry = db.query(SimulationScenarioRunDB).filter(SimulationScenarioRunDB.scenario_id == scenario_id).first()
                    if run_entry:
                        run_entry.completed_hourly_records = completed_count
                        run_entry.generated_records_count = completed_count
                        run_entry.alerts_detected_count = alerts_count
                        run_entry.current_timestamp = dt_str
                        run_entry.current_building_id = b_id

                    db.commit()

            # Final flush & completion validation
            if accumulated_readings:
                supabase_service.store_simulated_readings(scenario_id, accumulated_readings)

            tot_saved_kwh = max(0.0, round(tot_predicted_kwh - tot_optimized_kwh, 2))
            tot_saved_inr = round(tot_saved_kwh * tariff, 2)
            tot_co2_reduced = round(tot_saved_kwh * carbon_factor, 2)

            db_final = db.query(SimulationScenarioRunDB).filter(SimulationScenarioRunDB.scenario_id == scenario_id).first()
            if db_final and db_final.status in ("running", "stopping"):
                if completed_count != total_planned_records:
                    db_final.status = "failed"
                    db_final.failure_message = f"Incomplete simulation run. Expected {total_planned_records} records, but processed {completed_count}."
                    logger.error("Simulation run '%s' FAILED completion check: %d / %d records.", scenario_id, completed_count, total_planned_records)
                else:
                    db_final.status = "completed"
                    db_final.completed_at = datetime.now(timezone.utc).isoformat()
                    db_final.total_baseline_kwh = round(tot_baseline_kwh, 2)
                    db_final.total_predicted_kwh = round(tot_predicted_kwh, 2)
                    db_final.total_optimized_kwh = round(tot_optimized_kwh, 2)
                    db_final.total_saved_kwh = tot_saved_kwh
                    db_final.total_saved_inr = tot_saved_inr
                    db_final.total_co2_reduced_kg = tot_co2_reduced
                    logger.info("Controlled simulation scenario '%s' COMPLETED 100%% (%d/%d records). Totals: Saved %f kWh, ₹%f", scenario_id, completed_count, total_planned_records, tot_saved_kwh, tot_saved_inr)
                db.commit()

        except Exception as e:
            db.rollback()
            logger.error("Error in controlled simulation worker: %s", e)
            db_fail = db.query(SimulationScenarioRunDB).filter(SimulationScenarioRunDB.scenario_id == scenario_id).first()
            if db_fail:
                db_fail.status = "failed"
                db_fail.failure_message = str(e)
                db.commit()
        finally:
            db.close()

    @staticmethod
    def stop_controlled_simulation(scenario_id: str, db: Session = None) -> dict:
        """Signal cancellation for a running simulation scenario ID."""
        init_db()
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True

        try:
            sc = db.query(SimulationScenarioRunDB).filter(SimulationScenarioRunDB.scenario_id == scenario_id).first()
            if not sc:
                raise ValueError(f"Scenario ID '{scenario_id}' not found.")

            sc.cancel_requested = True
            sc.status = "stopping"
            db.commit()

            return {
                "success": True,
                "scenario_id": scenario_id,
                "status": "stopping",
                "message": f"Stop signal sent for simulation scenario '{scenario_id}'. Processing current hourly record before safe shutdown."
            }
        finally:
            if close_after:
                db.close()

    @staticmethod
    def get_simulation_progress(scenario_id: str, db: Session = None) -> SimulationProgressSchema:
        """Retrieve real-time simulation run status & live progress metrics."""
        init_db()
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True

        try:
            db.expire_all()
            sc = db.query(SimulationScenarioRunDB).filter(SimulationScenarioRunDB.scenario_id == scenario_id).first()
            if not sc:
                raise ValueError(f"Scenario ID '{scenario_id}' not found.")

            total = max(1, sc.total_hourly_records or 1)
            completed = sc.completed_hourly_records or 0
            pct = round(min(100.0, (completed / total) * 100.0), 1)

            return SimulationProgressSchema(
                scenario_id=sc.scenario_id,
                status=sc.status,
                cancel_requested=sc.cancel_requested or False,
                simulation_start_datetime=sc.simulation_start_datetime or "",
                simulation_end_datetime=sc.simulation_end_datetime or "",
                selected_scope=sc.building_ids or "ALL",
                total_hourly_records=total,
                completed_hourly_records=completed,
                completion_percentage=pct,
                current_timestamp=sc.current_timestamp,
                current_building_id=sc.current_building_id,
                generated_records_count=sc.generated_records_count or completed,
                alerts_detected_count=sc.alerts_detected_count or 0,
                started_at=sc.started_at,
                stopped_at=sc.stopped_at,
                completed_at=sc.completed_at,
                failure_message=sc.failure_message
            )
        finally:
            if close_after:
                db.close()

    @staticmethod
    def cleanup_simulated_records(scenario_id: str = None, db: Session = None) -> dict:
        """Safely delete simulation records from DB and Supabase where data_source='simulated'."""
        init_db()
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True

        try:
            if scenario_id:
                readings_deleted = db.query(SimulatedReadingDB).filter(
                    SimulatedReadingDB.scenario_id == scenario_id,
                    SimulatedReadingDB.data_source == "simulated"
                ).delete(synchronize_session=False)

                scenarios_deleted = db.query(SimulationScenarioRunDB).filter(
                    SimulationScenarioRunDB.scenario_id == scenario_id,
                    SimulationScenarioRunDB.data_source == "simulated_vignan_loop"
                ).delete(synchronize_session=False)

                alerts_deleted = db.query(AlertDB).filter(
                    AlertDB.scenario_id == scenario_id,
                    AlertDB.data_source == "simulated"
                ).delete(synchronize_session=False)
            else:
                readings_deleted = db.query(SimulatedReadingDB).filter(
                    SimulatedReadingDB.data_source == "simulated"
                ).delete(synchronize_session=False)

                scenarios_deleted = db.query(SimulationScenarioRunDB).filter(
                    SimulationScenarioRunDB.data_source == "simulated_vignan_loop"
                ).delete(synchronize_session=False)

                alerts_deleted = db.query(AlertDB).filter(
                    AlertDB.data_source == "simulated"
                ).delete(synchronize_session=False)

            db.commit()
            supabase_service.delete_simulated_records(scenario_id)

            return {
                "success": True,
                "readings_deleted": readings_deleted,
                "scenarios_deleted": scenarios_deleted,
                "alerts_deleted": alerts_deleted,
                "message": f"Successfully cleaned {readings_deleted} simulated records, {scenarios_deleted} scenario runs, and {alerts_deleted} simulation alerts."
            }
        except Exception as e:
            db.rollback()
            logger.error("Error cleaning simulated records: %s", e)
            raise e
        finally:
            if close_after:
                db.close()

    @staticmethod
    def run_loop_simulation(req: LoopSimulationRequestSchema, db: Session = None) -> LoopSimulationResponseSchema:
        """Backward compatible synchronous run endpoint."""
        init_db()
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True

        try:
            if req.clean_previous:
                LoopSimulationService.cleanup_simulated_records(db=db)

            scenario_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"

            start_date = req.from_date or "2025-07-01"
            end_date = req.to_date or "2025-07-31"

            target_buildings = LoopSimulationService._get_target_buildings(req.building_id, req.building_ids, db)
            b_name = target_buildings[0]["name"] if len(target_buildings) == 1 else "All Vignan Campus Blocks"

            tariff = CAMPUS.get("tariff_inr_per_kwh", 8.75)
            carbon_factor = CAMPUS.get("grid_carbon_kg_per_kwh", 0.82)

            date_range = pd.date_range(f"{start_date} 00:00:00", f"{end_date} 23:00:00", freq="1h")
            records = []
            rng = np.random.default_rng(seed=42)

            for dt in date_range:
                month = dt.month
                hour = dt.hour
                for b in target_buildings:
                    b_id = b["id"]
                    base_kw = b["base_kw"]
                    category = b["category"]
                    day_type, time_window = ContextAwareAnomalyEngine._classify_day_and_window(dt.to_pydatetime(), category)
                    outdoor_temp = WEATHER["mean_temp_c"] + np.sin(2 * np.pi * (hour - 15) / 24.0) * WEATHER["daily_amplitude_c"] + rng.normal(0, 0.4)

                    expected_kwh, _ = ContextAwareAnomalyEngine._calculate_expected_kwh(
                        category, base_kw, day_type, time_window, hour, 0.5, outdoor_temp
                    )

                    sim_kwh = expected_kwh * 1.05
                    pred_kwh = sim_kwh * (1.0 + 0.015 * max(0.0, outdoor_temp - 30.0))
                    opt_kwh = pred_kwh * (1.0 - abs(req.temperature_delta) * 0.06)

                    records.append({
                        "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "date": dt.strftime("%Y-%m-%d"),
                        "building_id": b_id,
                        "month": month,
                        "hour": hour,
                        "outdoor_temperature_c": outdoor_temp,
                        "occupancy_ratio": 0.5,
                        "temperature_diff_c": round(outdoor_temp - 24.0, 2),
                        "active_device_count": 5,
                        "cooling_load_index": round(max(0.0, outdoor_temp - 24.0), 2),
                        "simulated_raw_kwh": sim_kwh,
                        "predicted_kwh": pred_kwh,
                        "optimized_kwh": opt_kwh
                    })

            processed_df = pd.DataFrame(records)

            total_baseline_kwh = float(processed_df["simulated_raw_kwh"].sum())
            total_predicted_kwh = float(processed_df["predicted_kwh"].sum())
            total_optimized_kwh = float(processed_df["optimized_kwh"].sum())
            total_saved_kwh = total_predicted_kwh - total_optimized_kwh
            total_predicted_cost_inr = total_predicted_kwh * tariff
            total_saved_inr = total_saved_kwh * tariff
            total_co2_reduced = total_saved_kwh * carbon_factor

            # Store to Supabase & local DB
            hourly_readings_to_store = [
                {
                    "building_id": str(row["building_id"]),
                    "timestamp": str(row["timestamp"]),
                    "month": int(row["month"]),
                    "occupancy_ratio": float(row["occupancy_ratio"]),
                    "temperature_diff_c": float(row["temperature_diff_c"]),
                    "active_device_count": int(row["active_device_count"]),
                    "cooling_load_index": float(row["cooling_load_index"]),
                    "simulated_kwh": round(float(row["simulated_raw_kwh"]), 2),
                    "predicted_kwh": round(float(row["predicted_kwh"]), 2),
                }
                for _, row in processed_df.iterrows()
            ]

            supabase_res = supabase_service.store_simulated_readings(scenario_id, hourly_readings_to_store)

            scenario_run = SimulationScenarioRunDB(
                scenario_id=scenario_id,
                data_source="simulated_vignan_loop",
                status="completed",
                months_run=json.dumps(list(set([int(m) for m in processed_df["month"].unique()]))),
                building_ids=json.dumps([b["id"] for b in target_buildings]),
                temperature_delta=req.temperature_delta,
                occupancy_scale=req.occupancy_scale,
                include_solar=req.include_solar,
                total_baseline_kwh=round(total_baseline_kwh, 2),
                total_predicted_kwh=round(total_predicted_kwh, 2),
                total_optimized_kwh=round(total_optimized_kwh, 2),
                total_saved_kwh=round(total_saved_kwh, 2),
                total_saved_inr=round(total_saved_inr, 2),
                total_co2_reduced_kg=round(total_co2_reduced, 2),
                monthly_summary_json=json.dumps([]),
            )
            db.add(scenario_run)
            db.commit()

            return LoopSimulationResponseSchema(
                run_id=scenario_id,
                scenario_id=scenario_id,
                data_source="simulated_vignan_loop",
                from_date=start_date,
                to_date=end_date,
                building_id=req.building_id,
                building_name=b_name,
                months_simulated=list(set([int(m) for m in processed_df["month"].unique()])),
                total_buildings=len(target_buildings),
                total_intervals=len(processed_df),
                total_records=len(processed_df),
                temperature_delta=req.temperature_delta,
                occupancy_scale=req.occupancy_scale,
                predicted_energy_kwh=round(total_predicted_kwh, 2),
                predicted_cost_inr=round(total_predicted_cost_inr, 2),
                estimated_saved_kwh=round(total_saved_kwh, 2),
                estimated_saved_inr=round(total_saved_inr, 2),
                carbon_avoided_kg=round(total_co2_reduced, 2),
                peak_demand_kw=186.0,
                supabase_status=supabase_res.get("status", "local_sqlite"),
                persistence_status=f"Stored {len(hourly_readings_to_store)} hourly records in database.",
                monthly_breakdown=[],
                chart_series=[]
            )
        finally:
            if close_after:
                db.close()

    @staticmethod
    def get_scenarios(db: Session = None) -> list[ScenarioListItemSchema]:
        init_db()
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True
        try:
            scenarios = db.query(SimulationScenarioRunDB).order_by(SimulationScenarioRunDB.created_at.desc()).all()
            results = []
            for sc in scenarios:
                months = json.loads(sc.months_run or "[]")
                results.append(
                    ScenarioListItemSchema(
                        scenario_id=sc.scenario_id,
                        data_source=sc.data_source,
                        months_count=len(months),
                        temperature_delta=sc.temperature_delta,
                        total_saved_kwh=sc.total_saved_kwh or 0.0,
                        total_saved_inr=sc.total_saved_inr or 0.0,
                        total_co2_reduced_kg=sc.total_co2_reduced_kg or 0.0,
                        status=sc.status,
                        created_at=sc.created_at.isoformat() if sc.created_at else "",
                    )
                )
            return results
        finally:
            if close_after:
                db.close()

    @staticmethod
    def get_scenario_detail(scenario_id: str, db: Session = None) -> ScenarioDetailSchema:
        init_db()
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True
        try:
            sc = db.query(SimulationScenarioRunDB).filter(SimulationScenarioRunDB.scenario_id == scenario_id).first()
            if not sc:
                raise ValueError(f"Scenario ID '{scenario_id}' not found.")

            readings = db.query(SimulatedReadingDB).filter(
                SimulatedReadingDB.scenario_id == scenario_id,
                SimulatedReadingDB.data_source == "simulated"
            ).all()
            readings_count = len(readings)

            tot_baseline = sc.total_baseline_kwh or 0.0
            tot_predicted = sc.total_predicted_kwh or 0.0
            tot_optimized = sc.total_optimized_kwh or 0.0
            tot_saved_kwh = sc.total_saved_kwh or 0.0
            tot_saved_inr = sc.total_saved_inr or 0.0
            tot_co2 = sc.total_co2_reduced_kg or 0.0

            if (tot_predicted == 0.0 or tot_saved_kwh == 0.0) and readings_count > 0:
                tot_baseline = round(sum(r.simulated_kwh for r in readings), 2)
                tot_predicted = round(sum(r.predicted_kwh for r in readings), 2)
                saving_pct = abs(sc.temperature_delta or 2.0) * 0.06
                tot_optimized = round(tot_predicted * (1.0 - saving_pct), 2)
                tot_saved_kwh = max(0.0, round(tot_predicted - tot_optimized, 2))
                tot_saved_inr = round(tot_saved_kwh * 8.75, 2)
                tot_co2 = round(tot_saved_kwh * 0.82, 2)

            months = json.loads(sc.months_run or "[]")
            b_ids = json.loads(sc.building_ids or "[]")

            return ScenarioDetailSchema(
                scenario_id=sc.scenario_id,
                data_source=sc.data_source,
                months_run=months,
                building_ids=b_ids,
                temperature_delta=sc.temperature_delta,
                occupancy_scale=sc.occupancy_scale,
                include_solar=sc.include_solar,
                total_baseline_kwh=tot_baseline,
                total_predicted_kwh=tot_predicted,
                total_optimized_kwh=tot_optimized,
                total_saved_kwh=tot_saved_kwh,
                total_saved_inr=tot_saved_inr,
                total_co2_reduced_kg=tot_co2,
                monthly_breakdown=[],
                preprocessed_records_stored=readings_count,
                created_at=sc.created_at.isoformat() if sc.created_at else "",
            )
        finally:
            if close_after:
                db.close()


loop_simulation_service = LoopSimulationService()
