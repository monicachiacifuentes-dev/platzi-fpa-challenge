-- stg_subscriptions: typed, trimmed subscription periods (one row per billing period)
SELECT
    trim(subscription_id)  AS subscription_id,
    trim(user_id)           AS user_id,
    trim(plan_type)         AS plan_type,
    CAST(start_date AS DATE) AS start_date,
    CAST(end_date AS DATE)   AS end_date,
    CAST(mrr AS DOUBLE)      AS mrr,
    trim(status)             AS status
FROM raw_subscriptions
