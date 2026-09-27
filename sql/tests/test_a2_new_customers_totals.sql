-- PASS if empty: mart_a2_01 segment totals (summed across all 16 months) must
-- reconcile to the known users.csv counts (Docs/Datasets.md) and B2B = SMB+Enterprise.
WITH totals AS (
    SELECT segment, SUM(new_paying_customers) AS n
    FROM mart_a2_01_new_paying_customers
    GROUP BY segment
)
SELECT * FROM totals
WHERE (segment = 'B2C' AND n <> 2225)
   OR (segment = 'SMB' AND n <> 361)
   OR (segment = 'Enterprise' AND n <> 109)
   OR (segment = 'B2B' AND n <> 470)
   OR (segment = 'Total' AND n <> 2695)
