-- mart_a2_04_funnel_channel_total: WP21 -- cost per signup by channel, for B2C
-- and SMB only (paying customers can't be split by channel -- no channel field
-- on users.csv -- so this stops at the marketing funnel metric, per the brief).
-- Two periods: T16M (2023-01 .. 2024-04, full history) and T6M (2023-11 .. 2024-04).
WITH base AS (
    SELECT month, segment, channel, spend, new_users_acquired
    FROM stg_marketing_spend
    WHERE segment IN ('B2C', 'SMB')
),
periods AS (
    SELECT 'T16M' AS period, month, segment, channel, spend, new_users_acquired FROM base
    UNION ALL
    SELECT 'T6M' AS period, month, segment, channel, spend, new_users_acquired FROM base
    WHERE month BETWEEN DATE '2023-11-01' AND DATE '2024-04-01'
)
SELECT
    period,
    segment,
    channel,
    SUM(spend)               AS spend,
    SUM(new_users_acquired)  AS new_users_acquired,
    ROUND(SUM(spend) / NULLIF(SUM(new_users_acquired), 0), 2) AS cost_per_signup
FROM periods
GROUP BY period, segment, channel
ORDER BY period DESC, segment, cost_per_signup
