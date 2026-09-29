-- WP34b -- Q4: NDR T12M (M-08), GRR (M-09), Start/Exp/Contr/Churn/End bridge (M-10),
-- BigQuery Standard SQL port.
-- Mirrors DuckDB mart: sql/marts/mart_q4_ndr_t12m.sql (via fct_customer_mrr_monthly
-- for the primary snapshot method, fct_subscriptions/int_subscription_periods for
-- the renewal-event cross-check). Recomputed FROM raw_users / raw_subscriptions
-- ONLY -- no mart_*/fct_* tables are read.
-- Expected: NDR T12M (Total) ~63.7%, GRR ~59.9%, base 417 customers.
--
-- Dialect differences vs. DuckDB (see sql/README.md):
--  * fct_customer_mrr_monthly in DuckDB builds a full 16-month grid via
--    int_month_spine (generate_series). Here we only need MRR at two fixed
--    snapshot dates (2023-04-30 and 2024-04-30) for the M-08/M-09 base, so we
--    compute "active MRR as of D" directly per user for just those two dates
--    instead of materializing the full monthly grid -- mathematically
--    equivalent for this query (COALESCE(...,0) when no subscription covers
--    D matches the grid's 0-mrr row).
--  * LAG/ROW_NUMBER window functions (renewal cross-check) are ANSI-portable,
--    unchanged from DuckDB.
--  * DuckDB LEAST(a,b) -> BigQuery LEAST(a,b) (same function name/semantics).
CREATE OR REPLACE TABLE platzi_fpa.bq_q4_ndr_t12m AS
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
-- MRR per user as of a fixed snapshot date (M-02), equivalent to
-- fct_customer_mrr_monthly.mrr at that month_end
mrr_2023_04 AS (
    SELECT s.user_id, u.segment, u.customer_type, SUM(s.mrr) AS start_mrr
    FROM stg_subscriptions s
    JOIN stg_users u ON u.user_id = s.user_id
    WHERE s.start_date <= DATE '2023-04-30' AND DATE '2023-04-30' < s.end_date
    GROUP BY s.user_id, u.segment, u.customer_type
),
mrr_2024_04 AS (
    SELECT s.user_id, SUM(s.mrr) AS end_mrr
    FROM stg_subscriptions s
    WHERE s.start_date <= DATE '2024-04-30' AND DATE '2024-04-30' < s.end_date
    GROUP BY s.user_id
),
base AS (
    -- M-08 base: customers active (mrr > 0) on 2023-04-30
    SELECT user_id, segment, customer_type, start_mrr
    FROM mrr_2023_04
    WHERE start_mrr > 0
),
joined AS (
    SELECT b.user_id, b.segment, b.customer_type, b.start_mrr,
           COALESCE(e.end_mrr, 0) AS end_mrr
    FROM base b
    LEFT JOIN mrr_2024_04 e ON e.user_id = b.user_id
),
expanded AS (
    SELECT segment AS segment_group, start_mrr, end_mrr FROM joined
    UNION ALL
    SELECT 'B2B', start_mrr, end_mrr FROM joined WHERE customer_type = 'B2B'
    UNION ALL
    SELECT 'Total', start_mrr, end_mrr FROM joined
),
primary_agg AS (
    SELECT
        'M08_M09_M10' AS method,
        segment_group AS segment,
        CAST(COUNT(*) AS INT64)                                                          AS base_customers,
        SUM(start_mrr)                                                                    AS start_mrr,
        SUM(CASE WHEN end_mrr > start_mrr THEN end_mrr - start_mrr ELSE 0 END)            AS expansion_mrr,
        SUM(CASE WHEN end_mrr > 0 AND end_mrr < start_mrr THEN start_mrr - end_mrr ELSE 0 END) AS contraction_mrr,
        SUM(CASE WHEN end_mrr = 0 THEN start_mrr ELSE 0 END)                              AS churn_mrr,
        SUM(end_mrr)                                                                       AS end_mrr,
        ROUND(SUM(end_mrr) / NULLIF(SUM(start_mrr), 0), 4)                                 AS ndr,
        ROUND(SUM(LEAST(end_mrr, start_mrr)) / NULLIF(SUM(start_mrr), 0), 4)               AS grr
    FROM expanded
    GROUP BY segment_group
),
-- int_subscription_periods equivalent (only columns the renewal cross-check needs)
periods AS (
    SELECT
        s.user_id,
        u.segment,
        u.customer_type,
        s.start_date,
        ROW_NUMBER() OVER (PARTITION BY s.user_id ORDER BY s.start_date) AS period_number,
        s.mrr - LAG(s.mrr) OVER (PARTITION BY s.user_id ORDER BY s.start_date) AS mrr_delta
    FROM stg_subscriptions s
    JOIN stg_users u ON u.user_id = s.user_id
),
renewal_events AS (
    SELECT segment AS segment_group, customer_type, mrr_delta
    FROM periods
    WHERE period_number > 1
      AND start_date BETWEEN DATE '2023-05-01' AND DATE '2024-04-30'
),
renewal_events_expanded AS (
    SELECT segment_group, mrr_delta FROM renewal_events
    UNION ALL
    SELECT 'B2B', mrr_delta FROM renewal_events WHERE customer_type = 'B2B'
    UNION ALL
    SELECT 'Total', mrr_delta FROM renewal_events
),
crosscheck AS (
    SELECT
        'renewal_crosscheck' AS method,
        segment_group          AS segment,
        CAST(COUNT(*) AS INT64)                                     AS base_customers,  -- renewal-event count, not customer count
        CAST(NULL AS FLOAT64)                                       AS start_mrr,
        SUM(CASE WHEN mrr_delta > 0 THEN mrr_delta ELSE 0 END)      AS expansion_mrr,
        SUM(CASE WHEN mrr_delta < 0 THEN -mrr_delta ELSE 0 END)     AS contraction_mrr,
        CAST(NULL AS FLOAT64)                                       AS churn_mrr,
        CAST(NULL AS FLOAT64)                                       AS end_mrr,
        CAST(NULL AS FLOAT64)                                       AS ndr,
        CAST(NULL AS FLOAT64)                                       AS grr
    FROM renewal_events_expanded
    GROUP BY segment_group
),
unioned AS (
    SELECT * FROM primary_agg
    UNION ALL
    SELECT * FROM crosscheck
)
SELECT * FROM unioned
ORDER BY
    method,
    CASE segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'B2B' THEN 4 WHEN 'Total' THEN 5 END;
