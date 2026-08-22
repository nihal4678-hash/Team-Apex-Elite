import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.db_models import (
    AlertDB, AuditLogDB, BuildingDB, RecommendationDB,
    SimulationDB, SustainabilityReportDB
)
from app.services import ml_bridge


class DBRepository:
    @staticmethod
    def get_buildings(db: Session = None) -> list[dict]:
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True
        try:
            buildings_db = db.query(BuildingDB).all()
            if not buildings_db:
                # Fallback if DB not seeded
                return []
            return [
                {
                    "id": b.id,
                    "name": b.name,
                    "category": b.category,
                    "area_sqm": b.area_sqm,
                    "kw": b.current_kw,
                    "load": b.load_percent,
                    "status": b.status,
                }
                for b in buildings_db
            ]
        finally:
            if close_after:
                db.close()

    @staticmethod
    def get_snapshot(db: Session = None) -> dict:
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True
        try:
            weekly_report = ml_bridge.load_weekly_report_json()
            monthly = weekly_report.get("monthly_savings", {})

            # Count persistent applied actions and resolved alerts from DB
            applied_count = db.query(RecommendationDB).filter(RecommendationDB.applied == True).count()
            resolved_count = db.query(AlertDB).filter(AlertDB.status == "resolved").count()

            # Calculate accumulated extra savings from applied recommendations in DB
            applied_recs = db.query(RecommendationDB).filter(RecommendationDB.applied == True).all()
            extra_kwh = sum(r.energy_saved_kwh for r in applied_recs)
            extra_inr = sum(r.money_saved_inr for r in applied_recs)
            extra_co2 = sum(r.co2_reduced_kg for r in applied_recs)

            base_kwh = monthly.get("energy_kwh", 6347.03) + extra_kwh
            base_inr = monthly.get("money_inr", 55536.51) + extra_inr
            base_co2 = monthly.get("co2_kg", 5204.56) + extra_co2

            return {
                "energy_used_today_kwh": 847.0,
                "energy_saved_month_kwh": round(base_kwh, 2),
                "energy_cost_today_inr": 124.80,
                "money_saved_month_inr": round(base_inr, 2),
                "carbon_avoided_kg": round(base_co2, 2),
                "peak_demand_kw": 186.0,
                "weekly_change_percent": -12.4,
                "active_actions_count": applied_count,
                "resolved_alerts_count": resolved_count,
            }
        finally:
            if close_after:
                db.close()

    @staticmethod
    def get_forecast() -> dict:
        df = ml_bridge.load_forecast_df()
        if not df.empty and "predicted_energy_kwh" in df.columns:
            df_hourly = df.groupby("hour")["predicted_energy_kwh"].mean().reset_index()
            df_hourly["actual"] = df.groupby("hour")["energy_kwh"].mean().values
            actuals = [round(v, 1) for v in df_hourly["actual"].head(16).tolist()]
            forecasts = [round(v, 1) for v in df_hourly["predicted_energy_kwh"].tail(8).tolist()]
            return {"actual": actuals, "forecast": forecasts}
        return {
            "actual": [52, 61, 57, 66, 72, 69, 78, 74, 83, 79, 88, 84, 91, 86, 94, 90],
            "forecast": [82, 76, 69, 62, 56, 49, 45, 42],
        }

    @staticmethod
    def get_alerts(db: Session = None) -> list[dict]:
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True
        try:
            alerts_db = db.query(AlertDB).all()
            return [
                {
                    "id": a.id,
                    "building_id": a.building_id,
                    "building": a.building,
                    "type": a.type,
                    "severity": a.severity,
                    "message": a.message,
                    "recommended_action": a.recommended_action,
                    "estimated_waste_kwh": a.estimated_waste_kwh,
                    "estimated_cost_inr": a.estimated_cost_inr,
                    "status": a.status,
                }
                for a in alerts_db
            ]
        finally:
            if close_after:
                db.close()

    @staticmethod
    def get_recommendations(db: Session = None) -> list[dict]:
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True
        try:
            recs_db = db.query(RecommendationDB).all()
            return [
                {
                    "recommendation_id": r.recommendation_id,
                    "category": r.category,
                    "title": r.title,
                    "description": r.description,
                    "priority_score": r.priority_score,
                    "buildings": json.loads(r.buildings_json or "[]"),
                    "energy_saved_kwh": r.energy_saved_kwh,
                    "money_saved_inr": r.money_saved_inr,
                    "co2_reduced_kg": r.co2_reduced_kg,
                    "applied": r.applied,
                    "applied_at": r.applied_at,
                }
                for r in recs_db
            ]
        finally:
            if close_after:
                db.close()

    @staticmethod
    def apply_action(action_id: str, params: dict = None, db: Session = None) -> dict:
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True
        try:
            now_str = datetime.now(timezone.utc).isoformat()
            rec = db.query(RecommendationDB).filter(RecommendationDB.recommendation_id == action_id).first()

            saved_kwh = rec.energy_saved_kwh if rec else 150.0
            saved_inr = rec.money_saved_inr if rec else 1312.5
            saved_co2 = rec.co2_reduced_kg if rec else 123.0

            if rec:
                rec.applied = True
                rec.applied_at = now_str

                # Reduce building loads for affected buildings in DB
                affected_buildings = json.loads(rec.buildings_json or "[]")
                for b_id in affected_buildings:
                    b_obj = db.query(BuildingDB).filter(BuildingDB.id == b_id).first()
                    if b_obj:
                        b_obj.current_kw = max(30.0, round(b_obj.current_kw * 0.88, 1))
                        b_obj.load_percent = max(15, int(b_obj.load_percent * 0.88))

            # Record persistent Audit Log
            audit = AuditLogDB(
                user_id="jordan-davis",
                action="apply_recommendation",
                target_type="recommendation",
                target_id=action_id,
                details_json=json.dumps({"saved_kwh": saved_kwh, "saved_inr": saved_inr, "saved_co2": saved_co2, "params": params or {}})
            )
            db.add(audit)
            db.commit()

            return {
                "success": True,
                "action_id": action_id,
                "status": "applied",
                "saved_kwh": saved_kwh,
                "saved_inr": saved_inr,
                "saved_co2_kg": saved_co2,
                "applied_at": now_str,
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            if close_after:
                db.close()

    @staticmethod
    def resolve_alert(alert_id: str, db: Session = None) -> dict:
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True
        try:
            alert = db.query(AlertDB).filter(AlertDB.id == alert_id).first()
            if alert:
                alert.status = "resolved"

            audit = AuditLogDB(
                user_id="jordan-davis",
                action="resolve_alert",
                target_type="alert",
                target_id=alert_id,
                details_json=json.dumps({"status": "resolved"})
            )
            db.add(audit)
            db.commit()
            return {"success": True, "alert_id": alert_id, "status": "resolved"}
        except Exception as e:
            db.rollback()
            raise e
        finally:
            if close_after:
                db.close()

    @staticmethod
    def run_simulation(building_id: str, temp_delta: float, duration_minutes: int, db: Session = None) -> dict:
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True
        try:
            b_obj = db.query(BuildingDB).filter(BuildingDB.id == building_id).first()
            base_kw = b_obj.current_kw if b_obj else 200.0

            saving_pct = abs(temp_delta) * 0.06
            saved_kw = base_kw * saving_pct
            saved_kwh = saved_kw * (duration_minutes / 60.0)
            saved_inr = saved_kwh * 8.75
            saved_co2 = saved_kwh * 0.82

            sim_record = SimulationDB(
                building_id=building_id,
                temp_delta=temp_delta,
                duration_minutes=duration_minutes,
                saved_kwh=round(saved_kwh, 2),
                estimated_savings_inr=round(saved_inr, 2),
                co2_reduced_kg=round(saved_co2, 2),
                status="completed"
            )
            db.add(sim_record)

            audit = AuditLogDB(
                user_id="jordan-davis",
                action="run_simulation",
                target_type="simulation",
                target_id=building_id,
                details_json=json.dumps({"temp_delta": temp_delta, "saved_kwh": saved_kwh, "saved_inr": saved_inr})
            )
            db.add(audit)
            db.commit()

            return {
                "building_id": building_id,
                "temp_delta": temp_delta,
                "duration_minutes": duration_minutes,
                "saved_kwh": round(saved_kwh, 2),
                "estimated_savings_inr": round(saved_inr, 2),
                "co2_reduced_kg": round(saved_co2, 2),
                "status": "simulation_complete",
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            if close_after:
                db.close()

    @staticmethod
    def get_sustainability_data(db: Session = None) -> dict:
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True
        try:
            snapshot = DBRepository.get_snapshot(db)
            weekly_data = ml_bridge.load_weekly_report_json()
            return {
                "carbon_avoided_kg": snapshot["carbon_avoided_kg"],
                "energy_saved_month_kwh": snapshot["energy_saved_month_kwh"],
                "money_saved_month_inr": snapshot["money_saved_month_inr"],
                "energy_intensity": "12.4% below baseline",
                "campus_info": weekly_data.get("campus", {}),
                "green_leaderboard": weekly_data.get("green_leaderboard", []),
                "weekly_history": weekly_data.get("weekly", []),
            }
        finally:
            if close_after:
                db.close()


db_repository = DBRepository()
