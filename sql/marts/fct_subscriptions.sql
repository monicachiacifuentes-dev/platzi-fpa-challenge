-- fct_subscriptions: denormalized FP&A fact table, one row per subscription period.
-- Adds cash-side facts from payments: number of payments, amount paid (list price,
-- see Docs/Datasets.md quirk: payments do not reflect B2B mrr changes), and the
-- subscription's main payment gateway (the gateway used on the most payments for
-- that subscription_id; ties broken by the lowest payment_gateway_id).
WITH payment_agg AS (
    SELECT
        subscription_id,
        COUNT(*)         AS n_payments,
        SUM(amount)      AS amount_paid
    FROM stg_payments
    GROUP BY subscription_id
),
gateway_rank AS (
    SELECT
        p.subscription_id,
        g.payment_gateway_name,
        COUNT(*) AS n,
        ROW_NUMBER() OVER (
            PARTITION BY p.subscription_id
            ORDER BY COUNT(*) DESC, p.payment_gateway_id ASC
        ) AS rn
    FROM stg_payments p
    JOIN stg_payment_gateways g ON g.payment_gateway_id = p.payment_gateway_id
    GROUP BY p.subscription_id, g.payment_gateway_name, p.payment_gateway_id
),
main_gateway AS (
    SELECT subscription_id, payment_gateway_name AS main_gateway
    FROM gateway_rank
    WHERE rn = 1
)
SELECT
    isp.*,
    COALESCE(pa.n_payments, 0)    AS n_payments,
    COALESCE(pa.amount_paid, 0)   AS amount_paid,
    mg.main_gateway
FROM int_subscription_periods isp
LEFT JOIN payment_agg  pa ON pa.subscription_id = isp.subscription_id
LEFT JOIN main_gateway mg ON mg.subscription_id = isp.subscription_id
