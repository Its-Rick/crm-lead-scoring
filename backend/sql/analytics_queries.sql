-- Account-level metrics through the allowed CRM tables only.
-- calls are linked to accounts through activities_rel.

WITH account_calls AS (
    SELECT
        ar.parent_id AS account_id,
        c.id AS call_id,
        c.total_duration_minute,
        c.call_status,
        c.call_outcome,
        c.overall_call_rating,
        c.sentiment_analysis,
        c.start_date
    FROM activities_rel ar
    JOIN calls c ON c.id = ar.activity_id
    WHERE ar.deleted_at IS NULL
      AND c.deleted_at IS NULL
      AND lower(ar.parent_module) IN ('accounts', 'account')
      AND lower(ar.activity_module) IN ('calls', 'call')
),
opportunities AS (
    SELECT account_id, count(*) AS opportunities_count
    FROM account_opportunity
    WHERE deleted_at IS NULL
    GROUP BY account_id
),
tickets AS (
    SELECT account_id, count(*) AS ticket_count
    FROM account_ticket
    WHERE deleted_at IS NULL
    GROUP BY account_id
),
recent_activities AS (
    SELECT parent_id AS account_id, count(*) AS recent_activities_count
    FROM activities_rel
    WHERE deleted_at IS NULL
      AND lower(parent_module) IN ('accounts', 'account')
      AND coalesce(updated_at, created_at) >= now() - interval '14 days'
    GROUP BY parent_id
)
SELECT
    a.id,
    a.name,
    a.industry,
    a.customer_type,
    a.account_status,
    a.rating,
    coalesce(a.untouched_since_days, 0) AS untouched_since_days,
    count(ac.call_id) AS total_calls,
    coalesce(avg(ac.total_duration_minute), 0) AS average_call_duration,
    coalesce(avg(ac.overall_call_rating), 0) AS average_call_rating,
    coalesce(o.opportunities_count, 0) AS opportunities_count,
    coalesce(t.ticket_count, 0) AS ticket_count,
    coalesce(ra.recent_activities_count, 0) AS recent_activities_count
FROM accounts a
LEFT JOIN account_calls ac ON ac.account_id = a.id
LEFT JOIN opportunities o ON o.account_id = a.id
LEFT JOIN tickets t ON t.account_id = a.id
LEFT JOIN recent_activities ra ON ra.account_id = a.id
WHERE a.deleted_at IS NULL
GROUP BY a.id, o.opportunities_count, t.ticket_count, ra.recent_activities_count;

