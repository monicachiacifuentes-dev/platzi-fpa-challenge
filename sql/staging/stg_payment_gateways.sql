-- stg_payment_gateways: gateway id -> name lookup
SELECT
    CAST(payment_gateway_id AS INTEGER) AS payment_gateway_id,
    trim(payment_gateway_name)          AS payment_gateway_name
FROM raw_payment_gateways
