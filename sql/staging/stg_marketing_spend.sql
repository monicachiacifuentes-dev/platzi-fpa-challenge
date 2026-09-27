-- stg_marketing_spend: month (YYYY-MM string) -> DATE of first day of month
SELECT
    CAST(trim(CAST(month AS VARCHAR)) || '-01' AS DATE) AS month,
    trim(channel)                     AS channel,
    CAST(spend AS DOUBLE)             AS spend,
    CAST(new_users_acquired AS INTEGER) AS new_users_acquired,
    trim(segment)                     AS segment
FROM raw_marketing_spend
