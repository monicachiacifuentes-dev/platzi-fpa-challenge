-- mart_a1_01_cohort_retention: signup-month cohort retention matrix (M-11), long format,
-- for Total / B2C / B2B, months since signup 0..15, logo and $ (MRR incl. expansion) versions.
--
-- Built on fct_customer_mrr_monthly (user x month-end grid, MRR per M-02). Cohort = signup
-- month (date_trunc('month', signup_date)); month_k = months between month_end and cohort
-- month. Because the grid only runs from a user's signup month through 2024-04-30, month_k
-- naturally truncates near the end of the 16-month window (e.g. the 2024-04 cohort only has
-- month_k=0) -- no fabricated future months.
--
-- customers_start / mrr_start = cohort size / MRR at month_k=0 (every user's first
-- subscription starts on signup_date, so every cohort member is active at month_k=0 --
-- verified data fact, Plan_and_Index.md section 2). logo_retention = customers_active /
-- customers_start; dollar_retention = mrr_active / mrr_start (includes expansion, so can
-- exceed 100% for B2B cohorts).
WITH base AS (
    SELECT
        f.user_id,
        f.segment,
        f.customer_type,
        f.month_end,
        f.mrr,
        CAST(date_trunc('month', u.signup_date) AS DATE) AS cohort_month,
        (EXTRACT(YEAR FROM f.month_end)  - EXTRACT(YEAR FROM u.signup_date)) * 12
            + (EXTRACT(MONTH FROM f.month_end) - EXTRACT(MONTH FROM u.signup_date)) AS month_k
    FROM fct_customer_mrr_monthly f
    JOIN stg_users u ON u.user_id = f.user_id
),
segmented AS (
    SELECT cohort_month, month_k, user_id, mrr, 'Total' AS segment_group FROM base
    UNION ALL
    SELECT cohort_month, month_k, user_id, mrr, customer_type AS segment_group FROM base
),
agg AS (
    SELECT
        cohort_month,
        segment_group,
        month_k,
        COUNT(DISTINCT CASE WHEN mrr > 0 THEN user_id END) AS customers_active,
        SUM(mrr)                                           AS mrr_active
    FROM segmented
    GROUP BY 1, 2, 3
),
starts AS (
    SELECT cohort_month, segment_group,
           customers_active AS customers_start,
           mrr_active       AS mrr_start
    FROM agg
    WHERE month_k = 0
)
SELECT
    a.cohort_month,
    a.segment_group,
    a.month_k,
    st.customers_start,
    a.customers_active,
    CASE WHEN st.customers_start > 0 THEN a.customers_active::DOUBLE / st.customers_start END AS logo_retention,
    st.mrr_start,
    a.mrr_active,
    CASE WHEN st.mrr_start > 0 THEN a.mrr_active / st.mrr_start END AS dollar_retention
FROM agg a
JOIN starts st USING (cohort_month, segment_group)
ORDER BY 1, 2, 3
