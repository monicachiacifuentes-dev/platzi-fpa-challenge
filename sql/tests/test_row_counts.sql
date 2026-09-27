-- PASS if this returns zero rows: staging row counts must match Docs/Datasets.md
SELECT * FROM (
    SELECT 'users' AS table_name, COUNT(*) AS actual, 2695 AS expected FROM stg_users
    UNION ALL
    SELECT 'subscriptions', COUNT(*), 9683 FROM stg_subscriptions
    UNION ALL
    SELECT 'payments', COUNT(*), 17209 FROM stg_payments
    UNION ALL
    SELECT 'engagement', COUNT(*), 9683 FROM stg_engagement
    UNION ALL
    SELECT 'marketing_spend', COUNT(*), 144 FROM stg_marketing_spend
    UNION ALL
    SELECT 'support_costs', COUNT(*), 64 FROM stg_support_costs
) t
WHERE actual <> expected
