-- mart_a3_04_t6m_waterfall_long: long format (segment, step, step_order, amount) of
-- the T6M bridge in mart_a3_03_t6m_decomposition, ready for a Looker Studio
-- waterfall chart. Same convention as mart_a3_02_t12m_waterfall_long.
SELECT segment, 'Start MRR'   AS step, 1 AS step_order, start_mrr       AS amount FROM mart_a3_03_t6m_decomposition
UNION ALL
SELECT segment, 'Churn',              2,               -churn_mrr              FROM mart_a3_03_t6m_decomposition
UNION ALL
SELECT segment, 'Contraction',        3,               -contraction_mrr        FROM mart_a3_03_t6m_decomposition
UNION ALL
SELECT segment, 'Expansion',          4,                expansion_mrr          FROM mart_a3_03_t6m_decomposition
UNION ALL
SELECT segment, 'End MRR',            5,                end_mrr                FROM mart_a3_03_t6m_decomposition
ORDER BY segment, step_order
