-- PASS if this returns zero rows: no orphan foreign keys between staging tables
SELECT 'subscriptions.user_id not in users' AS check_name, COUNT(*) AS n
FROM stg_subscriptions s LEFT JOIN stg_users u ON u.user_id = s.user_id
WHERE u.user_id IS NULL
HAVING COUNT(*) > 0
UNION ALL
SELECT 'engagement.subscription_id not in subscriptions', COUNT(*)
FROM stg_engagement e LEFT JOIN stg_subscriptions s ON s.subscription_id = e.subscription_id
WHERE s.subscription_id IS NULL
HAVING COUNT(*) > 0
UNION ALL
SELECT 'engagement.user_id mismatch vs subscriptions.user_id', COUNT(*)
FROM stg_engagement e
JOIN stg_subscriptions s ON s.subscription_id = e.subscription_id
WHERE e.user_id <> s.user_id
HAVING COUNT(*) > 0
