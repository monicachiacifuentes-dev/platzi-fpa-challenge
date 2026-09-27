-- PASS if zero rows: Total customers_active/mrr_active must equal B2C + B2B at every
-- (cohort_month, month_k) -- cross-check that the segment_group UNION ALL in
-- mart_a1_01_cohort_retention didn't double-count or drop rows.
WITH piv AS (
    SELECT
        cohort_month, month_k,
        SUM(CASE WHEN segment_group = 'Total' THEN customers_active END) AS total_cust,
        SUM(CASE WHEN segment_group = 'B2C'   THEN customers_active END) AS b2c_cust,
        SUM(CASE WHEN segment_group = 'B2B'   THEN customers_active END) AS b2b_cust,
        SUM(CASE WHEN segment_group = 'Total' THEN mrr_active END) AS total_mrr,
        SUM(CASE WHEN segment_group = 'B2C'   THEN mrr_active END) AS b2c_mrr,
        SUM(CASE WHEN segment_group = 'B2B'   THEN mrr_active END) AS b2b_mrr
    FROM mart_a1_01_cohort_retention
    GROUP BY 1, 2
)
SELECT *
FROM piv
WHERE total_cust <> COALESCE(b2c_cust, 0) + COALESCE(b2b_cust, 0)
   OR ABS(total_mrr - (COALESCE(b2c_mrr, 0) + COALESCE(b2b_mrr, 0))) > 0.01
