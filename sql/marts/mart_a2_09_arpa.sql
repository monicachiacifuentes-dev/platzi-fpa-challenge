-- mart_a2_09_arpa: WP21 -- ARPA = revenue (MRR) / active customers, by segment,
-- as an Apr-24 snapshot and a T6M (2023-11..2024-04) simple average of the
-- monthly ARPA values.
WITH monthly AS (
    SELECT month, segment, revenue, active_customers,
           ROUND(revenue / NULLIF(active_customers, 0), 2) AS arpa
    FROM mart_a2_08_gm_monthly
),
apr24 AS (
    SELECT segment, 'Apr-24' AS period, arpa
    FROM monthly WHERE month = DATE '2024-04-30'
),
t6m AS (
    SELECT segment, 'T6M_avg' AS period, ROUND(AVG(arpa), 2) AS arpa
    FROM monthly
    WHERE month BETWEEN DATE '2023-11-30' AND DATE '2024-04-30'
    GROUP BY segment
),
combined AS (
    SELECT * FROM apr24
    UNION ALL
    SELECT * FROM t6m
)
SELECT * FROM combined
ORDER BY
    CASE segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'B2B' THEN 4 WHEN 'Total' THEN 5 END,
    period
