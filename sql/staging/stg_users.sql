-- stg_users: typed, trimmed users with derived customer_type (B2C/B2B)
SELECT
    trim(user_id)                          AS user_id,
    trim(first_name)                       AS first_name,
    trim(lower(email))                     AS email,
    CAST(age AS INTEGER)                   AS age,
    trim(segment)                          AS segment,
    CASE WHEN trim(segment) = 'B2C' THEN 'B2C' ELSE 'B2B' END AS customer_type,
    CAST(signup_date AS DATE)              AS signup_date
FROM raw_users
