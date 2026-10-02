"""
Pydantic v2 schemas for FakeNews Killer.
Defines every request, response, and agent-output model used by the API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid


# ───────────────────────── Request Models ─────────────────────────

class AnalyzeRequest(BaseModel):
    """Payload accepted by POST /analyze."""
    text: str = Field(..., min_length=1, description="Raw text / claim to fact-check")


# ───────────────────────── Agent Output Models ─────────────────────────

class Claim(BaseModel):
    claim_id: Optional[str] = None
    original_text: Optional[str] = None
    normalized_claim: Optional[str] = None
    claim_type: Optional[str] = None
    entities: Optional[List[str]] = []
    time_reference: Optional[str] = None
    verifiable: Optional[bool] = None

class ReaderOutput(BaseModel):
    """Structured output returned by the Reader agent."""
    content_type: Optional[str] = None
    language_detected: Optional[str] = None
    red_flag_patterns: Optional[List[str]] = []
    initial_suspicion_score: Optional[int] = None
    claims: Optional[List[Claim]] = []
    total_claims: Optional[int] = None


class BestSource(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    headline: Optional[str] = None

class AnalyzedClaim(BaseModel):
    claim_id: Optional[str] = None
    normalized_claim: Optional[str] = None
    truth_score: Optional[int] = None
    verdict: Optional[str] = None
    verdict_category: Optional[str] = None
    reasoning: Optional[str] = None
    sources_checked: Optional[List[str]] = []
    best_source: Optional[BestSource] = None
    search_queries_used: Optional[List[str]] = []

class AnalystOutput(BaseModel):
    """Structured output returned by the Analyst agent."""
    overall_verdict: Optional[str] = None
    overall_confidence: Optional[int] = None
    analysis_summary: Optional[str] = None
    claims_analysis: Optional[List[AnalyzedClaim]] = []
    spread_risk: Optional[str] = None
    spread_risk_reason: Optional[str] = None


class RecommendedAction(BaseModel):
    action_id: Optional[str] = None
    action_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    urgency: Optional[str] = None
    simulated_output_type: Optional[str] = None
    priority_rank: Optional[int] = None

class StrategistOutput(BaseModel):
    """Structured output returned by the Strategist agent."""
    harm_level: Optional[str] = None
    affected_audience: Optional[str] = None
    recommended_actions: Optional[List[RecommendedAction]] = []
    do_not_share_warning: Optional[str] = None
    context_note: Optional[str] = None


class VerdictCard(BaseModel):
    claim_summary: Optional[str] = None
    overall_verdict: Optional[str] = None
    verdict_color: Optional[str] = None
    confidence_percentage: Optional[int] = None
    key_finding: Optional[str] = None
    sources: Optional[List[str]] = []
    fact_checked_by: Optional[str] = None
    check_timestamp: Optional[str] = None
    share_text: Optional[str] = None
    urdu_verdict: Optional[str] = None
    roman_urdu_warning: Optional[str] = None

class TrackerEntryData(BaseModel):
    entry_id: Optional[str] = None
    claim_text: Optional[str] = None
    verdict: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    spread_risk: Optional[str] = None
    first_detected: Optional[str] = None
    sources_cited: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    status: Optional[str] = None

class PlatformReport(BaseModel):
    report_type: Optional[str] = None
    platform: Optional[str] = None
    content_description: Optional[str] = None
    harm_category: Optional[str] = None
    evidence_summary: Optional[str] = None
    recommended_action: Optional[str] = None
    reporter: Optional[str] = None
    report_body: Optional[str] = None

class ExecutionLog(BaseModel):
    step: Optional[int] = None
    action: Optional[str] = None
    status: Optional[str] = None
    timestamp: Optional[str] = None
    entry_id: Optional[str] = None
    platform: Optional[str] = None

class ExecutorOutput(BaseModel):
    """Structured output returned by the Executor agent."""
    execution_timestamp: Optional[str] = None
    actions_executed: Optional[int] = None
    verdict_card: Optional[VerdictCard] = None
    tracker_entry: Optional[TrackerEntryData] = None
    platform_report: Optional[PlatformReport] = None
    execution_log: Optional[List[ExecutionLog]] = []


# ───────────────────────── Response Models ─────────────────────────

class AnalyzeResponse(BaseModel):
    """Full pipeline result returned by POST /analyze."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "completed"
    reader: ReaderOutput
    analyst: AnalystOutput
    strategist: StrategistOutput
    executor: ExecutorOutput
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class TrackerEntry(BaseModel):
    """A single misinformation tracker row (maps 1-to-1 with a Firestore document)."""
    id: Optional[str] = None
    claim_text: str
    verdict: str
    category: str
    language: str
    spread_risk: str
    first_detected: Optional[str] = None
    sources_cited: list[str] = []
    tags: list[str] = []
    status: str = "active"
    confidence_score: int = 0
    analyst_data: Optional[dict] = None
    executor_data: Optional[dict] = None


class HealthResponse(BaseModel):
    """Returned by GET /health."""
    status: str = "ok"
