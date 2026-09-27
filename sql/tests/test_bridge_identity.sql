-- PASS if this returns zero rows: MRR bridge identity must hold every month x segment
-- opening + new + expansion - contraction - churn = closing (tolerance 0.01)
SELECT
    month_end,
    segment,
    opening_mrr, new_mrr, expansion_mrr, contraction_mrr, churn_mrr, closing_mrr,
    (COALESCE(opening_mrr, 0) + COALESCE(new_mrr, 0) + COALESCE(expansion_mrr, 0)
     - COALESCE(contraction_mrr, 0) - COALESCE(churn_mrr, 0) - closing_mrr) AS diff
FROM mart_mrr_bridge
WHERE ABS(COALESCE(opening_mrr, 0) + COALESCE(new_mrr, 0) + COALESCE(expansion_mrr, 0)
          - COALESCE(contraction_mrr, 0) - COALESCE(churn_mrr, 0) - closing_mrr) > 0.01
