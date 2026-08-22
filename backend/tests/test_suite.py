import sys
import unittest
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.database.database import SessionLocal, init_db
from app.repositories.db_repository import db_repository
from app.routes.health import health_check, readiness_check
from app.schemas.cost_prediction import CostPredictionRequestSchema
from app.services.agent_orchestrator import agent_orchestration_service
from app.services.artifact_ingestion import artifact_ingestion_service
from app.services.cost_prediction_service import cost_prediction_service
from app.services.db_seed import seed_database
from app.services.gemini_service import gemini_service


class TestEcoMindSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_database()

    def test_01_core_config(self):
        self.assertEqual(settings.VERSION, "1.0.0")
        self.assertTrue(settings.GENERATED_DATA_DIR.exists())

    def test_02_health_and_readiness(self):
        h = health_check()
        self.assertEqual(h.status, "healthy")
        self.assertEqual(h.service, "ecomind-api")

        r = readiness_check()
        self.assertTrue(r.ml_artifacts_present)

    def test_03_db_persistence(self):
        buildings = db_repository.get_buildings()
        self.assertGreater(len(buildings), 0)

        snapshot = db_repository.get_snapshot()
        self.assertIn("energy_used_today_kwh", snapshot)
        self.assertGreater(snapshot["carbon_avoided_kg"], 0)

    def test_04_artifact_ingestion(self):
        res = artifact_ingestion_service.ingest_all_phase1_artifacts("RUN-TEST-SUITE")
        self.assertTrue(res["buildings"]["schema_valid"])
        self.assertEqual(res["buildings"]["status"], "ingested")

        bad_res = artifact_ingestion_service.ingest_artifact("RUN-BAD", "buildings", "invalid.csv")
        self.assertFalse(bad_res["schema_valid"])
        self.assertEqual(bad_res["status"], "rejected")

    def test_05_agent_orchestration(self):
        history = agent_orchestration_service.get_run_history()
        self.assertGreater(len(history), 0)

        pipe_res = agent_orchestration_service.execute_full_pipeline("RUN-SUITE-TEST")
        self.assertEqual(pipe_res["run_id"], "RUN-SUITE-TEST")

    def test_06_cost_prediction_engine(self):
        req = CostPredictionRequestSchema(
            previous_month_cost_inr=55536.51,
            target_month="October 2026",
            expected_temperature_c=32.0,
            is_exam_season=False
        )
        res = cost_prediction_service.predict_next_month_cost(req)
        self.assertEqual(res.target_month, "October 2026")
        self.assertGreater(res.predicted_cost_inr, 0)
        self.assertGreater(len(res.top_cost_drivers), 0)
        self.assertGreater(res.scenarios.pessimistic_inr, res.scenarios.optimistic_inr)

    def test_07_audit_logging(self):
        res = db_repository.apply_action("REC-HVAC-001")
        self.assertTrue(res["success"])

        snapshot = db_repository.get_snapshot()
        self.assertGreater(snapshot["active_actions_count"], 0)

    def test_08_api_repositories(self):
        forecast = db_repository.get_forecast()
        self.assertIn("actual", forecast)
        self.assertIn("forecast", forecast)

        alerts = db_repository.get_alerts()
        self.assertGreater(len(alerts), 0)

        sustainability = db_repository.get_sustainability_data()
        self.assertIn("green_leaderboard", sustainability)

    def test_09_gemini_intelligence_service(self):
        # 1. Forecast Explainer
        cost_exp = gemini_service.explain_cost_forecast()
        self.assertIsNotNone(cost_exp.summary)
        self.assertGreater(len(cost_exp.top_drivers), 0)

        # 2. Anomaly Explainer
        anom_sum = gemini_service.summarize_anomalies()
        self.assertGreater(anom_sum.total_anomalies_count, 0)
        self.assertIsNotNone(anom_sum.operational_advice)

        # 3. Recommendation Advisor
        app_supp = gemini_service.evaluate_approval_support("REC-HVAC-001")
        self.assertEqual(app_supp.verdict, "APPROVE")
        self.assertIsNotNone(app_supp.reasoning)

        # 4. Scenario Analyst
        sc_analysis = gemini_service.analyze_scenarios()
        self.assertIsNotNone(sc_analysis.narrative_comparison)
        self.assertGreater(sc_analysis.pessimistic_cost_inr, sc_analysis.optimistic_cost_inr)

        # 5. Executive Report Writer
        exec_rep = gemini_service.generate_executive_report()
        self.assertIsNotNone(exec_rep.executive_summary)
        self.assertGreater(len(exec_rep.strategic_action_plan), 0)

        # 6. Natural Language Q&A Engine
        qa_res = gemini_service.answer_natural_language_question("Which building consumed the most energy?")
        self.assertIsNotNone(qa_res.answer)
        self.assertGreater(len(qa_res.cited_metrics), 0)


if __name__ == "__main__":
    unittest.main()
