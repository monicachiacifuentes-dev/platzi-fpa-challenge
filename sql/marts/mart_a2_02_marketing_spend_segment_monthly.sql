-- mart_a2_02_marketing_spend_segment_monthly: WP21 -- total marketing spend per
-- month by segment (all channels included, per the brief: "Sales Team" line is
-- Enterprise-only and is included; Content and Organic included too), plus a
-- B2B roll-up and a Total row.
WITH base AS (
    SELECT month, segment, spend, new_users_acquired
    FROM stg_marketing_spend
),
expanded AS (
    SELECT month, segment AS segment_group, spend, new_users_acquired FROM base
    UNION ALL
    SELECT month, 'B2B' AS segment_group, spend, new_users_acquired FROM base WHERE segment IN ('SMB', 'Enterprise')
    UNION ALL
    SELECT month, 'Total' AS segment_group, spend, new_users_acquired FROM base
)
SELECT
    month,
    segment_group AS segment,
    SUM(spend)               AS marketing_spend,
    SUM(new_users_acquired)  AS new_users_acquired_marketing
FROM expanded
GROUP BY month, segment_group
ORDER BY month,
    CASE segment_group WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'B2B' THEN 4 WHEN 'Total' THEN 5 END
