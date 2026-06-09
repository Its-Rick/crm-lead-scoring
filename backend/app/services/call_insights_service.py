from collections import Counter, defaultdict
from datetime import datetime

from app.models.crm import Call
from app.repositories.crm_repository import CRMRepository
from app.schemas.analytics import AgentPerformance, CallInsightsResponse
from app.utils.json_parsing import normalize_sentiment
from app.utils.scoring import is_failed_call, is_successful_call


class CallInsightsService:
    def __init__(self, repository: CRMRepository):
        self.repository = repository

    async def get_insights(self) -> CallInsightsResponse:
        calls = await self.repository.list_all_calls()
        sentiments = [normalize_sentiment(call.sentiment_analysis) for call in calls]
        successful = [call for call in calls if is_successful_call(call.call_status, call.call_outcome)]
        failed = [call for call in calls if is_failed_call(call.call_status, call.call_outcome)]

        return CallInsightsResponse(
            total_calls=len(calls),
            positive_calls=sum(1 for score in sentiments if score > 0.25),
            negative_calls=sum(1 for score in sentiments if score < -0.25),
            neutral_calls=sum(1 for score in sentiments if -0.25 <= score <= 0.25),
            average_successful_call_duration=self._average_duration(successful),
            best_performing_agents=self._best_agents(calls),
            failed_call_patterns=self._failed_patterns(failed),
            call_outcome_analytics=dict(Counter((call.call_outcome or call.call_status or "Unknown") for call in calls)),
            sentiment_trends=self._sentiment_trends(calls),
            insights=self._insight_text(calls, successful, failed, sentiments),
        )

    def _average_duration(self, calls: list[Call]) -> float:
        durations = [float(call.total_duration_minute or 0) for call in calls if call.total_duration_minute]
        return round(sum(durations) / len(durations), 2) if durations else 0.0

    def _best_agents(self, calls: list[Call]) -> list[AgentPerformance]:
        by_agent: dict[str, list[Call]] = defaultdict(list)
        for call in calls:
            by_agent[call.assigned_user_id or call.logged_by or "unassigned"].append(call)
        agents: list[AgentPerformance] = []
        for agent_id, agent_calls in by_agent.items():
            ratings = [call.overall_call_rating or 0 for call in agent_calls]
            successes = sum(1 for call in agent_calls if is_successful_call(call.call_status, call.call_outcome))
            agents.append(
                AgentPerformance(
                    agent_id=agent_id,
                    total_calls=len(agent_calls),
                    average_rating=round(sum(ratings) / len(ratings), 2) if ratings else 0.0,
                    success_rate=round(successes / len(agent_calls), 3) if agent_calls else 0.0,
                )
            )
        return sorted(agents, key=lambda item: (item.success_rate, item.average_rating, item.total_calls), reverse=True)[:5]

    def _failed_patterns(self, calls: list[Call]) -> list[dict]:
        patterns = Counter((call.call_outcome or call.call_status or "Unknown") for call in calls)
        return [{"pattern": pattern, "count": count} for pattern, count in patterns.most_common(5)]

    def _sentiment_trends(self, calls: list[Call]) -> list[dict]:
        buckets: dict[str, list[float]] = defaultdict(list)
        for call in calls:
            dt: datetime | None = call.start_date or call.created_at
            bucket = dt.strftime("%Y-%m") if dt else "unknown"
            buckets[bucket].append(normalize_sentiment(call.sentiment_analysis))
        return [
            {"period": bucket, "average_sentiment": round(sum(values) / len(values), 3), "calls": len(values)}
            for bucket, values in sorted(buckets.items())
        ]

    def _insight_text(self, calls: list[Call], successful: list[Call], failed: list[Call], sentiments: list[float]) -> list[str]:
        insights: list[str] = []
        if self._average_duration(successful) >= 5:
            insights.append("Calls above 5 minutes are associated with successful outcomes")
        if failed and len(failed) / max(len(calls), 1) >= 0.3:
            insights.append("Failed call patterns are high enough to prioritize recovery workflows")
        if sentiments and sum(1 for score in sentiments if score < -0.25) / len(sentiments) >= 0.25:
            insights.append("Negative sentiment increases follow-up priority")
        if not insights:
            insights.append("Call performance is stable based on available CRM activity")
        return insights

