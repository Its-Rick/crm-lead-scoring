from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LeadScore(BaseModel):
    score: int = Field(ge=0, le=100)
    category: str
    explanations: list[str]


class FollowUpRecommendation(BaseModel):
    priority: str
    suggested_action: str
    recommended_time: str
    reasons: list[str]


class AccountMetrics(BaseModel):
    total_calls: int
    average_call_duration: float
    average_sentiment: float
    opportunities_count: int
    ticket_count: int
    recent_activities_count: int
    average_call_rating: float
    failed_calls_count: int
    successful_calls_count: int
    untouched_since_days: int


class RecentCall(BaseModel):
    id: str
    start_date: datetime | None = None
    status: str | None = None
    outcome: str | None = None
    sentiment_score: float
    duration_minutes: float
    rating: int
    next_step: str | None = None


class AccountAnalytics(BaseModel):
    account_id: str
    account_name: str | None = None
    industry: str | None = None
    customer_type: str | None = None
    account_status: str | None = None
    rating: str | None = None
    metrics: AccountMetrics
    lead_score: LeadScore
    follow_up: FollowUpRecommendation
    recent_calls: list[RecentCall] = []


class PaginatedAccountAnalytics(BaseModel):
    items: list[AccountAnalytics]
    total: int
    limit: int
    offset: int


class AgentPerformance(BaseModel):
    agent_id: str
    total_calls: int
    average_rating: float
    success_rate: float


class CallInsightsResponse(BaseModel):
    total_calls: int
    positive_calls: int
    negative_calls: int
    neutral_calls: int
    average_successful_call_duration: float
    best_performing_agents: list[AgentPerformance]
    failed_call_patterns: list[dict[str, Any]]
    call_outcome_analytics: dict[str, int]
    sentiment_trends: list[dict[str, Any]]
    insights: list[str]


class RefreshResponse(BaseModel):
    refreshed: bool
    message: str


class HealthResponse(BaseModel):
    service: str
    database: str
    version: str

    model_config = ConfigDict(from_attributes=True)

