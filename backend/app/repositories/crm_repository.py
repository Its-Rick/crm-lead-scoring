from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import Account, AccountOpportunity, AccountTicket, ActivityRel, Call


class CRMRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_active_accounts(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        industry: str | None = None,
        account_status: str | None = None,
    ) -> tuple[list[Account], int]:
        stmt = self._account_filters(select(Account), industry, account_status)
        count_stmt = self._account_filters(select(func.count(Account.id)), industry, account_status)
        stmt = stmt.order_by(Account.updated_at.desc().nullslast(), Account.created_at.desc().nullslast()).limit(limit).offset(offset)
        accounts = list((await self.session.scalars(stmt)).all())
        total = int(await self.session.scalar(count_stmt) or 0)
        return accounts, total

    async def get_active_account(self, account_id: str) -> Account | None:
        stmt = select(Account).where(Account.id == account_id, Account.deleted_at.is_(None))
        return await self.session.scalar(stmt)

    async def get_account_calls(self, account_ids: list[str]) -> dict[str, list[Call]]:
        if not account_ids:
            return {}
        stmt = (
            select(ActivityRel.parent_id, Call)
            .join(Call, Call.id == ActivityRel.activity_id)
            .where(
                ActivityRel.parent_id.in_(account_ids),
                ActivityRel.deleted_at.is_(None),
                Call.deleted_at.is_(None),
                func.lower(ActivityRel.parent_module).in_(("accounts", "account")),
                func.lower(ActivityRel.activity_module).in_(("calls", "call")),
            )
            .order_by(Call.start_date.desc().nullslast(), Call.created_at.desc().nullslast())
        )
        rows = (await self.session.execute(stmt)).all()
        by_account: dict[str, list[Call]] = {account_id: [] for account_id in account_ids}
        for account_id, call in rows:
            by_account.setdefault(account_id, []).append(call)
        return by_account

    async def count_opportunities(self, account_ids: list[str]) -> dict[str, int]:
        return await self._count_by_account(AccountOpportunity, account_ids)

    async def count_tickets(self, account_ids: list[str]) -> dict[str, int]:
        return await self._count_by_account(AccountTicket, account_ids)

    async def count_recent_activities(self, account_ids: list[str], since) -> dict[str, int]:
        if not account_ids:
            return {}
        stmt = (
            select(ActivityRel.parent_id, func.count(ActivityRel.id))
            .where(
                ActivityRel.parent_id.in_(account_ids),
                ActivityRel.deleted_at.is_(None),
                func.lower(ActivityRel.parent_module).in_(("accounts", "account")),
                func.coalesce(ActivityRel.updated_at, ActivityRel.created_at) >= since,
            )
            .group_by(ActivityRel.parent_id)
        )
        return {account_id: int(count) for account_id, count in (await self.session.execute(stmt)).all()}

    async def list_all_calls(self) -> list[Call]:
        stmt = select(Call).where(Call.deleted_at.is_(None)).order_by(Call.start_date.asc().nullslast())
        return list((await self.session.scalars(stmt)).all())

    async def ping(self) -> bool:
        await self.session.execute(select(1))
        return True

    def _account_filters(self, stmt: Select, industry: str | None, account_status: str | None) -> Select:
        stmt = stmt.where(Account.deleted_at.is_(None))
        if industry:
            stmt = stmt.where(Account.industry == industry)
        if account_status:
            stmt = stmt.where(Account.account_status == account_status)
        return stmt

    async def _count_by_account(self, model, account_ids: list[str]) -> dict[str, int]:
        if not account_ids:
            return {}
        stmt = (
            select(model.account_id, func.count(model.id))
            .where(model.account_id.in_(account_ids), model.deleted_at.is_(None))
            .group_by(model.account_id)
        )
        return {account_id: int(count) for account_id, count in (await self.session.execute(stmt)).all()}

