-- mart_a3_07_renewal_segmentation: renewal-event view (a larger, more representative
-- population than the 417-customer T12M snapshot cohort). All renewals
-- (period_number > 1) whose new period starts 2023-05-01..2024-04-30, from
-- fct_subscriptions (built on int_subscription_periods). Segmented by
-- segment x plan_type x tenure bucket (from period_number) x MRR tier (from the
-- PRE-renewal mrr, i.e. prev_mrr) x renewal_change (expansion/contraction/flat).
WITH renewals AS (
    SELECT
        segment,
        customer_type,
        plan_type,
        prev_mrr,
        mrr AS new_mrr,
        mrr_delta,
        renewal_change,
        CASE
            WHEN period_number = 2               THEN '2'
            WHEN period_number BETWEEN 3 AND 4   THEN '3-4'
            WHEN period_number BETWEEN 5 AND 8   THEN '5-8'
            ELSE '9+'
        END AS tenure_bucket,
        CASE
            WHEN prev_mrr < 100  THEN '<100'
            WHEN prev_mrr < 300  THEN '100-300'
            WHEN prev_mrr < 600  THEN '300-600'
            WHEN prev_mrr < 1000 THEN '600-1000'
            ELSE '1000+'
        END AS mrr_tier
    FROM fct_subscriptions
    WHERE period_number > 1
      AND start_date BETWEEN DATE '2023-05-01' AND DATE '2024-04-30'
)
SELECT
    segment,
    plan_type,
    tenure_bucket,
    mrr_tier,
    renewal_change,
    CAST(COUNT(*) AS BIGINT)                                              AS n_events,
    SUM(prev_mrr)                                                         AS pre_renewal_mrr,
    SUM(new_mrr)                                                          AS post_renewal_mrr,
    SUM(CASE WHEN renewal_change = 'expansion'   THEN mrr_delta  ELSE 0 END) AS expansion_amt,
    SUM(CASE WHEN renewal_change = 'contraction' THEN -mrr_delta ELSE 0 END) AS contraction_amt
FROM renewals
GROUP BY segment, plan_type, tenure_bucket, mrr_tier, renewal_change
ORDER BY segment, plan_type, tenure_bucket, mrr_tier, renewal_change
