import json
import logging
from sqlalchemy.orm import Session

from app.database.database import SessionLocal, init_db
from app.models.db_models import (
    AlertDB, BuildingDB, CampusDB, RecommendationDB,
    SustainabilityReportDB, UserDB
)
from app.services import ml_bridge

logger = logging.getLogger("ecomind.seed")


def seed_database(db: Session = None):
    init_db()
    close_after = False
    if db is None:
        db = SessionLocal()
        close_after = True

    try:
        # 1. Seed User
        if db.query(UserDB).count() == 0:
            user = UserDB(
                id="jordan-davis",
                name="Jordan Davis",
                email="jordan@vignan.ac.in",
                role="Energy manager"
            )
            db.add(user)
            logger.info("Seeded admin user.")

        # 2. Seed Campus & Buildings
        if db.query(CampusDB).count() == 0:
            weekly_report = ml_bridge.load_weekly_report_json()
            campus_info = weekly_report.get("campus", {})
            campus = CampusDB(
                id="VIGNAN",
                name=campus_info.get("name", "Vignan University"),
                location=campus_info.get("location", "Vadlamudi, Guntur, AP"),
                latitude=campus_info.get("latitude", 16.2347),
                longitude=campus_info.get("longitude", 80.5516),
                tariff_inr_per_kwh=campus_info.get("tariff_inr_per_kwh", 8.75),
                grid_carbon_kg_per_kwh=campus_info.get("grid_carbon_kg_per_kwh", 0.82)
            )
            db.add(campus)

        if db.query(BuildingDB).count() == 0:
            df_b = ml_bridge.load_buildings_df()
            if not df_b.empty:
                for idx, row in df_b.iterrows():
                    b_id = str(row.get("building_id", f"BLK-{idx}"))
                    area = float(row.get("area_sqm", 5000))
                    base_kw = round(area * 0.015, 1)
                    max_cap = area * 0.025 if area > 0 else 100
                    load_pct = min(99, max(15, int((base_kw / max_cap) * 100)))
                    status = "high" if load_pct > 80 else ("warning" if load_pct > 70 else "normal")

                    b_db = BuildingDB(
                        id=b_id,
                        campus_id="VIGNAN",
                        name=str(row.get("building_name", b_id)),
                        category=str(row.get("category", "academic")),
                        area_sqm=area,
                        floors=int(row.get("floors", 3)),
                        current_kw=base_kw,
                        load_percent=load_pct,
                        status=status
                    )
                    db.add(b_db)
                logger.info(f"Seeded {len(df_b)} buildings from ML digital twin.")

        # 3. Seed Recommendations
        if db.query(RecommendationDB).count() == 0:
            recs = ml_bridge.load_recommendations_json()
            for r in recs:
                rec_db = RecommendationDB(
                    recommendation_id=r.get("recommendation_id"),
                    category=r.get("category", "hvac_optimization"),
                    title=r.get("title", "Optimization Action"),
                    description=r.get("description", ""),
                    priority_score=r.get("priority_score", 50),
                    buildings_json=json.dumps(r.get("buildings", [])),
                    energy_saved_kwh=r.get("energy_saved_kwh", 0.0),
                    money_saved_inr=r.get("money_saved_inr", 0.0),
                    co2_reduced_kg=r.get("co2_reduced_kg", 0.0),
                    applied=False
                )
                db.add(rec_db)
            logger.info(f"Seeded {len(recs)} ML recommendations.")

        # 4. Seed Alerts
        if db.query(AlertDB).count() == 0:
            df_a = ml_bridge.load_alerts_df()
            if not df_a.empty:
                sample_a = df_a.head(20)
                for idx, row in sample_a.iterrows():
                    alert_id = f"ALT-{idx+100}"
                    alert_db = AlertDB(
                        id=alert_id,
                        building_id=str(row.get("building_id", "BLK-A")),
                        building=str(row.get("building_name", "Academic Block A")),
                        type=str(row.get("injected_fault", "Spike")).replace("_", " ").title(),
                        severity=str(row.get("severity", "medium")).lower(),
                        message=str(row.get("reason", "Anomaly detected")),
                        recommended_action=str(row.get("recommended_action", "Check controls")),
                        estimated_waste_kwh=round(float(row.get("estimated_waste_kwh", 2.5)), 2),
                        estimated_cost_inr=round(float(row.get("estimated_cost_inr", 21.8)), 2),
                        status="pending"
                    )
                    db.add(alert_db)
                logger.info("Seeded anomaly alerts.")

        # 5. Seed Sustainability Weekly Reports
        if db.query(SustainabilityReportDB).count() == 0:
            weekly_report = ml_bridge.load_weekly_report_json()
            weekly_list = weekly_report.get("weekly", [])
            for w in weekly_list:
                s_db = SustainabilityReportDB(
                    week_period=w.get("week", "2025-07-01"),
                    energy_kwh=w.get("energy_kwh", 0.0),
                    energy_saved_kwh=w.get("energy_saved_kwh", 0.0),
                    money_saved_inr=w.get("money_saved_inr", 0.0),
                    co2_reduced_kg=w.get("co2_reduced_kg", 0.0),
                    sustainability_score=w.get("sustainability_score", 70.0)
                )
                db.add(s_db)
            logger.info("Seeded weekly sustainability reports.")

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
    finally:
        if close_after:
            db.close()
