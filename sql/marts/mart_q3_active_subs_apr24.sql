-- mart_q3_active_subs_apr24: Q3 -- active subscriptions at 2024-04-30 by segment x plan_type,
-- with segment/plan/grand totals. Per M-02. Grand total must equal 1,941.
WITH active AS (
    SELECT s.subscription_id, u.segment, s.plan_type
    FROM stg_subscriptions s
    JOIN stg_users u ON u.user_id = s.user_id
    WHERE s.start_date <= DATE '2024-04-30' AND DATE '2024-04-30' < s.end_date
),
cell AS (
    SELECT segment, plan_type, COUNT(*) AS active_subs
    FROM active
    GROUP BY segment, plan_type
),
segment_total AS (
    SELECT segment, 'Total' AS plan_type, COUNT(*) AS active_subs
    FROM active
    GROUP BY segment
),
plan_total AS (
    SELECT 'Total' AS segment, plan_type, COUNT(*) AS active_subs
    FROM active
    GROUP BY plan_type
),
grand_total AS (
    SELECT 'Total' AS segment, 'Total' AS plan_type, COUNT(*) AS active_subs
    FROM active
),
unioned AS (
    SELECT * FROM cell
    UNION ALL SELECT * FROM segment_total
    UNION ALL SELECT * FROM plan_total
    UNION ALL SELECT * FROM grand_total
)
SELECT * FROM unioned
ORDER BY
    CASE segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'Total' THEN 4 END,
    CASE plan_type WHEN 'monthly' THEN 1 WHEN 'annual' THEN 2 WHEN 'Total' THEN 3 END
