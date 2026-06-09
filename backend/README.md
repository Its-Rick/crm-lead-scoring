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
