-- mart_q2_retention_q1_24: Q2 -- Q1 2024 retention.
-- method = 'M06_primary'   : renewal-event basis, end_date in [2024-01-01, 2024-03-31].
--                             logo_rate = renewed / (renewed + churned); split = 'all' | 'monthly' | 'annual'.
--                             dollar_rate = sum(next_mrr of renewed) / sum(mrr of all ended).
-- method = 'M07_crosscheck': customer-snapshot basis. n_ended column holds the
--                             base (customers active on 2023-12-31); logo_rate = still active on 2024-03-31 / base.
WITH ended AS (
    SELECT *
    FROM fct_subscriptions
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
        CAST(SUM(CASE WHEN status = 'renewed' THEN 1 ELSE 0 END) AS BIGINT) AS n_renewed,
        CAST(SUM(CASE WHEN status = 'churned' THEN 1 ELSE 0 END) AS BIGINT) AS n_churned,
        CAST(COUNT(*) AS BIGINT)                                            AS n_ended,
        ROUND(1.0 * SUM(CASE WHEN status = 'renewed' THEN 1 ELSE 0 END) / COUNT(*), 4) AS logo_rate,
        CAST(SUM(CASE WHEN status = 'renewed' THEN next_mrr ELSE 0 END) AS DOUBLE)     AS dollar_numerator,
        CAST(SUM(mrr) AS DOUBLE)                                                       AS dollar_denominator,
        ROUND(SUM(CASE WHEN status = 'renewed' THEN next_mrr ELSE 0 END) / SUM(mrr), 4) AS dollar_rate
    FROM ended_expanded
    GROUP BY segment_group
),
m06_by_plan AS (
    SELECT
        segment_group AS segment,
        plan_type      AS split,
        'M06_primary'  AS method,
        CAST(SUM(CASE WHEN status = 'renewed' THEN 1 ELSE 0 END) AS BIGINT) AS n_renewed,
        CAST(SUM(CASE WHEN status = 'churned' THEN 1 ELSE 0 END) AS BIGINT) AS n_churned,
        CAST(COUNT(*) AS BIGINT)                                            AS n_ended,
        ROUND(1.0 * SUM(CASE WHEN status = 'renewed' THEN 1 ELSE 0 END) / COUNT(*), 4) AS logo_rate,
        CAST(SUM(CASE WHEN status = 'renewed' THEN next_mrr ELSE 0 END) AS DOUBLE)     AS dollar_numerator,
        CAST(SUM(mrr) AS DOUBLE)                                                       AS dollar_denominator,
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
        CAST(NULL AS BIGINT) AS n_renewed,
        CAST(NULL AS BIGINT) AS n_churned,
        CAST(COUNT(DISTINCT ad.user_id) AS BIGINT) AS n_ended,  -- base: active on 2023-12-31
        ROUND(1.0 * COUNT(DISTINCT CASE WHEN am.user_id IS NOT NULL THEN ad.user_id END) / COUNT(DISTINCT ad.user_id), 4) AS logo_rate,
        CAST(NULL AS DOUBLE) AS dollar_numerator,
        CAST(NULL AS DOUBLE) AS dollar_denominator,
        CAST(NULL AS DOUBLE) AS dollar_rate
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
    split
