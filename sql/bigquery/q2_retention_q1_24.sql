-- WP34b -- Q2: Q1 2024 retention (logo & $), B2C vs B2B, BigQuery Standard SQL port.
-- Metric IDs: M-06 (primary, renewal-event basis), M-07 (cross-check, customer-snapshot basis).
-- Mirrors DuckDB mart: sql/marts/mart_q2_retention_q1_24.sql (via
-- fct_subscriptions / int_subscription_periods for M-06, stg_subscriptions +
-- stg_users directly for M-07). Recomputed FROM raw_users / raw_subscriptions
-- ONLY -- no mart_*/fct_* tables are read.
-- Expected: logo retention ~90.1% (Total, M-06 'all' split).
--
-- Dialect differences vs. DuckDB (see sql/README.md):
--  * LAG/LEAD/ROW_NUMBER window functions are ANSI-portable, unchanged.
--  * DuckDB CAST(... AS BIGINT) -> BigQuery INT64 (integer literals/COUNT
--    already return INT64, so the casts here are a no-op safeguard only).
--  * No DATE_DIFF / date-spine functions needed in this query.
CREATE OR REPLACE TABLE platzi_fpa.bq_q2_retention_q1_24 AS
WITH stg_users AS (
    SELECT
        TRIM(user_id)  AS user_id,
        TRIM(segment)  AS segment,
        CASE WHEN TRIM(segment) = 'B2C' THEN 'B2C' ELSE 'B2B' END AS customer_type
    FROM platzi_fpa.raw_users
),
stg_subscriptions AS (
    SELECT
        TRIM(subscription_id) AS subscription_id,
        TRIM(user_id)          AS user_id,
        TRIM(plan_type)        AS plan_type,
        CAST(start_date AS DATE) AS start_date,
        CAST(end_date AS DATE)   AS end_date,
        CAST(mrr AS FLOAT64)     AS mrr,
        TRIM(status)             AS status
    FROM platzi_fpa.raw_subscriptions
),
-- int_subscription_periods equivalent (only the columns Q2 needs)
periods AS (
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
        LEAD(s.mrr) OVER (PARTITION BY s.user_id ORDER BY s.start_date) AS next_mrr
    FROM stg_subscriptions s
    JOIN stg_users u ON u.user_id = s.user_id
),
ended AS (
    SELECT *
    FROM periods
    WHERE end_date BETWEEN DATE '2024-01-01' AND DATE '2024-03-31'
      AND status IN ('renewed', 'churned')
),
ended_expanded AS (
    SELECT segment AS segment_group, plan_type, status, mrr, next_mrr FROM ended
    UNION ALL
    SELECT 'B2B', plan_type, status, mrr, next_mrr FROM ended WHERE customer_type = 'B2B'
    UNION ALL
    SELECT 'Total', plan_type, status, mrr, next_mrr FROM ended
),
m06_all AS (
    SELECT
        segment_group AS segment,
        'all'          AS split,
        'M06_primary'  AS method,
        CAST(SUM(CASE WHEN status = 'renewed' THEN 1 ELSE 0 END) AS INT64) AS n_renewed,
        CAST(SUM(CASE WHEN status = 'churned' THEN 1 ELSE 0 END) AS INT64) AS n_churned,
        CAST(COUNT(*) AS INT64)                                            AS n_ended,
        ROUND(1.0 * SUM(CASE WHEN status = 'renewed' THEN 1 ELSE 0 END) / COUNT(*), 4) AS logo_rate,
        CAST(SUM(CASE WHEN status = 'renewed' THEN next_mrr ELSE 0 END) AS FLOAT64)    AS dollar_numerator,
        CAST(SUM(mrr) AS FLOAT64)                                                      AS dollar_denominator,
        ROUND(SUM(CASE WHEN status = 'renewed' THEN next_mrr ELSE 0 END) / SUM(mrr), 4) AS dollar_rate
    FROM ended_expanded
    GROUP BY segment_group
),
m06_by_plan AS (
    SELECT
        segment_group AS segment,
        plan_type      AS split,
        'M06_primary'  AS method,
        CAST(SUM(CASE WHEN status = 'renewed' THEN 1 ELSE 0 END) AS INT64) AS n_renewed,
        CAST(SUM(CASE WHEN status = 'churned' THEN 1 ELSE 0 END) AS INT64) AS n_churned,
        CAST(COUNT(*) AS INT64)                                            AS n_ended,
        ROUND(1.0 * SUM(CASE WHEN status = 'renewed' THEN 1 ELSE 0 END) / COUNT(*), 4) AS logo_rate,
        CAST(SUM(CASE WHEN status = 'renewed' THEN next_mrr ELSE 0 END) AS FLOAT64)    AS dollar_numerator,
        CAST(SUM(mrr) AS FLOAT64)                                                      AS dollar_denominator,
        ROUND(SUM(CASE WHEN status = 'renewed' THEN next_mrr ELSE 0 END) / SUM(mrr), 4) AS dollar_rate
    FROM ended_expanded
    GROUP BY segment_group, plan_type
),
active_dec AS (
    SELECT DISTINCT s.user_id, u.segment, u.customer_type
    FROM stg_subscriptions s
    JOIN stg_users u ON u.user_id = s.user_id
    WHERE s.start_date <= DATE '2023-12-31' AND DATE '2023-12-31' < s.end_date
),
active_mar AS (
    SELECT DISTINCT s.user_id
    FROM stg_subscriptions s
    WHERE s.start_date <= DATE '2024-03-31' AND DATE '2024-03-31' < s.end_date
),
active_dec_expanded AS (
    SELECT segment AS segment_group, user_id FROM active_dec
    UNION ALL
    SELECT 'B2B', user_id FROM active_dec WHERE customer_type = 'B2B'
    UNION ALL
    SELECT 'Total', user_id FROM active_dec
),
m07 AS (
    SELECT
        ad.segment_group AS segment,
        'all'             AS split,
        'M07_crosscheck'  AS method,
        CAST(NULL AS INT64) AS n_renewed,
        CAST(NULL AS INT64) AS n_churned,
        CAST(COUNT(DISTINCT ad.user_id) AS INT64) AS n_ended,  -- base: active on 2023-12-31
        ROUND(1.0 * COUNT(DISTINCT CASE WHEN am.user_id IS NOT NULL THEN ad.user_id END) / COUNT(DISTINCT ad.user_id), 4) AS logo_rate,
        CAST(NULL AS FLOAT64) AS dollar_numerator,
        CAST(NULL AS FLOAT64) AS dollar_denominator,
        CAST(NULL AS FLOAT64) AS dollar_rate
    FROM active_dec_expanded ad
    LEFT JOIN active_mar am ON am.user_id = ad.user_id
    GROUP BY ad.segment_group
),
unioned AS (
    SELECT * FROM m06_all
    UNION ALL SELECT * FROM m06_by_plan
    UNION ALL SELECT * FROM m07
)
SELECT * FROM unioned
ORDER BY
    method,
    CASE segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'B2B' THEN 4 WHEN 'Total' THEN 5 END,
    split;
