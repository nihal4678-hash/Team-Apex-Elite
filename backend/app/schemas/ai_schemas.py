from typing import Optional, List
from pydantic import BaseModel, Field


class AskQuestionRequestSchema(BaseModel):
    question: str = Field(..., description="User natural language question about campus energy")
    context_filter: Optional[str] = Field(default=None, description="Optional domain filter: cost, forecast, anomaly, recommendation, sustainability, simulation")
    scenario_id: Optional[str] = Field(default=None, description="Optional scenario ID for simulation questions")


class AskQuestionResponseSchema(BaseModel):
    question: str
    answer: str
    intent: str = "general"
    explanation: Optional[str] = None
    supporting_metrics: List[str] = []
    cited_metrics: List[str] = []
    source_labels: List[str] = ["Actual data"]
    confidence_score: float = 0.95
    suggested_action: Optional[str] = None
    timestamp: str


class GeminiStatusSchema(BaseModel):
    configured: bool
    provider_reachable: bool
    selected_model: str
    last_error_category: str  # none, missing_api_key, invalid_api_key, quota_exceeded, network_failure, malformed_response


class CostExplanationResponseSchema(BaseModel):
    target_month: str
    predicted_cost_inr: float
    summary: str
    top_drivers: list[dict]
    cost_trend_explanation: str
    suggested_mitigations: list[str]


class AnomalySummaryResponseSchema(BaseModel):
    total_anomalies_count: int
    critical_count: int
    top_5_waste_issues: list[dict]
    operational_advice: str


class ApprovalSupportRequestSchema(BaseModel):
    recommendation_id: str


class ApprovalSupportResponseSchema(BaseModel):
    recommendation_id: str
    title: str
    verdict: str  # APPROVE / CAUTION / REJECT
    reasoning: str
    financial_benefit_inr: float
    operational_disruption_risk: str  # Low / Medium / High
    risk_notes: str


class ScenarioAnalysisResponseSchema(BaseModel):
    target_month: str
    baseline_cost_inr: float
    optimistic_cost_inr: float
    pessimistic_cost_inr: float
    narrative_comparison: str


class ExecutiveReportResponseSchema(BaseModel):
    campus_name: str
    time_period: str
    executive_summary: str
    key_metrics_summary: dict
    top_inefficiencies: list[str]
    strategic_action_plan: list[str]
