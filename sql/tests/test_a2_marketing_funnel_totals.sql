-- PASS if empty: marketing_spend.new_users_acquired totals (T16M, from
-- mart_a2_03) must match Docs/Datasets.md's marketing_spend.csv profile.
WITH totals AS (
    SELECT segment, SUM(new_users_acquired_marketing) AS n
    FROM mart_a2_03_funnel_segment_monthly
    GROUP BY segment
)
SELECT * FROM totals
WHERE (segment = 'B2C' AND n <> 21573)
   OR (segment = 'SMB' AND n <> 695)
   OR (segment = 'Enterprise' AND n <> 82)
