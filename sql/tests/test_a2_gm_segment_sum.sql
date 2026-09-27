-- PASS if empty: B2C + SMB + Enterprise revenue and active_customers must sum
-- exactly to the Total row, every month, in mart_a2_08_gm_monthly.
WITH parts AS (
    SELECT month, SUM(revenue) AS sum_revenue, SUM(active_customers) AS sum_active
    FROM mart_a2_08_gm_monthly
    WHERE segment IN ('B2C', 'SMB', 'Enterprise')
    GROUP BY month
),
tot AS (
    SELECT month, revenue, active_customers
    FROM mart_a2_08_gm_monthly
    WHERE segment = 'Total'
)
SELECT p.*, t.revenue AS total_revenue, t.active_customers AS total_active
FROM parts p
JOIN tot t ON t.month = p.month
WHERE ABS(p.sum_revenue - t.revenue) > 0.05
   OR p.sum_active <> t.active_customers
