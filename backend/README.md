# CRM AI Analytics Backend

FastAPI MVP for explainable CRM analytics using only the required CRM schema tables.

## What It Provides

- AI Lead Scoring with deterministic explanations.
- AI Call Insights for dashboard widgets.
- Smart Follow-Up Recommendations.
- One shared pipeline based on `accounts`, `calls`, `activities_rel`, `account_opportunity`, and `account_ticket`.
- No authentication, no chatbot, and no analytics result tables.

## Relationship Model

`calls` does not contain `account_id`. Account-call relationships are derived from `activities_rel`:

```sql
activities_rel.parent_id = accounts.id
activities_rel.activity_id = calls.id
lower(parent_module) in ('accounts', 'account')
lower(activity_module) in ('calls', 'call')
```

## Local Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
docker compose up -d
psql "postgresql://crm:crm@localhost:5432/crm_analytics" -f sql/schema.sql
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

The basic dashboard is available at `http://127.0.0.1:8000/`.

## Use Existing Local MySQL Data

If your CRM tables already exist in MySQL, do not run `sql/schema.sql` and do not run the Faker seed script. Point the backend at your existing database instead.

1. Install dependencies:

```bash
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Create or update `.env`:

```env
DATABASE_URL=mysql+aiomysql://MYSQL_USER:MYSQL_PASSWORD@127.0.0.1:3306/MYSQL_DATABASE
ENABLE_OPENAI_INSIGHTS=false
OPENAI_API_KEY=
CACHE_TTL_SECONDS=300
```

Example:

```env
DATABASE_URL=mysql+aiomysql://root:password@127.0.0.1:3306/sangam_crm
```

3. Confirm these tables exist in MySQL:

```sql
SHOW TABLES;
DESCRIBE accounts;
DESCRIBE calls;
DESCRIBE activities_rel;
```

The analytics require `activities_rel` to connect accounts to calls:

```text
activities_rel.parent_id = accounts.id
activities_rel.activity_id = calls.id
```

For the provided `sangam_crm` dump, `activities_rel` is not present and `calls` has no account/contact foreign key. In that schema, account lead scores use account profile fields plus `account_opportunity`, `account_lead`, and `account_contact` activity. Call insights still use the global `calls` table, but calls are not attributed to individual accounts unless a relationship column/table is added.

4. Start the API:

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/
```

## APIs

- `GET /health`
- `GET /api/v1/analytics/accounts`
- `GET /api/v1/analytics/accounts/{account_id}`
- `GET /api/v1/analytics/lead-scores?category=Hot&min_score=75`
- `GET /api/v1/analytics/call-insights`
- `GET /api/v1/analytics/follow-ups`
- `POST /api/v1/pipeline/refresh`

## Dashboard Response Shape

```json
{
  "account_id": "uuid",
  "account_name": "Acme Ltd",
  "metrics": {
    "total_calls": 8,
    "average_call_duration": 6.4,
    "average_sentiment": 0.52,
    "opportunities_count": 2,
    "ticket_count": 1,
    "recent_activities_count": 3,
    "average_call_rating": 4.2,
    "failed_calls_count": 1,
    "successful_calls_count": 5,
    "untouched_since_days": 4
  },
  "lead_score": {
    "score": 86,
    "category": "Hot",
    "explanations": ["Lead has high engagement from repeated calls"]
  },
  "follow_up": {
    "priority": "Low",
    "suggested_action": "Call to move opportunity forward",
    "recommended_time": "within 7 days",
    "reasons": ["High conversion probability"]
  }
}
```

## Notes

The Faker seed script expects the allowed tables to already exist in PostgreSQL. Create them with `sql/schema.sql`, then run `python scripts/seed_faker_data.py`.
