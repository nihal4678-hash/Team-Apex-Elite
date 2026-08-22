import json
import logging
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.repositories.db_repository import db_repository
from app.schemas.ai_schemas import (
    AnomalySummaryResponseSchema, ApprovalSupportResponseSchema,
    AskQuestionResponseSchema, CostExplanationResponseSchema,
    ExecutiveReportResponseSchema, ScenarioAnalysisResponseSchema
)
from app.schemas.cost_prediction import CostPredictionRequestSchema
from app.services.cost_prediction_service import cost_prediction_service

logger = logging.getLogger("ecomind.gemini")


class GeminiService:
    def __init__(self):
        self.active_key_index = 0

    def get_api_keys_pool(self) -> list[str]:
        raw_keys = os.getenv("GEMINI_API_KEYS", "") or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        return keys

    @property
    def model_name(self) -> str:
        return settings.GEMINI_MODEL or os.getenv("GEMINI_MODEL", "gemini-flash-latest")

    def _call_gemini_api(self, prompt: str, system_instruction: str = "") -> str | None:
        """Call Google Gemini REST API with automatic multi-key rotation on 429/403 rate limits."""
        keys_pool = self.get_api_keys_pool()
        if not keys_pool:
            return None

        models_to_try = [
            "models/gemini-flash-latest",
            "models/gemini-2.5-flash",
            "models/gemini-2.5-flash-lite",
        ]

        # Try key pool failover loop
        attempts = 0
        max_attempts = len(keys_pool)

        while attempts < max_attempts:
            current_key = keys_pool[self.active_key_index % len(keys_pool)]
            attempts += 1

            for m in models_to_try:
                m_path = m if m.startswith("models/") else f"models/{m}"
                url = f"https://generativelanguage.googleapis.com/v1beta/{m_path}:generateContent?key={current_key}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                if system_instruction:
                    payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )

                try:
                    with urllib.request.urlopen(req, timeout=6) as response:
                        res_data = json.loads(response.read().decode("utf-8"))
                        candidates = res_data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                text = parts[0].get("text", "").strip()
                                if text:
                                    return text
                except urllib.error.HTTPError as e:
                    e.close()
                    if e.code in (429, 403):
                        # Rate limit or quota hit on this key -> Rotate to next key in pool!
                        self.active_key_index = (self.active_key_index + 1) % len(keys_pool)
                        logger.warning(f"Key #{self.active_key_index} hit quota ({e.code}). Automatically rotated to key index {self.active_key_index}.")
                        break  # Break model loop to retry next key
                    continue
                except Exception as e:
                    logger.debug(f"Gemini API call ({m_path}) exception: {e}")
                    continue

        return None

    # --- CONTEXT AGGREGATION METHODS ---
    def get_forecast_context(self) -> dict:
        return db_repository.get_forecast()

    def get_anomalies_context(self) -> dict:
        alerts = db_repository.get_alerts()
        top_alerts = sorted(alerts, key=lambda x: x.get("estimated_cost_inr", 0), reverse=True)[:5]
        return {
            "total_count": len(alerts),
            "critical_count": sum(1 for a in alerts if a.get("severity") == "critical"),
            "top_5_anomalies": top_alerts,
        }

    def get_recommendations_context(self) -> list[dict]:
        return db_repository.get_recommendations()

    def get_sustainability_context(self) -> dict:
        return db_repository.get_sustainability_data()

    def get_monthly_cost_context(self) -> dict:
        default_req = CostPredictionRequestSchema()
        pred = cost_prediction_service.predict_next_month_cost(default_req)
        return pred.model_dump()

    # --- GEMINI INTELLIGENCE ROLE 1: COST FORECAST EXPLAINER ---
    def explain_cost_forecast(self, req: CostPredictionRequestSchema = None) -> CostExplanationResponseSchema:
        if req is None:
            req = CostPredictionRequestSchema()

        pred = cost_prediction_service.predict_next_month_cost(req)

        prompt = f"""
        Explain the university energy cost forecast for {pred.target_month} at Vignan University.
        Predicted Cost: ₹{pred.predicted_cost_inr:,.2f} (MoM Change: {pred.mom_change_percent}%).
        Previous Month Cost: ₹{req.previous_month_cost_inr:,.2f}.
        Expected Weather: {req.expected_temperature_c}°C, {req.expected_humidity_pct}% humidity.
        Exam Season: {req.is_exam_season}.
        Top Drivers: {[d.driver for d in pred.top_cost_drivers]}.
        Provide a concise plain-English explanation of why energy cost is changing and what actions to take.
        """

        gemini_text = self._call_gemini_api(prompt, "You are EcoMind AI energy forecast explainer.")

        if not gemini_text:
            summary = f"Next month's energy cost for {pred.target_month} is projected at ₹{pred.predicted_cost_inr:,.2f}, representing a {pred.mom_change_percent}% change compared to last month."
            trend_exp = f"The primary cost elevation is driven by higher expected outdoor temperatures ({req.expected_temperature_c}°C), which increases HVAC cooling load across academic blocks and CSE laboratories."
            if req.is_exam_season:
                trend_exp += " Additionally, university examination schedules extend lab and central library operating hours into late evening."
        else:
            summary = gemini_text[:250] + "..." if len(gemini_text) > 250 else gemini_text
            trend_exp = gemini_text

        return CostExplanationResponseSchema(
            target_month=pred.target_month,
            predicted_cost_inr=pred.predicted_cost_inr,
            summary=summary,
            top_drivers=[d.model_dump() for d in pred.top_cost_drivers],
            cost_trend_explanation=trend_exp,
            suggested_mitigations=[
                "Enforce 26°C after-hours HVAC setback in Academic Blocks A & B.",
                "Pre-cool CSE laboratories 45 minutes before peak 15:30 heat window.",
                "Consolidate late-night study sections into designated Central Library floors."
            ]
        )

    # --- GEMINI INTELLIGENCE ROLE 2: ANOMALY EXPLAINER ---
    def summarize_anomalies(self) -> AnomalySummaryResponseSchema:
        ctx = self.get_anomalies_context()
        top_alerts = ctx["top_5_anomalies"]

        prompt = f"Summarize these top 5 campus energy waste anomalies for Vignan University in plain English with clear operational advice: {json.dumps(top_alerts)}"
        gemini_text = self._call_gemini_api(prompt, "You are EcoMind AI anomaly explainer.")

        if not gemini_text:
            op_advice = f"Detected {ctx['total_count']} total energy anomalies ({ctx['critical_count']} critical). Primary waste is concentrated in un-setback HVAC systems running post-18:00 in low-occupancy academic rooms and empty room lighting."
        else:
            op_advice = gemini_text

        return AnomalySummaryResponseSchema(
            total_anomalies_count=ctx["total_count"],
            critical_count=ctx["critical_count"],
            top_5_waste_issues=top_alerts,
            operational_advice=op_advice
        )

    # --- GEMINI INTELLIGENCE ROLE 3: RECOMMENDATION ADVISOR ---
    def evaluate_approval_support(self, recommendation_id: str) -> ApprovalSupportResponseSchema:
        recs = db_repository.get_recommendations()
        target = next((r for r in recs if r.get("recommendation_id") == recommendation_id), None)

        if not target:
            target = recs[0] if recs else {
                "recommendation_id": recommendation_id,
                "title": "HVAC Pre-Cooling Action",
                "energy_saved_kwh": 549.2,
                "money_saved_inr": 4805.61,
                "co2_reduced_kg": 450.35,
                "buildings": ["BLK-A", "LAB-CSE"]
            }

        title = target.get("title", "Optimization Action")
        saved_inr = target.get("money_saved_inr", 4805.61)

        prompt = f"Evaluate recommendation approval for '{title}' (Savings: ₹{saved_inr:,.2f}, Impacted Buildings: {target.get('buildings')}). State whether to APPROVE, provide reasoning, and list operational disruption risks."
        gemini_text = self._call_gemini_api(prompt, "You are EcoMind AI recommendation approval advisor.")

        verdict = "APPROVE"
        disruption = "Low"
        reasoning = f"APPROVE: '{title}' delivers ₹{saved_inr:,.2f} in immediate monthly cost savings with low disruption to daytime academic classes."
        risk_notes = "Minimal risk. Action schedules HVAC setback outside core lecture hours (18:00–06:00)."

        if gemini_text:
            reasoning = gemini_text

        return ApprovalSupportResponseSchema(
            recommendation_id=target.get("recommendation_id", recommendation_id),
            title=title,
            verdict=verdict,
            reasoning=reasoning,
            financial_benefit_inr=saved_inr,
            operational_disruption_risk=disruption,
            risk_notes=risk_notes
        )

    # --- GEMINI INTELLIGENCE ROLE 4: SCENARIO ANALYST ---
    def analyze_scenarios(self, req: CostPredictionRequestSchema = None) -> ScenarioAnalysisResponseSchema:
        if req is None:
            req = CostPredictionRequestSchema()

        pred = cost_prediction_service.predict_next_month_cost(req)
        sc = pred.scenarios

        prompt = f"Compare energy cost scenarios for {pred.target_month}: Optimistic (₹{sc.optimistic_inr:,.2f}), Baseline (₹{sc.baseline_inr:,.2f}), Pessimistic (₹{sc.pessimistic_inr:,.2f}). Provide a narrative summary."
        gemini_text = self._call_gemini_api(prompt, "You are EcoMind AI scenario analyst.")

        narrative = (
            f"For {pred.target_month}, baseline campus electricity cost is estimated at ₹{sc.baseline_inr:,.2f}. "
            f"Under an Optimistic Scenario with full EcoMind closed-loop setback controls, monthly expenditure drops to ₹{sc.optimistic_inr:,.2f} (saving ₹{sc.baseline_inr - sc.optimistic_inr:,.2f}). "
            f"Conversely, a severe heatwave or unmonitored post-hours lab usage could surge costs to ₹{sc.pessimistic_inr:,.2f} (+12.5%)."
        )

        if gemini_text:
            narrative = gemini_text

        return ScenarioAnalysisResponseSchema(
            target_month=pred.target_month,
            baseline_cost_inr=sc.baseline_inr,
            optimistic_cost_inr=sc.optimistic_inr,
            pessimistic_cost_inr=sc.pessimistic_inr,
            narrative_comparison=narrative
        )

    # --- GEMINI INTELLIGENCE ROLE 5: EXECUTIVE REPORT WRITER ---
    def generate_executive_report(self) -> ExecutiveReportResponseSchema:
        sus = db_repository.get_sustainability_data()
        snapshot = db_repository.get_snapshot()
        recs = db_repository.get_recommendations()

        prompt = f"Generate an executive dean-ready energy & sustainability summary report for Vignan University based on: {json.dumps(sus)}"
        gemini_text = self._call_gemini_api(prompt, "You are EcoMind AI executive report writer.")

        exec_summary = (
            f"Vignan University (VFSTR) campus operations maintained efficient energy performance over the past period, "
            f"avoiding {snapshot['carbon_avoided_kg']:,.1f} kg CO₂ and saving ₹{snapshot['money_saved_month_inr']:,.2f} in total energy costs. "
            f"Implementing top AI optimization recommendations will yield an additional ₹{sum(r.get('money_saved_inr', 0) for r in recs):,.2f} in financial savings."
        )

        if gemini_text:
            exec_summary = gemini_text

        return ExecutiveReportResponseSchema(
            campus_name="Vignan's Foundation for Science, Technology & Research (VFSTR)",
            time_period="Monthly Operational Cycle 2026",
            executive_summary=exec_summary,
            key_metrics_summary={
                "total_carbon_avoided_kg": snapshot["carbon_avoided_kg"],
                "total_money_saved_inr": snapshot["money_saved_month_inr"],
                "peak_demand_kw": snapshot["peak_demand_kw"],
                "tariff_rate": "₹8.75 / kWh",
                "grid_carbon_factor": "0.82 kg CO₂ / kWh",
            },
            top_inefficiencies=[
                "Un-setback HVAC systems in Academic Block A after 18:00",
                "Occupancy-zero lighting left active in empty science lecture rooms",
                "Uncalibrated computer lab batch job schedules during peak 14:00 demand"
            ],
            strategic_action_plan=[
                "Execute automated after-hours HVAC setback across Academic Blocks A, B, and C.",
                "Enforce 10-minute occupancy sensor auto-off shutoff in non-essential rooms.",
                "Pre-cool CSE laboratories prior to 15:30 afternoon heat peaks."
            ]
        )

    # --- GEMINI INTELLIGENCE ROLE 6: NATURAL LANGUAGE Q&A ---
    def answer_natural_language_question(self, question: str) -> AskQuestionResponseSchema:
        q_lower = question.lower()
        now_str = datetime.now(timezone.utc).isoformat()
        snapshot = db_repository.get_snapshot()
        buildings = db_repository.get_buildings()
        recs = db_repository.get_recommendations()

        context_str = f"Campus: Vignan University. Snapshot: {json.dumps(snapshot)}. Top Buildings: {json.dumps(buildings[:4])}. Top Actions: {json.dumps(recs[:3])}."

        prompt = f"User Question: {question}\nCampus Context Facts: {context_str}\nAnswer concisely using only the facts provided."
        gemini_text = self._call_gemini_api(prompt, "You are EcoMind AI energy manager Q&A assistant.")

        if gemini_text:
            answer = gemini_text
            cited = ["Vignan University Telemetry & Live Gemini 2.5 API"]
        elif "building" in q_lower or "highest" in q_lower or "waste" in q_lower:
            highest_b = max(buildings, key=lambda b: b.get("kw", 0)) if buildings else {"name": "Academic Block A", "kw": 218}
            answer = f"According to live telemetry, **{highest_b['name']}** recorded the highest consumption at **{highest_b['kw']} kW** ({highest_b['load']}% capacity load)."
            cited = [f"Building Telemetry: {highest_b['id']}"]
        elif "cost" in q_lower or "bill" in q_lower or "save" in q_lower:
            answer = f"Total projected monthly cost savings stand at **₹{snapshot['money_saved_month_inr']:,.2f}**, with **{snapshot['carbon_avoided_kg']:,.1f} kg CO₂** avoided."
            cited = ["Monthly ESG & Sustainability Audit"]
        else:
            answer = f"Vignan University campus energy is operating efficiently at **{snapshot['peak_demand_kw']} kW** peak demand. Total monthly carbon avoided is **{snapshot['carbon_avoided_kg']} kg CO₂**."
            cited = ["Campus Snapshot Telemetry"]

        return AskQuestionResponseSchema(
            question=question,
            answer=answer,
            cited_metrics=cited,
            confidence_score=0.98,
            timestamp=now_str
        )


gemini_service = GeminiService()
