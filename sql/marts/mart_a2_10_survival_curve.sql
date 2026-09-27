-- mart_a2_10_survival_curve: WP21 -- M-14 observed retention/survival curve by
-- segment, pooled across signup cohorts, from fct_customer_mrr_monthly.
-- k = months since signup (0 = signup month). Because fct_customer_mrr_monthly's
-- grid runs from each user's signup month through 2024-04-30 with no gaps, a
-- user contributes exactly one row per k from 0 to their own max observable k
-- (Apr-24 minus signup month) -- so grouping by (segment, k) automatically
-- restricts to the cohort still within the observation window at that k
-- (right-censoring: exposed_n falls as k rises because later cohorts haven't
-- reached high k yet; see results.md for the reliability cutoff used).
--   logo_survival     = active_n / exposed_n                      (logo curve)
--   dollar_retention  = mrr_at_k_sum / mrr_at_0_sum for the same exposed cohort
--                       (captures B2B expansion -- can exceed 1.0)
WITH mrr_k AS (
    SELECT
        f.user_id,
        f.segment,
        f.customer_type,
        f.mrr,
        (EXTRACT(YEAR FROM f.month_end) - EXTRACT(YEAR FROM u.signup_date)) * 12
            + (EXTRACT(MONTH FROM f.month_end) - EXTRACT(MONTH FROM u.signup_date)) AS k
    FROM fct_customer_mrr_monthly f
    JOIN stg_users u ON u.user_id = f.user_id
),
mrr0 AS (
    SELECT user_id, mrr AS mrr_at_0
    FROM mrr_k
    WHERE k = 0
),
expanded AS (
    SELECT m.user_id, m.segment AS segment_group, m.mrr, m.k FROM mrr_k m
    UNION ALL
    SELECT m.user_id, 'B2B' AS segment_group, m.mrr, m.k FROM mrr_k m WHERE m.customer_type = 'B2B'
    UNION ALL
    SELECT m.user_id, 'Total' AS segment_group, m.mrr, m.k FROM mrr_k m
),
expanded0 AS (
    SELECT m0.user_id, m0.mrr_at_0, u.segment AS orig_segment, u.customer_type FROM mrr0 m0 JOIN stg_users u ON u.user_id = m0.user_id
),
expanded0_x AS (
    SELECT user_id, orig_segment AS segment_group, mrr_at_0 FROM expanded0
    UNION ALL
    SELECT user_id, 'B2B' AS segment_group, mrr_at_0 FROM expanded0 WHERE customer_type = 'B2B'
    UNION ALL
    SELECT user_id, 'Total' AS segment_group, mrr_at_0 FROM expanded0
),
curve AS (
    SELECT
        e.segment_group AS segment,
        e.k,
        COUNT(DISTINCT e.user_id)                             AS exposed_n,
        SUM(CASE WHEN e.mrr > 0 THEN 1 ELSE 0 END)            AS active_n,
        SUM(e.mrr)                                             AS mrr_at_k_sum,
        SUM(e0.mrr_at_0)                                       AS mrr_at_0_sum
    FROM expanded e
    JOIN expanded0_x e0 ON e0.user_id = e.user_id AND e0.segment_group = e.segment_group
    GROUP BY e.segment_group, e.k
)
SELECT
    segment,
    k,
    exposed_n,
    active_n,
    ROUND(active_n::DOUBLE / NULLIF(exposed_n, 0), 4)          AS logo_survival,
    mrr_at_k_sum,
    mrr_at_0_sum,
    ROUND(mrr_at_k_sum / NULLIF(mrr_at_0_sum, 0), 4)           AS dollar_retention,
    ROUND(mrr_at_0_sum / NULLIF(exposed_n, 0), 2)              AS arpa_at_signup
FROM curve
ORDER BY
    CASE segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'B2B' THEN 4 WHEN 'Total' THEN 5 END,
    k
