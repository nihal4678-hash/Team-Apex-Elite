from fastapi import APIRouter, HTTPException
from app.schemas.ai_schemas import (
    AnomalySummaryResponseSchema, ApprovalSupportRequestSchema,
    ApprovalSupportResponseSchema, AskQuestionRequestSchema,
    AskQuestionResponseSchema, CostExplanationResponseSchema,
    ExecutiveReportResponseSchema, ScenarioAnalysisResponseSchema
)
from app.schemas.cost_prediction import CostPredictionRequestSchema
from app.services.gemini_service import gemini_service

router = APIRouter(prefix="/ai", tags=["gemini_intelligence"])


# --- CONTEXT ENDPOINTS ---
@router.get("/context/forecast")
def get_forecast_context():
    return gemini_service.get_forecast_context()


@router.get("/context/anomalies")
def get_anomalies_context():
    return gemini_service.get_anomalies_context()


@router.get("/context/recommendations")
def get_recommendations_context():
    return gemini_service.get_recommendations_context()


@router.get("/context/sustainability")
def get_sustainability_context():
    return gemini_service.get_sustainability_context()


@router.get("/context/monthly-cost")
def get_monthly_cost_context():
    return gemini_service.get_monthly_cost_context()


# --- GEMINI INTELLIGENCE & REASONING ENDPOINTS ---
@router.get("/cost-explanation", response_model=CostExplanationResponseSchema)
def get_cost_explanation() -> CostExplanationResponseSchema:
    return gemini_service.explain_cost_forecast()


@router.post("/cost-explanation", response_model=CostExplanationResponseSchema)
def post_cost_explanation(payload: CostPredictionRequestSchema) -> CostExplanationResponseSchema:
    return gemini_service.explain_cost_forecast(payload)


@router.get("/anomaly-summary", response_model=AnomalySummaryResponseSchema)
def get_anomaly_summary() -> AnomalySummaryResponseSchema:
    return gemini_service.summarize_anomalies()


@router.post("/approval-support", response_model=ApprovalSupportResponseSchema)
def evaluate_approval_support(payload: ApprovalSupportRequestSchema) -> ApprovalSupportResponseSchema:
    return gemini_service.evaluate_approval_support(payload.recommendation_id)


@router.get("/scenario", response_model=ScenarioAnalysisResponseSchema)
def get_scenario_analysis() -> ScenarioAnalysisResponseSchema:
    return gemini_service.analyze_scenarios()


@router.post("/scenario", response_model=ScenarioAnalysisResponseSchema)
def post_scenario_analysis(payload: CostPredictionRequestSchema) -> ScenarioAnalysisResponseSchema:
    return gemini_service.analyze_scenarios(payload)


@router.get("/report", response_model=ExecutiveReportResponseSchema)
def get_executive_report() -> ExecutiveReportResponseSchema:
    return gemini_service.generate_executive_report()


@router.post("/ask", response_model=AskQuestionResponseSchema)
def ask_gemini(payload: AskQuestionRequestSchema) -> AskQuestionResponseSchema:
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question prompt cannot be empty.")
    return gemini_service.answer_natural_language_question(payload.question.strip())
