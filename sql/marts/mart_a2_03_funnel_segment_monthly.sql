-- mart_a2_03_funnel_segment_monthly: WP21 -- D-06 funnel view.
-- marketing_spend.new_users_acquired is reported ONLY as a funnel metric here
-- (cost per signup, signup->paid conversion), NOT as the CAC denominator
-- (see mart_a2_01 / D-06). Joins mart_a2_02 (marketing, segment-native rows
-- only: B2C/SMB/Enterprise) with mart_a2_01 (paying customers from users.csv).
SELECT
    m.month,
    m.segment,
    m.marketing_spend,
    m.new_users_acquired_marketing,
    p.new_paying_customers,
    ROUND(m.marketing_spend / NULLIF(m.new_users_acquired_marketing, 0), 2) AS cost_per_signup,
    ROUND(p.new_paying_customers::DOUBLE / NULLIF(m.new_users_acquired_marketing, 0), 4) AS signup_to_paid_conversion
FROM mart_a2_02_marketing_spend_segment_monthly m
LEFT JOIN mart_a2_01_new_paying_customers p
    ON p.month = m.month AND p.segment = m.segment
WHERE m.segment IN ('B2C', 'SMB', 'Enterprise', 'Total')
ORDER BY m.month,
    CASE m.segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'Total' THEN 5 END
