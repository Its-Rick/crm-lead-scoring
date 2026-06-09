from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models.crm import Account, Call
from app.repositories.crm_repository import CRMRepository
from app.schemas.analytics import AccountAnalytics, AccountMetrics, PaginatedAccountAnalytics, RecentCall
from app.services.followup_service import FollowUpService
from app.services.lead_scoring_service import LeadScoringService
from app.utils.json_parsing import normalize_sentiment
from app.utils.scoring import is_failed_call, is_successful_call


class PipelineService:
    def __init__(
        self,
        repository: CRMRepository,
        scorer: LeadScoringService | None = None,
        followups: FollowUpService | None = None,
    ):
        self.repository = repository
        self.scorer = scorer or LeadScoringService()
        self.followups = followups or FollowUpService()

    async def list_account_analytics(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        industry: str | None = None,
        account_status: str | None = None,
    ) -> PaginatedAccountAnalytics:
        accounts, total = await self.repository.list_active_accounts(
            limit=limit,
            offset=offset,
            industry=industry,
            account_status=account_status,
        )
        items = await self._build_account_analytics(accounts)
        return PaginatedAccountAnalytics(items=items, total=total, limit=limit, offset=offset)

    async def get_account_analytics(self, account_id: str) -> AccountAnalytics | None:
        account = await self.repository.get_active_account(account_id)
        if not account:
            return None
        return (await self._build_account_analytics([account]))[0]

    async def list_lead_scores(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        category: str | None = None,
        industry: str | None = None,
        account_status: str | None = None,
        min_score: int | None = None,
    ) -> PaginatedAccountAnalytics:
        analytics = await self.list_account_analytics(
            limit=limit,
            offset=offset,
            industry=industry,
            account_status=account_status,
        )
        filtered = [
            item
            for item in analytics.items
            if (category is None or item.lead_score.category.lower() == category.lower())
            and (min_score is None or item.lead_score.score >= min_score)
        ]
        return PaginatedAccountAnalytics(items=filtered, total=len(filtered), limit=limit, offset=offset)

    async def list_followups(self, *, limit: int = 100, offset: int = 0) -> PaginatedAccountAnalytics:
        analytics = await self.list_account_analytics(limit=limit, offset=offset)
        priority_rank = {"High": 0, "Medium": 1, "Low": 2}
        analytics.items.sort(key=lambda item: (priority_rank.get(item.follow_up.priority, 9), -item.lead_score.score))
        return analytics

    async def refresh(self) -> None:
        return None

    async def _build_account_analytics(self, accounts: list[Account]) -> list[AccountAnalytics]:
        account_ids = [account.id for account in accounts]
        calls_by_account = await self.repository.get_account_calls(account_ids)
        opportunities = await self.repository.count_opportunities(account_ids)
        tickets = await self.repository.count_tickets(account_ids)
        recent_since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=14)
        recent_activities = await self.repository.count_recent_activities(account_ids, recent_since)

        items: list[AccountAnalytics] = []
        for account in accounts:
            metrics = self._metrics_for_account(
                account=account,
                calls=calls_by_account.get(account.id, []),
                opportunities_count=opportunities.get(account.id, 0),
                ticket_count=tickets.get(account.id, 0),
                recent_activities_count=recent_activities.get(account.id, 0),
            )
            lead_score = self.scorer.score(metrics)
            follow_up = self.followups.recommend(metrics, lead_score.category)
            items.append(
                AccountAnalytics(
                    account_id=account.id,
                    account_name=account.name,
                    industry=account.industry,
                    customer_type=account.customer_type,
                    account_status=account.account_status,
                    rating=account.rating,
                    metrics=metrics,
                    lead_score=lead_score,
                    follow_up=follow_up,
                    recent_calls=[self._recent_call(call) for call in calls_by_account.get(account.id, [])[:5]],
                )
            )
        return items

    def _metrics_for_account(
        self,
        *,
        account: Account,
        calls: list[Call],
        opportunities_count: int,
        ticket_count: int,
        recent_activities_count: int,
    ) -> AccountMetrics:
        durations = [self._duration_minutes(call) for call in calls if self._duration_minutes(call) > 0]
        sentiments = [normalize_sentiment(call.sentiment_analysis) for call in calls]
        ratings = [call.overall_call_rating for call in calls if call.overall_call_rating is not None]
        return AccountMetrics(
            total_calls=len(calls),
            average_call_duration=round(sum(durations) / len(durations), 2) if durations else 0.0,
            average_sentiment=round(sum(sentiments) / len(sentiments), 3) if sentiments else 0.0,
            opportunities_count=opportunities_count,
            ticket_count=ticket_count,
            recent_activities_count=recent_activities_count,
            average_call_rating=round(sum(ratings) / len(ratings), 2) if ratings else 0.0,
            failed_calls_count=sum(1 for call in calls if is_failed_call(call.call_status, call.call_outcome)),
            successful_calls_count=sum(1 for call in calls if is_successful_call(call.call_status, call.call_outcome)),
            untouched_since_days=account.untouched_since_days or 0,
        )

    def _recent_call(self, call: Call) -> RecentCall:
        return RecentCall(
            id=call.id,
            start_date=call.start_date,
            status=call.call_status,
            outcome=call.call_outcome,
            sentiment_score=normalize_sentiment(call.sentiment_analysis),
            duration_minutes=self._duration_minutes(call),
            rating=call.overall_call_rating or 0,
            next_step=call.next_step,
        )

    def _duration_minutes(self, call: Call) -> float:
        value = call.total_duration_minute
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, int | float):
            return float(value)
        if call.duration:
            return round(call.duration.hour * 60 + call.duration.minute + call.duration.second / 60, 2)
        return 0.0
