-- PASS if zero rows: T6M decomposition identity (start + expansion - contraction -
-- churn = end), GRR <= 1, NDR >= GRR, and customer-count identity (mart_a3_03).
SELECT *
FROM mart_a3_03_t6m_decomposition
WHERE ABS(start_mrr + expansion_mrr - contraction_mrr - churn_mrr - end_mrr) > 0.01
   OR grr > 1.0001
   OR ndr < grr - 0.0001
   OR (n_expansion + n_contraction + n_churn + n_flat) <> base_customers
