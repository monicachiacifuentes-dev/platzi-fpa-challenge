-- PASS if zero rows: mart_a1_05 (D-08 May-2024 at-risk population) must match the independent
-- count/MRR of active subscriptions ending in May 2024 (1,024 rows, $87,828.88 MRR).
SELECT 'row_count' AS check_name, COUNT(*) AS actual, 1024 AS expected
FROM mart_a1_05_may24_population
HAVING COUNT(*) <> 1024

UNION ALL
SELECT 'mrr_total', ROUND(SUM(mrr), 2), 87828.88
FROM mart_a1_05_may24_population
HAVING ABS(ROUND(SUM(mrr), 2) - 87828.88) > 0.01
