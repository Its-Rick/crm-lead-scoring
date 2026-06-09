from app.schemas.analytics import AccountMetrics
from app.services.followup_service import FollowUpService
from app.services.lead_scoring_service import LeadScoringService
from app.utils.json_parsing import normalize_sentiment
from app.utils.scoring import categorize_score


def test_sentiment_normalization_accepts_labels_and_scores():
    assert normalize_sentiment({"label": "positive"}) == 1.0
    assert normalize_sentiment({"score": 75}) == 0.75
    assert normalize_sentiment({"sentiment": "negative"}) == -1.0
    assert normalize_sentiment(None) == 0.0


def test_score_category_thresholds():
    assert categorize_score(75) == "Hot"
    assert categorize_score(45) == "Warm"
    assert categorize_score(44) == "Cold"


def test_hot_lead_score_has_explanations():
    metrics = AccountMetrics(
        total_calls=7,
        average_call_duration=8,
        average_sentiment=0.7,
        opportunities_count=2,
        ticket_count=0,
        recent_activities_count=3,
        average_call_rating=4.5,
        failed_calls_count=0,
        successful_calls_count=5,
        untouched_since_days=2,
    )

    lead_score = LeadScoringService().score(metrics)

    assert lead_score.category == "Hot"
    assert lead_score.score >= 75
    assert lead_score.explanations


def test_followup_high_priority_for_negative_inactive_account():
    metrics = AccountMetrics(
        total_calls=2,
        average_call_duration=2,
        average_sentiment=-0.7,
        opportunities_count=0,
        ticket_count=3,
        recent_activities_count=0,
        average_call_rating=2,
        failed_calls_count=2,
        successful_calls_count=0,
        untouched_since_days=40,
    )

    recommendation = FollowUpService().recommend(metrics, "Cold")

    assert recommendation.priority == "High"
    assert recommendation.recommended_time == "within 24 hours"
    assert recommendation.reasons

