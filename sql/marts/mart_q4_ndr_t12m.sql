-- mart_q4_ndr_t12m: Q4 -- NDR T12M (M-08), GRR (M-09), and Start/Exp/Contr/Churn/End
-- components (M-10) for the base of customers active on 2023-04-30, evaluated at
-- 2024-04-30. By segment, B2B roll-up and Total. Includes base customer count.
--
-- method = 'M08_M09_M10'       : the primary snapshot-based NDR/GRR/bridge.
-- method = 'renewal_crosscheck': cross-check -- sum of mrr_delta at renewal events
--                                 (period_number > 1) with start_date in
--                                 [2023-05-01, 2024-04-30], split into expansion vs
--                                 contraction. NOTE: this population is NOT the same
--                                 as the M-08 base (it includes renewals of customers
--                                 who signed up after 2023-04-30), so exact equality
--                                 with the M-10 components above is not expected --
--                                 it is a directional sanity check only.
WITH base AS (
    SELECT user_id, segment, customer_type, mrr AS start_mrr
    FROM fct_customer_mrr_monthly
    WHERE month_end = DATE '2023-04-30' AND mrr > 0
),
end_mrr AS (
    SELECT user_id, mrr AS end_mrr
    FROM fct_customer_mrr_monthly
    WHERE month_end = DATE '2024-04-30'
),
joined AS (
    SELECT b.user_id, b.segment, b.customer_type, b.start_mrr, COALESCE(e.end_mrr, 0) AS end_mrr
    FROM base b
    LEFT JOIN end_mrr e ON e.user_id = b.user_id
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
        CAST(COUNT(*) AS BIGINT)                                                              AS base_customers,
        SUM(start_mrr)                                                                         AS start_mrr,
        SUM(CASE WHEN end_mrr > start_mrr THEN end_mrr - start_mrr ELSE 0 END)                 AS expansion_mrr,
        SUM(CASE WHEN end_mrr > 0 AND end_mrr < start_mrr THEN start_mrr - end_mrr ELSE 0 END) AS contraction_mrr,
        SUM(CASE WHEN end_mrr = 0 THEN start_mrr ELSE 0 END)                                   AS churn_mrr,
        SUM(end_mrr)                                                                            AS end_mrr,
        ROUND(SUM(end_mrr) / NULLIF(SUM(start_mrr), 0), 4)                                      AS ndr,
        ROUND(SUM(LEAST(end_mrr, start_mrr)) / NULLIF(SUM(start_mrr), 0), 4)                    AS grr
    FROM expanded
    GROUP BY segment_group
),
renewal_events AS (
    SELECT segment AS segment_group, customer_type, mrr_delta
    FROM fct_subscriptions
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
        CAST(COUNT(*) AS BIGINT)                                    AS base_customers,  -- renewal-event count, not customer count
        CAST(NULL AS DOUBLE)                                        AS start_mrr,
        SUM(CASE WHEN mrr_delta > 0 THEN mrr_delta ELSE 0 END)      AS expansion_mrr,
        SUM(CASE WHEN mrr_delta < 0 THEN -mrr_delta ELSE 0 END)     AS contraction_mrr,
        CAST(NULL AS DOUBLE)                                        AS churn_mrr,
        CAST(NULL AS DOUBLE)                                        AS end_mrr,
        CAST(NULL AS DOUBLE)                                        AS ndr,
        CAST(NULL AS DOUBLE)                                        AS grr
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
    CASE segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'B2B' THEN 4 WHEN 'Total' THEN 5 END
