-- int_subscription_periods: one row per subscription period, enriched with
-- user segment/customer_type, engagement, sequence within user's history,
-- prev/next MRR, renewal_change classification, tenure and period length.
--
-- Portability note: DATE_DIFF('day'/'month', a, b) uses DuckDB's argument
-- order (unit, start, end). BigQuery's DATE_DIFF(end, start, unit) takes the
-- dates first and the unit last, and has no 'day' subtraction shortcut via
-- the `-` operator on DATE-DATE (which DuckDB does support) -- see sql/README.md.
SELECT
    s.subscription_id,
    s.user_id,
    u.segment,
    u.customer_type,
    s.plan_type,
    s.start_date,
    s.end_date,
    s.mrr,
    s.status,
    s.status                                                        AS next_status,  -- see README: status already encodes the fate at end_date (renewed/active/churned)
    e.active_days,
    e.courses_seen,
    e.materials_seen,
    e.favorite_category,
    ROW_NUMBER() OVER (PARTITION BY s.user_id ORDER BY s.start_date) AS period_number,
    LAG(s.mrr)  OVER (PARTITION BY s.user_id ORDER BY s.start_date)  AS prev_mrr,
    LEAD(s.mrr) OVER (PARTITION BY s.user_id ORDER BY s.start_date)  AS next_mrr,
    s.mrr - LAG(s.mrr) OVER (PARTITION BY s.user_id ORDER BY s.start_date) AS mrr_delta,
    CASE
        WHEN LAG(s.mrr) OVER (PARTITION BY s.user_id ORDER BY s.start_date) IS NULL THEN 'new'
        WHEN s.mrr - LAG(s.mrr) OVER (PARTITION BY s.user_id ORDER BY s.start_date) > 0 THEN 'expansion'
        WHEN s.mrr - LAG(s.mrr) OVER (PARTITION BY s.user_id ORDER BY s.start_date) < 0 THEN 'contraction'
        ELSE 'flat'
    END                                                               AS renewal_change,
    (EXTRACT(YEAR FROM s.start_date)  - EXTRACT(YEAR FROM u.signup_date)) * 12
        + (EXTRACT(MONTH FROM s.start_date) - EXTRACT(MONTH FROM u.signup_date)) AS tenure_months,
    DATE_DIFF('day', s.start_date, s.end_date)                       AS period_days
FROM stg_subscriptions s
JOIN stg_users u       ON u.user_id = s.user_id
LEFT JOIN stg_engagement e ON e.subscription_id = s.subscription_id
