-- PASS if zero rows: monthly NDR series identity (start + expansion - contraction -
-- churn = end), GRR <= 1, NDR >= GRR, for every month x segment (mart_a3_05).
SELECT *
FROM mart_a3_05_monthly_ndr_series
WHERE ABS(start_mrr + expansion_mrr - contraction_mrr - churn_mrr - end_mrr) > 0.01
   OR grr > 1.0001
   OR ndr < grr - 0.0001
