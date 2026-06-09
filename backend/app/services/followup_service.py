from app.schemas.analytics import AccountMetrics, FollowUpRecommendation


class FollowUpService:
    def recommend(self, metrics: AccountMetrics, lead_category: str) -> FollowUpRecommendation:
        reasons: list[str] = []
        priority = "Low"
        suggested_action = "Monitor account activity"
        recommended_time = "within 7 days"

        high_risk = (
            metrics.untouched_since_days >= 30
            or metrics.average_sentiment < -0.25
            or metrics.ticket_count >= 3
            or metrics.failed_calls_count >= 2
            or (lead_category == "Hot" and metrics.recent_activities_count == 0)
        )

        if high_risk:
            priority = "High"
            recommended_time = "within 24 hours"
            suggested_action = "Call customer and confirm next step"
            if metrics.average_sentiment < -0.25:
                reasons.append("Customer sentiment indicates churn risk")
                suggested_action = "Escalate with a retention-focused call"
            if metrics.untouched_since_days >= 30:
                reasons.append(f"Account has been untouched for {metrics.untouched_since_days} days")
            if metrics.ticket_count >= 3:
                reasons.append("Multiple support tickets need proactive handling")
            if metrics.failed_calls_count >= 2:
                reasons.append("Recent failed call pattern needs recovery")
            if lead_category == "Hot" and metrics.recent_activities_count == 0:
                reasons.append("High-scoring lead has no recent activity")
        elif lead_category == "Warm" or metrics.untouched_since_days >= 14:
            priority = "Medium"
            recommended_time = "within 2-3 days"
            suggested_action = "Schedule follow-up and validate interest"
            reasons.append("Lead is warm or moderately inactive")
        else:
            reasons.append("Account has low immediate follow-up risk")

        if lead_category == "Hot" and priority != "High":
            suggested_action = "Call to move opportunity forward"
            reasons.append("High conversion probability")

        return FollowUpRecommendation(
            priority=priority,
            suggested_action=suggested_action,
            recommended_time=recommended_time,
            reasons=reasons,
        )

