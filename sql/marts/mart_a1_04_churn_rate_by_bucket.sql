-- mart_a1_04_churn_rate_by_bucket: churn rate (of periods with a known outcome) by bucket,
-- one dimension at a time, long format for a Looker Studio bar chart grid. Whole population
-- (train+test), descriptive only -- the model itself is fit separately (see Python script /
-- results.md), this mart is the "why" behind the feature choices.
SELECT 'active_days' AS dimension, active_days_bucket AS bucket,
       CASE active_days_bucket
           WHEN '0-5' THEN 1 WHEN '6-10' THEN 2 WHEN '11-15' THEN 3
           WHEN '16-20' THEN 4 WHEN '21-25' THEN 5 ELSE 6 END AS sort_order,
       COUNT(*) AS n, SUM(churned) AS churned, SUM(churned)::DOUBLE / COUNT(*) AS churn_rate
FROM mart_a1_03_churn_indicators_base GROUP BY 1, 2, 3

UNION ALL
SELECT 'courses_seen', courses_seen_bucket,
       CASE courses_seen_bucket
           WHEN '0-2' THEN 1 WHEN '3-5' THEN 2 WHEN '6-8' THEN 3
           WHEN '9-11' THEN 4 ELSE 5 END,
       COUNT(*), SUM(churned), SUM(churned)::DOUBLE / COUNT(*)
FROM mart_a1_03_churn_indicators_base GROUP BY 1, 2, 3

UNION ALL
SELECT 'materials_seen', materials_seen_bucket,
       CASE materials_seen_bucket
           WHEN '0-9' THEN 1 WHEN '10-19' THEN 2 WHEN '20-29' THEN 3
           WHEN '30-49' THEN 4 ELSE 5 END,
       COUNT(*), SUM(churned), SUM(churned)::DOUBLE / COUNT(*)
FROM mart_a1_03_churn_indicators_base GROUP BY 1, 2, 3

UNION ALL
SELECT 'tenure_periods', tenure_bucket,
       CASE tenure_bucket
           WHEN '1' THEN 1 WHEN '2' THEN 2 WHEN '3' THEN 3
           WHEN '4-6' THEN 4 ELSE 5 END,
       COUNT(*), SUM(churned), SUM(churned)::DOUBLE / COUNT(*)
FROM mart_a1_03_churn_indicators_base GROUP BY 1, 2, 3

UNION ALL
SELECT 'plan_type', plan_type,
       CASE plan_type WHEN 'monthly' THEN 1 ELSE 2 END,
       COUNT(*), SUM(churned), SUM(churned)::DOUBLE / COUNT(*)
FROM mart_a1_03_churn_indicators_base GROUP BY 1, 2, 3

UNION ALL
SELECT 'segment', segment,
       CASE segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 ELSE 3 END,
       COUNT(*), SUM(churned), SUM(churned)::DOUBLE / COUNT(*)
FROM mart_a1_03_churn_indicators_base GROUP BY 1, 2, 3

UNION ALL
SELECT 'favorite_category', favorite_category, 1,
       COUNT(*), SUM(churned), SUM(churned)::DOUBLE / COUNT(*)
FROM mart_a1_03_churn_indicators_base GROUP BY 1, 2, 3

UNION ALL
SELECT 'renewal_change_at_prev_renewal', renewal_change_bucket,
       CASE renewal_change_bucket
           WHEN 'no_prior_renewal' THEN 1 WHEN 'contraction' THEN 2
           WHEN 'flat' THEN 3 ELSE 4 END,
       COUNT(*), SUM(churned), SUM(churned)::DOUBLE / COUNT(*)
FROM mart_a1_03_churn_indicators_base GROUP BY 1, 2, 3

UNION ALL
SELECT 'main_gateway', COALESCE(main_gateway, 'Unknown (no payment)'), 1,
       COUNT(*), SUM(churned), SUM(churned)::DOUBLE / COUNT(*)
FROM mart_a1_03_churn_indicators_base GROUP BY 1, 2, 3

ORDER BY 1, 3
