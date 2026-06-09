import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from app.api.deps import get_call_insights_service, get_pipeline_service
from app.main import app
from app.schemas.analytics import (
    AccountAnalytics,
    AccountMetrics,
    CallInsightsResponse,
    FollowUpRecommendation,
    LeadScore,
    PaginatedAccountAnalytics,
)


def sample_account() -> AccountAnalytics:
    metrics = AccountMetrics(
        total_calls=1,
        average_call_duration=6,
        average_sentiment=0.5,
        opportunities_count=1,
        ticket_count=0,
        recent_activities_count=1,
        average_call_rating=4,
        failed_calls_count=0,
        successful_calls_count=1,
        untouched_since_days=3,
    )
    return AccountAnalytics(
        account_id="account-1",
        account_name="Acme",
        metrics=metrics,
        lead_score=LeadScore(score=82, category="Hot", explanations=["High engagement"]),
        follow_up=FollowUpRecommendation(
            priority="Low",
            suggested_action="Call to move opportunity forward",
            recommended_time="within 7 days",
            reasons=["High conversion probability"],
        ),
    )


class FakePipelineService:
    async def list_account_analytics(self, **kwargs):
        return PaginatedAccountAnalytics(items=[sample_account()], total=1, limit=kwargs["limit"], offset=kwargs["offset"])

    async def get_account_analytics(self, account_id: str):
        return sample_account() if account_id == "account-1" else None

    async def list_lead_scores(self, **kwargs):
        return PaginatedAccountAnalytics(items=[sample_account()], total=1, limit=kwargs["limit"], offset=kwargs["offset"])

    async def list_followups(self, **kwargs):
        return PaginatedAccountAnalytics(items=[sample_account()], total=1, limit=kwargs["limit"], offset=kwargs["offset"])

    async def refresh(self):
        return None


class FakeCallInsightsService:
    async def get_insights(self):
        return CallInsightsResponse(
            total_calls=1,
            positive_calls=1,
            negative_calls=0,
            neutral_calls=0,
            average_successful_call_duration=6,
            best_performing_agents=[],
            failed_call_patterns=[],
            call_outcome_analytics={"Converted": 1},
            sentiment_trends=[],
            insights=["Calls above 5 minutes are associated with successful outcomes"],
        )


def test_analytics_routes_return_dashboard_json():
    app.dependency_overrides[get_pipeline_service] = lambda: FakePipelineService()
    app.dependency_overrides[get_call_insights_service] = lambda: FakeCallInsightsService()
    client = TestClient(app)

    assert client.get("/api/v1/analytics/accounts").status_code == 200
    assert client.get("/api/v1/analytics/accounts/account-1").json()["lead_score"]["category"] == "Hot"
    assert client.get("/api/v1/analytics/call-insights").json()["positive_calls"] == 1
    assert client.post("/api/v1/pipeline/refresh").json()["refreshed"] is True

    app.dependency_overrides.clear()

