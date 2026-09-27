-- PASS if zero rows: mart_a1_06 must cover every mart_a1_05 row exactly once, prob_churn
-- must be a valid probability, risk_tier must match the stated cutoffs (High >= 0.50,
-- Medium >= 0.25, else Low), and mrr_at_risk must equal mrr * prob_churn.
SELECT 'row_count' AS check_name, COUNT(*) AS actual,
       (SELECT COUNT(*) FROM mart_a1_05_may24_population) AS expected
FROM mart_a1_06_may24_churn_risk
HAVING COUNT(*) <> (SELECT COUNT(*) FROM mart_a1_05_may24_population)

UNION ALL
SELECT 'prob_out_of_range', COUNT(*), 0
FROM mart_a1_06_may24_churn_risk
WHERE prob_churn < 0 OR prob_churn > 1
HAVING COUNT(*) <> 0

UNION ALL
SELECT 'tier_mismatch', COUNT(*), 0
FROM mart_a1_06_may24_churn_risk
WHERE risk_tier <> CASE WHEN prob_churn >= 0.50 THEN 'High'
                        WHEN prob_churn >= 0.25 THEN 'Medium'
                        ELSE 'Low' END
HAVING COUNT(*) <> 0

UNION ALL
SELECT 'mrr_at_risk_mismatch', COUNT(*), 0
FROM mart_a1_06_may24_churn_risk
WHERE ABS(mrr_at_risk - mrr * prob_churn) > 0.01
HAVING COUNT(*) <> 0
