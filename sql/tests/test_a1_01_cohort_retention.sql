-- PASS if zero rows: at month_k=0 logo_retention and dollar_retention must always be exactly 1.0
-- (every cohort member's first subscription starts on signup_date -- verified data fact),
-- and customers_start/mrr_start must be positive for every cohort/segment_group.
SELECT *
FROM mart_a1_01_cohort_retention
WHERE month_k = 0
  AND (ABS(logo_retention - 1.0) > 0.0001 OR ABS(dollar_retention - 1.0) > 0.0001
       OR customers_start <= 0 OR mrr_start <= 0)
