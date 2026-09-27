-- mart_a3_01_t12m_decomposition: T12M NDR/GRR decomposition (M-08..M-10) by segment,
-- B2B roll-up and Total. Base = customers active on 2023-04-30 (M-08), evaluated at
-- 2024-04-30. Adds $ and % of start-MRR for every bridge step, plus the customer
-- count behind each movement category (expansion / contraction / churn / flat).
-- Ties exactly to sql/marts/mart_q4_ndr_t12m.sql (method='M08_M09_M10'); see
-- sql/tests/test_a3_ties_mart_q4.sql.
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
    SELECT
        b.user_id, b.segment, b.customer_type, b.start_mrr,
        COALESCE(e.end_mrr, 0) AS end_mrr
    FROM base b
    LEFT JOIN end_mrr e ON e.user_id = b.user_id
),
categorized AS (
    SELECT *,
        CASE
            WHEN end_mrr = 0 THEN 'churn'
            WHEN end_mrr > start_mrr THEN 'expansion'
            WHEN end_mrr < start_mrr THEN 'contraction'
            ELSE 'flat'
        END AS movement
    FROM joined
),
expanded AS (
    SELECT segment AS segment_group, start_mrr, end_mrr, movement FROM categorized
    UNION ALL
    SELECT 'B2B', start_mrr, end_mrr, movement FROM categorized WHERE customer_type = 'B2B'
    UNION ALL
    SELECT 'Total', start_mrr, end_mrr, movement FROM categorized
)
SELECT
    segment_group AS segment,
    CAST(COUNT(*) AS BIGINT)                                              AS base_customers,
    CAST(SUM(CASE WHEN movement = 'expansion'   THEN 1 ELSE 0 END) AS BIGINT) AS n_expansion,
    CAST(SUM(CASE WHEN movement = 'contraction' THEN 1 ELSE 0 END) AS BIGINT) AS n_contraction,
    CAST(SUM(CASE WHEN movement = 'churn'       THEN 1 ELSE 0 END) AS BIGINT) AS n_churn,
    CAST(SUM(CASE WHEN movement = 'flat'        THEN 1 ELSE 0 END) AS BIGINT) AS n_flat,
    SUM(start_mrr)                                                        AS start_mrr,
    SUM(CASE WHEN movement = 'expansion'   THEN end_mrr - start_mrr ELSE 0 END) AS expansion_mrr,
    SUM(CASE WHEN movement = 'contraction' THEN start_mrr - end_mrr ELSE 0 END) AS contraction_mrr,
    SUM(CASE WHEN movement = 'churn'       THEN start_mrr ELSE 0 END)          AS churn_mrr,
    SUM(end_mrr)                                                           AS end_mrr,
    100.0                                                                  AS start_pct,
    ROUND(100.0 * SUM(CASE WHEN movement = 'expansion'   THEN end_mrr - start_mrr ELSE 0 END) / NULLIF(SUM(start_mrr), 0), 2) AS expansion_pct_of_start,
    ROUND(100.0 * SUM(CASE WHEN movement = 'contraction' THEN start_mrr - end_mrr ELSE 0 END) / NULLIF(SUM(start_mrr), 0), 2) AS contraction_pct_of_start,
    ROUND(100.0 * SUM(CASE WHEN movement = 'churn'       THEN start_mrr ELSE 0 END)          / NULLIF(SUM(start_mrr), 0), 2) AS churn_pct_of_start,
    ROUND(100.0 * SUM(end_mrr) / NULLIF(SUM(start_mrr), 0), 2)             AS end_pct_of_start,
    ROUND(SUM(end_mrr) / NULLIF(SUM(start_mrr), 0), 4)                     AS ndr,
    ROUND(SUM(LEAST(end_mrr, start_mrr)) / NULLIF(SUM(start_mrr), 0), 4)   AS grr
FROM expanded
GROUP BY segment_group
ORDER BY CASE segment_group WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'B2B' THEN 4 WHEN 'Total' THEN 5 END
