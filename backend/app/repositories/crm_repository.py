from types import SimpleNamespace
from typing import Any

from sqlalchemy import bindparam, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


class CRMRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._column_cache: dict[str, set[str]] = {}
        self._table_cache: set[str] | None = None

    async def list_active_accounts(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        industry: str | None = None,
        account_status: str | None = None,
    ) -> tuple[list[Any], int]:
        columns = await self._table_columns("accounts")
        select_columns = [
            "id",
            "name",
            "assigned_user_id",
            "customer_type",
            "account_status",
            "industry",
            "rating",
            "untouched_since_days",
            "latest_comment",
            "created_at",
            "updated_at",
            "deleted_at",
        ]
        where_parts = self._active_where("a", columns)
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        if industry and "industry" in columns:
            where_parts.append(f"a.{self._quote('industry')} = :industry")
            params["industry"] = industry
        if account_status and "account_status" in columns:
            where_parts.append(f"a.{self._quote('account_status')} = :account_status")
            params["account_status"] = account_status

        order_parts = self._order_parts("a", columns, [("updated_at", "DESC"), ("created_at", "DESC")])
        sql = f"""
            SELECT {self._select_list("a", select_columns, columns)}
            FROM {self._quote("accounts")} a
            WHERE {" AND ".join(where_parts)}
            ORDER BY {", ".join(order_parts)}
            LIMIT :limit OFFSET :offset
        """
        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM {self._quote("accounts")} a
            WHERE {" AND ".join(where_parts)}
        """
        rows = (await self.session.execute(text(sql), params)).mappings().all()
        total = int((await self.session.execute(text(count_sql), params)).scalar() or 0)
        return [self._namespace(row) for row in rows], total

    async def get_active_account(self, account_id: str) -> Any | None:
        columns = await self._table_columns("accounts")
        select_columns = [
            "id",
            "name",
            "assigned_user_id",
            "customer_type",
            "account_status",
            "industry",
            "rating",
            "untouched_since_days",
            "latest_comment",
            "created_at",
            "updated_at",
            "deleted_at",
        ]
        where_parts = self._active_where("a", columns)
        where_parts.append(f"a.{self._quote('id')} = :account_id")
        sql = f"""
            SELECT {self._select_list("a", select_columns, columns)}
            FROM {self._quote("accounts")} a
            WHERE {" AND ".join(where_parts)}
            LIMIT 1
        """
        row = (await self.session.execute(text(sql), {"account_id": account_id})).mappings().first()
        return self._namespace(row) if row else None

    async def get_account_calls(self, account_ids: list[str]) -> dict[str, list[Any]]:
        if not account_ids:
            return {}

        if await self._table_exists("activities_rel"):
            return await self._get_account_calls_from_activities(account_ids)
        return await self._get_account_calls_from_direct_columns(account_ids)

    async def _get_account_calls_from_activities(self, account_ids: list[str]) -> dict[str, list[Any]]:
        call_columns = await self._table_columns("calls")
        rel_columns = await self._table_columns("activities_rel")
        if not call_columns or not rel_columns or "parent_id" not in rel_columns or "activity_id" not in rel_columns:
            return {account_id: [] for account_id in account_ids}

        call_select_columns = self._call_select_columns()
        where_parts = [
            f"ar.{self._quote('parent_id')} IN :account_ids",
            f"c.{self._quote('id')} = ar.{self._quote('activity_id')}",
        ]
        where_parts.extend(self._active_where("ar", rel_columns))
        where_parts.extend(self._active_where("c", call_columns))
        if "parent_module" in rel_columns:
            where_parts.append(f"LOWER(ar.{self._quote('parent_module')}) IN ('accounts', 'account')")
        if "activity_module" in rel_columns:
            where_parts.append(f"LOWER(ar.{self._quote('activity_module')}) IN ('calls', 'call')")

        order_parts = self._order_parts("c", call_columns, [("start_date", "DESC"), ("created_at", "DESC")])
        sql = f"""
            SELECT
                ar.{self._quote('parent_id')} AS account_id,
                {self._select_list("c", call_select_columns, call_columns)}
            FROM {self._quote("activities_rel")} ar
            JOIN {self._quote("calls")} c ON c.{self._quote('id')} = ar.{self._quote('activity_id')}
            WHERE {" AND ".join(where_parts)}
            ORDER BY {", ".join(order_parts)}
        """
        stmt = text(sql).bindparams(bindparam("account_ids", expanding=True))
        rows = (await self.session.execute(stmt, {"account_ids": account_ids})).mappings().all()
        by_account: dict[str, list[Any]] = {account_id: [] for account_id in account_ids}
        for row in rows:
            data = dict(row)
            account_id = data.pop("account_id")
            by_account.setdefault(account_id, []).append(SimpleNamespace(**data))
        return by_account

    async def _get_account_calls_from_direct_columns(self, account_ids: list[str]) -> dict[str, list[Any]]:
        call_columns = await self._table_columns("calls")
        by_account: dict[str, list[Any]] = {account_id: [] for account_id in account_ids}
        if not call_columns:
            return by_account

        account_column = self._first_existing(call_columns, ["account_id", "parent_id", "module_id"])
        if account_column is None:
            return by_account

        where_parts = [f"c.{self._quote(account_column)} IN :account_ids"]
        where_parts.extend(self._active_where("c", call_columns))
        if account_column == "parent_id" and "parent_module" in call_columns:
            where_parts.append(f"LOWER(c.{self._quote('parent_module')}) IN ('accounts', 'account')")

        order_parts = self._order_parts("c", call_columns, [("start_date", "DESC"), ("created_at", "DESC")])
        sql = f"""
            SELECT
                c.{self._quote(account_column)} AS account_id,
                {self._select_list("c", self._call_select_columns(), call_columns)}
            FROM {self._quote("calls")} c
            WHERE {" AND ".join(where_parts)}
            ORDER BY {", ".join(order_parts)}
        """
        stmt = text(sql).bindparams(bindparam("account_ids", expanding=True))
        rows = (await self.session.execute(stmt, {"account_ids": account_ids})).mappings().all()
        for row in rows:
            data = dict(row)
            account_id = data.pop("account_id")
            by_account.setdefault(account_id, []).append(SimpleNamespace(**data))
        return by_account

    async def count_opportunities(self, account_ids: list[str]) -> dict[str, int]:
        return await self._count_by_account("account_opportunity", account_ids)

    async def count_tickets(self, account_ids: list[str]) -> dict[str, int]:
        if await self._table_exists("account_ticket"):
            return await self._count_by_account("account_ticket", account_ids)
        if await self._table_exists("tickets"):
            return await self._count_by_account("tickets", account_ids)
        return {}

    async def count_recent_activities(self, account_ids: list[str], since) -> dict[str, int]:
        if not account_ids:
            return {}
        if not await self._table_exists("activities_rel"):
            return await self._count_recent_account_activity(account_ids, since)

        columns = await self._table_columns("activities_rel")
        if "parent_id" not in columns:
            return {}

        activity_date = self._activity_date_expression("ar", columns)
        if activity_date is None:
            return {}

        where_parts = [f"ar.{self._quote('parent_id')} IN :account_ids", f"{activity_date} >= :since"]
        where_parts.extend(self._active_where("ar", columns))
        if "parent_module" in columns:
            where_parts.append(f"LOWER(ar.{self._quote('parent_module')}) IN ('accounts', 'account')")

        sql = f"""
            SELECT ar.{self._quote('parent_id')} AS account_id, COUNT(*) AS total
            FROM {self._quote("activities_rel")} ar
            WHERE {" AND ".join(where_parts)}
            GROUP BY ar.{self._quote('parent_id')}
        """
        stmt = text(sql).bindparams(bindparam("account_ids", expanding=True))
        rows = (await self.session.execute(stmt, {"account_ids": account_ids, "since": since})).all()
        return {account_id: int(total) for account_id, total in rows}

    async def _count_recent_account_activity(self, account_ids: list[str], since) -> dict[str, int]:
        totals: dict[str, int] = {}
        for table_name in ("account_opportunity", "account_lead", "account_contact"):
            counts = await self._count_recent_account_relation(table_name, account_ids, since)
            for account_id, count in counts.items():
                totals[account_id] = totals.get(account_id, 0) + count

        call_counts = await self._count_recent_direct_call_activity(account_ids, since)
        for account_id, count in call_counts.items():
            totals[account_id] = totals.get(account_id, 0) + count
        return totals

    async def _count_recent_account_relation(self, table_name: str, account_ids: list[str], since) -> dict[str, int]:
        if not await self._table_exists(table_name):
            return {}
        columns = await self._table_columns(table_name)
        if "account_id" not in columns:
            return {}
        activity_date = self._activity_date_expression("t", columns)
        if activity_date is None:
            return {}
        where_parts = [f"t.{self._quote('account_id')} IN :account_ids", f"{activity_date} >= :since"]
        where_parts.extend(self._active_where("t", columns))
        sql = f"""
            SELECT t.{self._quote('account_id')} AS account_id, COUNT(*) AS total
            FROM {self._quote(table_name)} t
            WHERE {" AND ".join(where_parts)}
            GROUP BY t.{self._quote('account_id')}
        """
        stmt = text(sql).bindparams(bindparam("account_ids", expanding=True))
        rows = (await self.session.execute(stmt, {"account_ids": account_ids, "since": since})).all()
        return {account_id: int(total) for account_id, total in rows}

    async def _count_recent_direct_call_activity(self, account_ids: list[str], since) -> dict[str, int]:
        call_columns = await self._table_columns("calls")
        if not call_columns:
            return {}

        account_column = self._first_existing(call_columns, ["account_id", "parent_id", "module_id"])
        activity_date = self._activity_date_expression("c", call_columns)
        if account_column is None or activity_date is None:
            return {}

        where_parts = [f"c.{self._quote(account_column)} IN :account_ids", f"{activity_date} >= :since"]
        where_parts.extend(self._active_where("c", call_columns))
        if account_column == "parent_id" and "parent_module" in call_columns:
            where_parts.append(f"LOWER(c.{self._quote('parent_module')}) IN ('accounts', 'account')")

        sql = f"""
            SELECT c.{self._quote(account_column)} AS account_id, COUNT(*) AS total
            FROM {self._quote("calls")} c
            WHERE {" AND ".join(where_parts)}
            GROUP BY c.{self._quote(account_column)}
        """
        stmt = text(sql).bindparams(bindparam("account_ids", expanding=True))
        rows = (await self.session.execute(stmt, {"account_ids": account_ids, "since": since})).all()
        return {account_id: int(total) for account_id, total in rows}

    async def list_all_calls(self) -> list[Any]:
        if not await self._table_exists("calls"):
            return []
        columns = await self._table_columns("calls")
        where_parts = self._active_where("c", columns)
        order_parts = self._order_parts("c", columns, [("start_date", "ASC"), ("created_at", "ASC")])
        sql = f"""
            SELECT {self._select_list("c", self._call_select_columns(), columns)}
            FROM {self._quote("calls")} c
            WHERE {" AND ".join(where_parts)}
            ORDER BY {", ".join(order_parts)}
        """
        rows = (await self.session.execute(text(sql))).mappings().all()
        return [self._namespace(row) for row in rows]

    async def ping(self) -> bool:
        await self.session.execute(select(1))
        return True

    async def _count_by_account(self, table_name: str, account_ids: list[str]) -> dict[str, int]:
        if not account_ids:
            return {}
        columns = await self._table_columns(table_name)
        if "account_id" not in columns:
            return {}
        where_parts = [f"t.{self._quote('account_id')} IN :account_ids"]
        where_parts.extend(self._active_where("t", columns))
        count_column = "id" if "id" in columns else "account_id"
        sql = f"""
            SELECT t.{self._quote('account_id')} AS account_id, COUNT(t.{self._quote(count_column)}) AS total
            FROM {self._quote(table_name)} t
            WHERE {" AND ".join(where_parts)}
            GROUP BY t.{self._quote('account_id')}
        """
        stmt = text(sql).bindparams(bindparam("account_ids", expanding=True))
        rows = (await self.session.execute(stmt, {"account_ids": account_ids})).all()
        return {account_id: int(total) for account_id, total in rows}

    async def _table_exists(self, table_name: str) -> bool:
        table_names = await self._table_names()
        return table_name in table_names

    async def _table_names(self) -> set[str]:
        if self._table_cache is not None:
            return self._table_cache
        dialect = self._dialect_name()
        if dialect == "mysql":
            rows = await self.session.execute(text("SHOW TABLES"))
            self._table_cache = {str(row[0]) for row in rows}
        else:
            rows = await self.session.execute(
                text(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    """
                )
            )
            self._table_cache = {str(row[0]) for row in rows}
        return self._table_cache

    async def _table_columns(self, table_name: str) -> set[str]:
        if table_name in self._column_cache:
            return self._column_cache[table_name]
        if self._table_cache is not None and table_name not in self._table_cache:
            self._column_cache[table_name] = set()
            return set()

        dialect = self._dialect_name()
        try:
            if dialect == "mysql":
                rows = await self.session.execute(text(f"SHOW COLUMNS FROM {self._quote(table_name)}"))
                columns = {str(row[0]) for row in rows}
            else:
                rows = await self.session.execute(
                    text(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = :table_name
                        """
                    ),
                    {"table_name": table_name},
                )
                columns = {str(row[0]) for row in rows}
        except SQLAlchemyError:
            columns = set()

        self._column_cache[table_name] = columns
        return columns

    def _select_list(self, alias: str, requested_columns: list[str], available_columns: set[str]) -> str:
        return ", ".join(self._select_expr(alias, column, available_columns) for column in requested_columns)

    def _select_expr(self, alias: str, column: str, available_columns: set[str]) -> str:
        quoted = self._quote(column)
        if column in available_columns:
            return f"{alias}.{quoted} AS {quoted}"
        return f"NULL AS {quoted}"

    def _active_where(self, alias: str, columns: set[str]) -> list[str]:
        if "deleted_at" in columns:
            return [f"{alias}.{self._quote('deleted_at')} IS NULL"]
        return ["1 = 1"]

    def _order_parts(self, alias: str, columns: set[str], candidates: list[tuple[str, str]]) -> list[str]:
        parts: list[str] = []
        for column, direction in candidates:
            if column in columns:
                quoted = self._quote(column)
                parts.append(f"{alias}.{quoted} IS NULL")
                parts.append(f"{alias}.{quoted} {direction}")
        if not parts:
            parts.append(f"{alias}.{self._quote('id')} ASC")
        return parts

    def _activity_date_expression(self, alias: str, columns: set[str]) -> str | None:
        if "updated_at" in columns and "created_at" in columns:
            return f"COALESCE({alias}.{self._quote('updated_at')}, {alias}.{self._quote('created_at')})"
        if "updated_at" in columns:
            return f"{alias}.{self._quote('updated_at')}"
        if "created_at" in columns:
            return f"{alias}.{self._quote('created_at')}"
        return None

    def _call_select_columns(self) -> list[str]:
        return [
            "id",
            "name",
            "assigned_user_id",
            "direction",
            "start_date",
            "end_date",
            "duration",
            "total_duration_minute",
            "call_status",
            "logged_by",
            "call_type",
            "latest_comment",
            "overall_call_rating",
            "call_quality_metrics",
            "sentiment_analysis",
            "next_step",
            "call_outcome",
            "mom",
            "summary",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def _first_existing(self, columns: set[str], candidates: list[str]) -> str | None:
        return next((column for column in candidates if column in columns), None)

    def _namespace(self, row) -> SimpleNamespace:
        return SimpleNamespace(**dict(row))

    def _quote(self, identifier: str) -> str:
        if self._dialect_name() == "mysql":
            return f"`{identifier}`"
        return f'"{identifier}"'

    def _dialect_name(self) -> str:
        bind = self.session.get_bind()
        return bind.dialect.name
