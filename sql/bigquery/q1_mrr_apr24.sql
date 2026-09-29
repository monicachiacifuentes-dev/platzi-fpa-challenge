-- WP34b -- Q1: MRR at 2024-04-30 by segment, BigQuery Standard SQL port.
-- Metric IDs: M-01 (as-of date), M-02 (active sub), M-03 (MRR), M-04 (segment).
-- Mirrors DuckDB mart: sql/marts/mart_q1_mrr_apr24.sql (via
-- fct_customer_mrr_monthly, itself built from stg_users + stg_subscriptions +
-- int_month_spine). This file recomputes everything FROM raw_users /
-- raw_subscriptions ONLY -- no mart_*/fct_* tables are read.
-- Expected total ~= 204,709.09 (B2C 64,365.00 / SMB 53,869.37 / Enterprise 86,474.72).
--
-- Dialect differences vs. DuckDB (see sql/README.md):
--  * int_month_spine used generate_series(DATE,DATE,INTERVAL) -> here we only
--    need the single month-end 2024-04-30, so no date-spine function is
--    needed at all (kept the query simpler than the full monthly grid).
--  * DuckDB CAST(... AS DOUBLE) -> BigQuery FLOAT64 (mrr already loads as
--    FLOAT64/FLOAT from autodetect, so no cast needed).
--  * raw_users.signup_date / raw_subscriptions.start_date,end_date autodetected
--    as DATE by BigQuery load (verified via `bq show --schema`), so no
--    SAFE.PARSE_DATE / CAST(... AS DATE) from STRING is required here; the
--    query still casts defensively as a no-op safeguard.
CREATE OR REPLACE TABLE platzi_fpa.bq_q1_mrr_apr24 AS
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
        CAST(start_date AS DATE) AS start_date,
        CAST(end_date AS DATE)   AS end_date,
        CAST(mrr AS FLOAT64)     AS mrr
    FROM platzi_fpa.raw_subscriptions
),
active_apr24 AS (
    -- M-02: start_date <= D < end_date, D = 2024-04-30
    SELECT s.user_id, u.segment, u.customer_type, s.mrr
    FROM stg_subscriptions s
    JOIN stg_users u ON u.user_id = s.user_id
    WHERE s.start_date <= DATE '2024-04-30' AND DATE '2024-04-30' < s.end_date
),
by_segment AS (
    SELECT segment, SUM(mrr) AS mrr
    FROM active_apr24
    GROUP BY segment
),
b2b AS (
    SELECT 'B2B' AS segment, SUM(mrr) AS mrr
    FROM active_apr24
    WHERE customer_type = 'B2B'
),
total AS (
    SELECT 'Total' AS segment, SUM(mrr) AS mrr
    FROM active_apr24
),
unioned AS (
    SELECT * FROM by_segment
    UNION ALL SELECT * FROM b2b
    UNION ALL SELECT * FROM total
)
SELECT
    segment,
    mrr,
    ROUND(100.0 * mrr / (SELECT mrr FROM total), 2) AS pct_of_total
FROM unioned
ORDER BY CASE segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'B2B' THEN 4 WHEN 'Total' THEN 5 END;
