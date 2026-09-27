-- PASS if zero rows: mart_a1_03 row count must equal renewed+churned subscriptions (7,742 =
-- 6,988 + 754, per Docs/Datasets.md), churned flag must match status exactly, and every row
-- must land in model_split 'train' or 'test' (no 'other' -- every renewed/churned period ends
-- on or before the 2024-04-30 snapshot).
SELECT 'row_count' AS check_name, COUNT(*) AS actual, 7742 AS expected
FROM mart_a1_03_churn_indicators_base
HAVING COUNT(*) <> 7742

UNION ALL
SELECT 'churned_flag_mismatch', COUNT(*), 0
FROM mart_a1_03_churn_indicators_base
WHERE (status = 'churned') <> (churned = 1)
HAVING COUNT(*) <> 0

UNION ALL
SELECT 'bad_split', COUNT(*), 0
FROM mart_a1_03_churn_indicators_base
WHERE model_split = 'other'
HAVING COUNT(*) <> 0
