import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from faker import Faker
from sqlalchemy import text

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.core.database import get_sessionmaker
from app.models.crm import Account, AccountOpportunity, AccountTicket, ActivityRel, Call

fake = Faker()
SCHEMA_PATH = ROOT_DIR / "sql" / "schema.sql"


def new_id() -> str:
    return str(uuid4())


async def main() -> None:
    async with get_sessionmaker()() as session:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        for statement in [part.strip() for part in schema_sql.split(";") if part.strip()]:
            await session.execute(text(statement))
        await session.commit()

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        accounts: list[Account] = []
        calls_inserted = 0
        opportunities_inserted = 0
        tickets_inserted = 0
        for _ in range(50):
            account = Account(
                id=new_id(),
                name=fake.company(),
                assigned_user_id=new_id(),
                customer_type=random.choice(["Prospect", "Customer", "Partner"]),
                account_status=random.choice(["New", "Active", "Dormant", "Qualified"]),
                industry=random.choice(["Manufacturing", "SaaS", "Finance", "Healthcare", "Retail"]),
                rating=random.choice(["A", "B", "C"]),
                how_old_days=random.randint(1, 720),
                untouched_since_days=random.randint(0, 60),
                latest_comment=fake.sentence(),
                created_at=now - timedelta(days=random.randint(1, 365)),
                updated_at=now - timedelta(days=random.randint(0, 30)),
            )
            accounts.append(account)
            session.add(account)

        for account in accounts:
            for _ in range(random.randint(0, 8)):
                call_id = new_id()
                sentiment = random.choice(
                    [
                        {"label": "positive", "score": random.uniform(0.4, 1)},
                        {"label": "neutral", "score": random.uniform(-0.2, 0.2)},
                        {"label": "negative", "score": random.uniform(-1, -0.3)},
                    ]
                )
                call = Call(
                    id=call_id,
                    name=f"Call with {account.name}",
                    assigned_user_id=account.assigned_user_id,
                    start_date=now - timedelta(days=random.randint(0, 90)),
                    total_duration_minute=Decimal(str(round(random.uniform(1, 18), 2))),
                    call_status=random.choice(["Completed", "Connected", "Missed", "No Answer", "Failed"]),
                    overall_call_rating=random.randint(1, 5),
                    sentiment_analysis=sentiment,
                    call_quality_metrics={"clarity": random.randint(1, 5), "script_adherence": random.randint(1, 5)},
                    next_step=random.choice(["Send proposal", "Schedule demo", "Call back", "Escalate ticket"]),
                    call_outcome=random.choice(["Interested", "Converted", "Not connected", "Rejected", "Follow up"]),
                    summary={"text": fake.sentence()},
                    created_at=now,
                    updated_at=now,
                )
                session.add(call)
                session.add(
                    ActivityRel(
                        id=new_id(),
                        parent_module="Accounts",
                        parent_id=account.id,
                        initial_module="Accounts",
                        initial_id=account.id,
                        activity_module="Calls",
                        activity_id=call_id,
                        created_at=call.start_date,
                        updated_at=call.start_date,
                    )
                )
                calls_inserted += 1

            for _ in range(random.randint(0, 3)):
                session.add(
                    AccountOpportunity(
                        id=new_id(),
                        account_id=account.id,
                        opportunity_id=new_id(),
                        created_at=now,
                        updated_at=now,
                    )
                )
                opportunities_inserted += 1
            for _ in range(random.randint(0, 4)):
                session.add(
                    AccountTicket(
                        id=new_id(),
                        account_id=account.id,
                        ticket_id=new_id(),
                        created_at=now,
                        updated_at=now,
                    )
                )
                tickets_inserted += 1

        await session.commit()
        print("Faker seed completed")
        print(f"accounts: {len(accounts)}")
        print(f"calls: {calls_inserted}")
        print(f"activities_rel: {calls_inserted}")
        print(f"account_opportunity: {opportunities_inserted}")
        print(f"account_ticket: {tickets_inserted}")


if __name__ == "__main__":
    asyncio.run(main())
