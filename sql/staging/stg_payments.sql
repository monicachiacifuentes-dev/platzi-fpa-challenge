-- stg_payments: typed, trimmed payments (list-price cash events, joined downstream by subscription_id)
SELECT
    trim(lower(email))               AS email,
    trim(subscription_id)            AS subscription_id,
    CAST(amount AS DOUBLE)           AS amount,
    CAST(payment_date AS DATE)       AS payment_date,
    CAST(payment_gateway_id AS INTEGER) AS payment_gateway_id
FROM raw_payments
