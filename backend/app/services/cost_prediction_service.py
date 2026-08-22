import json
import logging
from sqlalchemy.orm import Session

from app.database.database import SessionLocal, init_db
from app.models.db_models import CostPredictionDB
from app.schemas.cost_prediction import (
    ConfidenceRangeSchema, CostPredictionRequestSchema,
    CostPredictionResponseSchema, DriverImpactSchema,
    RecommendedSavingsActionSchema, ScenariosSchema
)

logger = logging.getLogger("ecomind.cost_prediction")


class CostPredictionService:
    @staticmethod
    def predict_next_month_cost(
        req: CostPredictionRequestSchema, db: Session = None
    ) -> CostPredictionResponseSchema:
        init_db()
        close_after = False
        if db is None:
            db = SessionLocal()
            close_after = True

        # 1. Base consumption & parameters
        prev_kwh = req.previous_month_kwh
        prev_cost = req.previous_month_cost_inr
        tariff = req.tariff_inr_per_kwh

        # 2. Weather & Cooling Load Adjustment
        base_temp = 28.0
        temp_diff = max(0.0, req.expected_temperature_c - base_temp)
        # Every 1 deg C above 28 C adds 3.5% HVAC load
        weather_impact_pct = temp_diff * 0.035

        # 3. Operational Factors (Exam Season & Occupancy)
        exam_impact_pct = 0.08 if req.is_exam_season else 0.0
        occupancy_impact_pct = (req.occupancy_ratio - 0.70) * 0.15

        total_multiplier = 1.0 + weather_impact_pct + exam_impact_pct + occupancy_impact_pct

        # 4. Projected Consumption & Financial Calculations
        predicted_kwh = prev_kwh * total_multiplier
        predicted_cost_inr = predicted_kwh * tariff

        mom_change_pct = ((predicted_cost_inr - prev_cost) / prev_cost) * 100.0

        # 5. Scenarios (Optimistic, Baseline, Pessimistic)
        optimistic_inr = round(predicted_cost_inr * 0.876, 2)  # EcoMind closed-loop 12.4% setback
        baseline_inr = round(predicted_cost_inr, 2)
        pessimistic_inr = round(predicted_cost_inr * 1.125, 2)  # Heatwave / extended lab hours

        # 6. Driver Explanations
        drivers = [
            DriverImpactSchema(
                driver="Outdoor Weather & Cooling Load",
                impact_percent=round(weather_impact_pct * 100, 1),
                description=f"Expected temp {req.expected_temperature_c}°C (+{round(temp_diff, 1)}°C above 28°C baseline) increases HVAC load."
            ),
            DriverImpactSchema(
                driver="Academic Calendar / Exam Operations",
                impact_percent=round(exam_impact_pct * 100, 1),
                description="Exam period extends library and computer laboratory operating hours." if req.is_exam_season else "Standard academic schedule."
            ),
            DriverImpactSchema(
                driver="Campus Occupancy Factor",
                impact_percent=round(occupancy_impact_pct * 100, 1),
                description=f"Campus occupancy at {int(req.occupancy_ratio * 100)}% capacity."
            )
        ]

        # 7. Recommended Savings Actions
        rec_actions = [
            RecommendedSavingsActionSchema(
                title="Apply After-Hours HVAC Setback",
                estimated_savings_inr=round(predicted_cost_inr * 0.08, 2),
                action_type="setback"
            ),
            RecommendedSavingsActionSchema(
                title="Pre-Cool CSE Labs Before Peak Heat",
                estimated_savings_inr=round(predicted_cost_inr * 0.044, 2),
                action_type="precooling"
            )
        ]

        # 8. Store prediction audit log in SQLite DB
        try:
            db_record = CostPredictionDB(
                target_month=req.target_month,
                previous_cost_inr=prev_cost,
                predicted_cost_inr=baseline_inr,
                predicted_kwh=round(predicted_kwh, 2),
                mom_change_percent=round(mom_change_pct, 2),
                optimistic_cost_inr=optimistic_inr,
                pessimistic_cost_inr=pessimistic_inr,
                drivers_json=json.dumps([d.model_dump() for d in drivers])
            )
            db.add(db_record)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving cost prediction record: {e}")
        finally:
            if close_after:
                db.close()

        return CostPredictionResponseSchema(
            target_month=req.target_month,
            predicted_cost_inr=baseline_inr,
            predicted_energy_kwh=round(predicted_kwh, 2),
            confidence_range_inr=ConfidenceRangeSchema(
                min_cost_inr=round(baseline_inr * 0.95, 2),
                max_cost_inr=round(baseline_inr * 1.05, 2)
            ),
            mom_change_percent=round(mom_change_pct, 2),
            top_cost_drivers=drivers,
            scenarios=ScenariosSchema(
                optimistic_inr=optimistic_inr,
                baseline_inr=baseline_inr,
                pessimistic_inr=pessimistic_inr
            ),
            recommended_savings_actions=rec_actions
        )


cost_prediction_service = CostPredictionService()
