-- WP34b -- Q3: active subscriptions at 2024-04-30 by segment x plan_type, BigQuery Standard SQL port.
-- Metric ID: M-02 (active subscription on date D).
-- Mirrors DuckDB mart: sql/marts/mart_q3_active_subs_apr24.sql (direct from
-- stg_subscriptions + stg_users, no fct_* dependency in DuckDB either).
-- Recomputed FROM raw_users / raw_subscriptions ONLY.
-- Expected grand total = 1,941.
--
-- Dialect differences vs. DuckDB: none of substance -- this mart doesn't use
-- window functions or date-diff functions; only CAST/TRIM/CASE, which are
-- ANSI-portable.
CREATE OR REPLACE TABLE platzi_fpa.bq_q3_active_subs_apr24 AS
WITH stg_users AS (
    SELECT
        TRIM(user_id)  AS user_id,
        TRIM(segment)  AS segment
    FROM platzi_fpa.raw_users
),
stg_subscriptions AS (
    SELECT
        TRIM(subscription_id) AS subscription_id,
        TRIM(user_id)          AS user_id,
        TRIM(plan_type)        AS plan_type,
        CAST(start_date AS DATE) AS start_date,
        CAST(end_date AS DATE)   AS end_date
    FROM platzi_fpa.raw_subscriptions
),
active AS (
    SELECT s.subscription_id, u.segment, s.plan_type
    FROM stg_subscriptions s
    JOIN stg_users u ON u.user_id = s.user_id
    WHERE s.start_date <= DATE '2024-04-30' AND DATE '2024-04-30' < s.end_date
),
cell AS (
    SELECT segment, plan_type, COUNT(*) AS active_subs
    FROM active
    GROUP BY segment, plan_type
),
segment_total AS (
    SELECT segment, 'Total' AS plan_type, COUNT(*) AS active_subs
    FROM active
    GROUP BY segment
),
plan_total AS (
    SELECT 'Total' AS segment, plan_type, COUNT(*) AS active_subs
    FROM active
    GROUP BY plan_type
),
grand_total AS (
    SELECT 'Total' AS segment, 'Total' AS plan_type, COUNT(*) AS active_subs
    FROM active
),
unioned AS (
    SELECT * FROM cell
    UNION ALL SELECT * FROM segment_total
    UNION ALL SELECT * FROM plan_total
    UNION ALL SELECT * FROM grand_total
)
SELECT * FROM unioned
ORDER BY
    CASE segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'Total' THEN 4 END,
    CASE plan_type WHEN 'monthly' THEN 1 WHEN 'annual' THEN 2 WHEN 'Total' THEN 3 END;
