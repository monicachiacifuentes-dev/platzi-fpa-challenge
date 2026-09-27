-- mart_a1_05_may24_population: the May-2024 "at risk" population per D-08 -- subscriptions
-- with status = 'active' and end_date falling in 2024-05 (monthly and annual renewals due
-- that month). Carries the same feature columns as mart_a1_03 (minus the outcome, which is
-- unknown for these rows) so mart_a1_06 can score them with the trained model.
SELECT
    subscription_id,
    user_id,
    segment,
    customer_type,
    plan_type,
    start_date,
    end_date,
    mrr,
    prev_mrr,
    mrr_delta,
    active_days,
    courses_seen,
    materials_seen,
    favorite_category,
    period_number,
    main_gateway,
    CASE
        WHEN prev_mrr IS NULL THEN 'no_prior_renewal'
        WHEN mrr_delta < 0     THEN 'contraction'
        WHEN mrr_delta > 0     THEN 'expansion'
        ELSE 'flat'
    END AS renewal_change_bucket
FROM fct_subscriptions
WHERE status = 'active'
  AND end_date BETWEEN DATE '2024-05-01' AND DATE '2024-05-31'
