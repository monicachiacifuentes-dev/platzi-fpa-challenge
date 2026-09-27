-- PASS if this returns zero rows: primary keys must be unique
SELECT 'stg_users.user_id' AS key_name, user_id AS key_value, COUNT(*) AS n
FROM stg_users GROUP BY user_id HAVING COUNT(*) > 1
UNION ALL
SELECT 'stg_subscriptions.subscription_id', subscription_id, COUNT(*)
FROM stg_subscriptions GROUP BY subscription_id HAVING COUNT(*) > 1
UNION ALL
SELECT 'stg_engagement.subscription_id', subscription_id, COUNT(*)
FROM stg_engagement GROUP BY subscription_id HAVING COUNT(*) > 1
UNION ALL
SELECT 'fct_subscriptions.subscription_id', subscription_id, COUNT(*)
FROM fct_subscriptions GROUP BY subscription_id HAVING COUNT(*) > 1
UNION ALL
SELECT 'fct_customer_mrr_monthly.user_id_month_end', user_id || '|' || CAST(month_end AS VARCHAR), COUNT(*)
FROM fct_customer_mrr_monthly GROUP BY user_id, month_end HAVING COUNT(*) > 1
