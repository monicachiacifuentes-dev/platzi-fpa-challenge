-- PASS if this returns zero rows: NDR bridge identity, GRR <= 1, NDR >= GRR (M-08..M-10)
SELECT *
FROM mart_q4_ndr_t12m
WHERE method = 'M08_M09_M10'
  AND (
        ABS(COALESCE(start_mrr, 0) + COALESCE(expansion_mrr, 0) - COALESCE(contraction_mrr, 0)
            - COALESCE(churn_mrr, 0) - COALESCE(end_mrr, 0)) > 0.01
        OR grr > 1.0001
        OR ndr < grr - 0.0001
      )
