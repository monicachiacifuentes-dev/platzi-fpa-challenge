-- mart_mrr_bridge: month x segment MRR bridge.
-- Identity (tested in sql/tests/test_bridge_identity.sql):
--   opening_mrr + new_mrr + expansion_mrr - contraction_mrr - churn_mrr = closing_mrr
SELECT
    month_end,
    segment,
    SUM(COALESCE(prev_mrr, 0))                                              AS opening_mrr,
    SUM(CASE WHEN movement = 'new'         THEN mrr END)                    AS new_mrr,
    SUM(CASE WHEN movement = 'expansion'   THEN mrr - prev_mrr END)         AS expansion_mrr,
    SUM(CASE WHEN movement = 'contraction' THEN prev_mrr - mrr END)         AS contraction_mrr,
    SUM(CASE WHEN movement = 'churn'       THEN prev_mrr END)               AS churn_mrr,
    SUM(mrr)                                                                AS closing_mrr,
    SUM(CASE WHEN mrr > 0 THEN 1 ELSE 0 END)                                AS active_customers
FROM fct_customer_mrr_monthly
GROUP BY month_end, segment

UNION ALL

SELECT
    month_end,
    'Total' AS segment,
    SUM(COALESCE(prev_mrr, 0))                                              AS opening_mrr,
    SUM(CASE WHEN movement = 'new'         THEN mrr END)                    AS new_mrr,
    SUM(CASE WHEN movement = 'expansion'   THEN mrr - prev_mrr END)         AS expansion_mrr,
    SUM(CASE WHEN movement = 'contraction' THEN prev_mrr - mrr END)         AS contraction_mrr,
    SUM(CASE WHEN movement = 'churn'       THEN prev_mrr END)               AS churn_mrr,
    SUM(mrr)                                                                AS closing_mrr,
    SUM(CASE WHEN mrr > 0 THEN 1 ELSE 0 END)                                AS active_customers
FROM fct_customer_mrr_monthly
GROUP BY month_end

UNION ALL

SELECT
    month_end,
    'B2B' AS segment,
    SUM(COALESCE(prev_mrr, 0))                                              AS opening_mrr,
    SUM(CASE WHEN movement = 'new'         THEN mrr END)                    AS new_mrr,
    SUM(CASE WHEN movement = 'expansion'   THEN mrr - prev_mrr END)         AS expansion_mrr,
    SUM(CASE WHEN movement = 'contraction' THEN prev_mrr - mrr END)         AS contraction_mrr,
    SUM(CASE WHEN movement = 'churn'       THEN prev_mrr END)               AS churn_mrr,
    SUM(mrr)                                                                AS closing_mrr,
    SUM(CASE WHEN mrr > 0 THEN 1 ELSE 0 END)                                AS active_customers
FROM fct_customer_mrr_monthly
WHERE customer_type = 'B2B'
GROUP BY month_end
