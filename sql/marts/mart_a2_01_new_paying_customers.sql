-- mart_a2_01_new_paying_customers: WP21 (A2 Unit Economics) -- CAC denominator (D-06 base).
-- New PAYING customers per calendar month, by segment (+ B2B roll-up + Total),
-- counted from users.csv signup_date (M-05: 1 user_id = 1 customer). This is the
-- CAC denominator base per D-06 (NOT marketing_spend.new_users_acquired, which is
-- reported separately as a funnel metric in mart_a2_03/04).
WITH base AS (
    SELECT
        CAST(date_trunc('month', signup_date) AS DATE) AS month,
        segment,
        customer_type,
        user_id
    FROM stg_users
),
expanded AS (
    SELECT month, segment AS segment_group, user_id FROM base
    UNION ALL
    SELECT month, 'B2B' AS segment_group, user_id FROM base WHERE customer_type = 'B2B'
    UNION ALL
    SELECT month, 'Total' AS segment_group, user_id FROM base
)
SELECT
    month,
    segment_group AS segment,
    COUNT(*) AS new_paying_customers
FROM expanded
GROUP BY month, segment_group
ORDER BY month,
    CASE segment_group WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'B2B' THEN 4 WHEN 'Total' THEN 5 END
