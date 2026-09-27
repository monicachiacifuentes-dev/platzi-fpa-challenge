-- mart_a3_02_t12m_waterfall_long: long format (segment, step, step_order, amount) of
-- the T12M bridge in mart_a3_01_t12m_decomposition, ready for a Looker Studio
-- waterfall chart. amount is the bar's own plotted value: Start/End are level bars
-- (positive), Churn/Contraction are negative deltas, Expansion is a positive delta,
-- so for every segment: Start + (-Churn) + (-Contraction) + Expansion = End.
SELECT segment, 'Start MRR'   AS step, 1 AS step_order, start_mrr       AS amount FROM mart_a3_01_t12m_decomposition
UNION ALL
SELECT segment, 'Churn',              2,               -churn_mrr              FROM mart_a3_01_t12m_decomposition
UNION ALL
SELECT segment, 'Contraction',        3,               -contraction_mrr        FROM mart_a3_01_t12m_decomposition
UNION ALL
SELECT segment, 'Expansion',          4,                expansion_mrr          FROM mart_a3_01_t12m_decomposition
UNION ALL
SELECT segment, 'End MRR',            5,                end_mrr                FROM mart_a3_01_t12m_decomposition
ORDER BY segment, step_order
