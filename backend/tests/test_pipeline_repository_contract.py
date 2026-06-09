from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from app.services.pipeline_service import PipelineService


def test_pipeline_metric_engineering_uses_call_signals():
    service = PipelineService(repository=SimpleNamespace())
    account = SimpleNamespace(untouched_since_days=12)
    calls = [
        SimpleNamespace(
            total_duration_minute=Decimal("6.5"),
            duration=None,
            sentiment_analysis={"score": 0.8},
            overall_call_rating=5,
            call_status="Completed",
            call_outcome="Converted",
        ),
        SimpleNamespace(
            total_duration_minute=Decimal("1.0"),
            duration=None,
            sentiment_analysis={"label": "negative"},
            overall_call_rating=2,
            call_status="No Answer",
            call_outcome="Not connected",
        ),
    ]

    metrics = service._metrics_for_account(
        account=account,
        calls=calls,
        opportunities_count=1,
        ticket_count=2,
        recent_activities_count=4,
    )

    assert metrics.total_calls == 2
    assert metrics.average_call_duration == 3.75
    assert metrics.average_sentiment == -0.1
    assert metrics.successful_calls_count == 1
    assert metrics.failed_calls_count == 1
    assert metrics.untouched_since_days == 12


def test_recent_call_shape_is_dashboard_ready():
    service = PipelineService(repository=SimpleNamespace())
    call = SimpleNamespace(
        id="call-1",
        start_date=datetime(2026, 5, 20),
        call_status="Completed",
        call_outcome="Interested",
        sentiment_analysis={"label": "positive"},
        total_duration_minute=Decimal("7.25"),
        duration=None,
        overall_call_rating=4,
        next_step="Send proposal",
    )

    recent = service._recent_call(call)

    assert recent.id == "call-1"
    assert recent.sentiment_score == 1.0
    assert recent.duration_minutes == 7.25

