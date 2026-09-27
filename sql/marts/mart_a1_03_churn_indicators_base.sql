-- mart_a1_03_churn_indicators_base: one row per subscription period with a KNOWN outcome
-- (status IN ('renewed','churned') -- excludes 'active', which is still in progress and has
-- no outcome yet, per the brief). This is both (a) the descriptive base for churn-rate-by-
-- bucket cuts (mart_a1_04) and (b) the modeling table for the logistic regression (WP20 /
-- doubles as WP32): features are bucketed here for readability, the Python script re-derives
-- standardized/dummy versions of the same underlying columns for the model itself.
--
-- model_split: time-based train/test split on end_date (brief's chosen cutoff) --
-- train = ended before 2024-01-01, test = ended 2024-01-01..2024-04-30. 'other' should not
-- occur (all renewed/churned periods end on or before 2024-04-30, the data snapshot).
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
    status,
    CASE WHEN status = 'churned' THEN 1 ELSE 0 END AS churned,
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
    END AS renewal_change_bucket,
    CASE
        WHEN active_days <= 5  THEN '0-5'
        WHEN active_days <= 10 THEN '6-10'
        WHEN active_days <= 15 THEN '11-15'
        WHEN active_days <= 20 THEN '16-20'
        WHEN active_days <= 25 THEN '21-25'
        ELSE '26-28'
    END AS active_days_bucket,
    CASE
        WHEN courses_seen <= 2  THEN '0-2'
        WHEN courses_seen <= 5  THEN '3-5'
        WHEN courses_seen <= 8  THEN '6-8'
        WHEN courses_seen <= 11 THEN '9-11'
        ELSE '12+'
    END AS courses_seen_bucket,
    CASE
        WHEN materials_seen <= 9  THEN '0-9'
        WHEN materials_seen <= 19 THEN '10-19'
        WHEN materials_seen <= 29 THEN '20-29'
        WHEN materials_seen <= 49 THEN '30-49'
        ELSE '50+'
    END AS materials_seen_bucket,
    CASE
        WHEN period_number = 1               THEN '1'
        WHEN period_number = 2               THEN '2'
        WHEN period_number = 3               THEN '3'
        WHEN period_number BETWEEN 4 AND 6   THEN '4-6'
        ELSE '7+'
    END AS tenure_bucket,
    CASE
        WHEN end_date < DATE '2024-01-01'                               THEN 'train'
        WHEN end_date BETWEEN DATE '2024-01-01' AND DATE '2024-04-30'   THEN 'test'
        ELSE 'other'
    END AS model_split
FROM fct_subscriptions
WHERE status IN ('renewed', 'churned')
