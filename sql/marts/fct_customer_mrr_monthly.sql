-- fct_customer_mrr_monthly: user x month-end grid (from the user's signup month
-- through 2024-04-30), with MRR active at each month-end per M-02
-- (start_date <= month_end < end_date; 0 if no subscription covers it),
-- the previous month-end's MRR, and a movement classification.
--
-- movement (implementation detail, not an M-xx metric; see sql/README.md /
-- Plan_and_Index.md decisions log for the rationale):
--   'new'            : first month in the grid (signup month) with mrr > 0,
--                      or prev_mrr = 0 and mrr > 0
--   'expansion'      : prev_mrr > 0 and mrr > prev_mrr
--   'contraction'    : prev_mrr > 0 and 0 < mrr < prev_mrr
--   'churn'          : prev_mrr > 0 and mrr = 0
--   'retained_flat'  : prev_mrr > 0 and mrr = prev_mrr
--   'inactive'       : prev_mrr = 0 (or NULL) and mrr = 0 (before first sub / after churn, no coverage)
WITH grid AS (
    SELECT u.user_id, u.segment, u.customer_type, u.signup_date, ms.month_start, ms.month_end
    FROM stg_users u
    CROSS JOIN int_month_spine ms
    WHERE ms.month_start >= date_trunc('month', u.signup_date)
),
mrr_per_month AS (
    SELECT
        g.user_id,
        g.segment,
        g.customer_type,
        g.month_end,
        COALESCE(SUM(s.mrr), 0) AS mrr
    FROM grid g
    LEFT JOIN stg_subscriptions s
        ON s.user_id = g.user_id
       AND s.start_date <= g.month_end
       AND g.month_end < s.end_date
    GROUP BY g.user_id, g.segment, g.customer_type, g.month_end
),
with_prev AS (
    SELECT
        *,
        LAG(mrr) OVER (PARTITION BY user_id ORDER BY month_end) AS prev_mrr
    FROM mrr_per_month
)
SELECT
    user_id,
    segment,
    customer_type,
    month_end,
    mrr,
    prev_mrr,
    CASE
        WHEN prev_mrr IS NULL AND mrr > 0 THEN 'new'
        WHEN COALESCE(prev_mrr, 0) = 0 AND mrr > 0 THEN 'new'
        WHEN prev_mrr > 0 AND mrr = 0 THEN 'churn'
        WHEN prev_mrr > 0 AND mrr > prev_mrr THEN 'expansion'
        WHEN prev_mrr > 0 AND mrr < prev_mrr AND mrr > 0 THEN 'contraction'
        WHEN prev_mrr > 0 AND mrr = prev_mrr THEN 'retained_flat'
        ELSE 'inactive'
    END AS movement
FROM with_prev
