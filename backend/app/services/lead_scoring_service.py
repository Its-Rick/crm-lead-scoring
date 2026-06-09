from app.schemas.analytics import AccountMetrics, LeadScore
from app.utils.scoring import categorize_score, clamp_score


class LeadScoringService:
    def score(self, metrics: AccountMetrics) -> LeadScore:
        score = 35.0
        explanations: list[str] = []

        call_points = min(metrics.total_calls * 4, 20)
        score += call_points
        if metrics.total_calls >= 5:
            explanations.append("Lead has high engagement from repeated calls")
        elif metrics.total_calls == 0:
            explanations.append("Lead has no call engagement yet")

        if metrics.average_call_duration >= 5:
            score += 10
            explanations.append("Average call duration is above 5 minutes")
        elif 0 < metrics.average_call_duration < 2:
            score -= 5
            explanations.append("Calls are short and may need better discovery")

        if metrics.average_sentiment > 0.35:
            score += 15
            explanations.append("Customer sentiment is positive")
        elif metrics.average_sentiment < -0.25:
            score -= 15
            explanations.append("Customer sentiment is negative")

        if metrics.opportunities_count > 0:
            score += min(metrics.opportunities_count * 8, 20)
            explanations.append("Lead has linked opportunities")

        if metrics.ticket_count >= 3:
            score -= 10
            explanations.append("Multiple support tickets may indicate risk")
        elif metrics.ticket_count > 0:
            score -= 4
            explanations.append("Open support history should be considered")

        if metrics.untouched_since_days >= 30:
            score -= 20
            explanations.append(f"Customer inactive for {metrics.untouched_since_days} days")
        elif metrics.untouched_since_days >= 14:
            score -= 10
            explanations.append(f"Customer untouched for {metrics.untouched_since_days} days")
        elif metrics.untouched_since_days <= 7:
            score += 8
            explanations.append("Lead was touched recently")

        if metrics.recent_activities_count > 0:
            score += min(metrics.recent_activities_count * 3, 12)
            explanations.append("Recent CRM activity exists")

        if metrics.average_call_rating >= 4:
            score += 10
            explanations.append("Call ratings are strong")
        elif 0 < metrics.average_call_rating < 3:
            score -= 6
            explanations.append("Call ratings are below target")

        final_score = clamp_score(score)
        if not explanations:
            explanations.append("Lead score is based on available CRM engagement signals")
        return LeadScore(score=final_score, category=categorize_score(final_score), explanations=explanations)

