-- WP31: at the M12 horizon (Apr-25), Bull MRR >= Base MRR >= Bear MRR for
-- every segment rollup (retention strategies succeeding + trend acquisition
-- can only help; churn stress + acquisition haircut + halved expansion can
-- only hurt). Returns violations -> PASS means 0 rows.
WITH m12 AS (
    SELECT scenario, segment, closing_mrr
    FROM mart_s_02_projection_monthly
    WHERE month_index = 12 AND plan_type = 'ALL'
),
piv AS (
    SELECT
        segment,
        MAX(CASE WHEN scenario = 'base' THEN closing_mrr END) AS base_mrr,
        MAX(CASE WHEN scenario = 'bull' THEN closing_mrr END) AS bull_mrr,
        MAX(CASE WHEN scenario = 'bear' THEN closing_mrr END) AS bear_mrr
    FROM m12
    GROUP BY segment
)
SELECT * FROM piv
WHERE bull_mrr < base_mrr - 0.01 OR base_mrr < bear_mrr - 0.01
