-- stg_engagement: typed engagement per subscription period (1:1 with subscriptions)
SELECT
    trim(user_id)                AS user_id,
    trim(subscription_id)        AS subscription_id,
    CAST(active_days AS INTEGER) AS active_days,
    CAST(courses_seen AS INTEGER) AS courses_seen,
    CAST(materials_seen AS INTEGER) AS materials_seen,
    trim(favorite_category)      AS favorite_category
FROM raw_engagement
