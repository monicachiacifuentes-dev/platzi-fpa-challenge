-- WP31: MRR bridge identity must hold every month, every scenario, every
-- segment/plan_type row of the projection engine:
--   opening + new + expansion - contraction - churn - migration_out + migration_in = closing
-- Returns offending rows -> PASS means 0 rows.
SELECT scenario, month_index, segment, plan_type,
       opening_mrr, new_mrr, expansion_mrr, contraction_mrr, churn_mrr,
       migration_out_mrr, migration_in_mrr, closing_mrr,
       (opening_mrr + new_mrr + expansion_mrr - contraction_mrr - churn_mrr
        - migration_out_mrr + migration_in_mrr) AS reconstructed_closing
FROM mart_s_02_projection_monthly
WHERE ABS(
    opening_mrr + new_mrr + expansion_mrr - contraction_mrr - churn_mrr
    - migration_out_mrr + migration_in_mrr - closing_mrr
) > 0.01
