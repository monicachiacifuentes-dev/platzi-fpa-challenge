-- mart_a1_02_cohort_risk_flags: flags signup cohorts whose retention at a given age (month_k)
-- is significantly below the company-wide benchmark for that age and segment_group.
--
-- Benchmark = the size-weighted average retention across ALL cohorts that have reached that
-- month_k yet, i.e. SUM(customers_active)/SUM(customers_start) (logo) and
-- SUM(mrr_active)/SUM(mrr_start) (dollar), computed with a window function partitioned by
-- (segment_group, month_k). This is the "average cohort at that age", not a simple
-- unweighted mean of percentages (which would over-weight tiny cohorts).
--
-- Flag rule: logo_gap_pp = logo_retention - weighted_avg_logo (in percentage points).
-- at_risk_logo = TRUE when logo_gap_pp <= -0.10 (10pp or more below the age benchmark)
-- AND the cohort has at least 20 starting customers (min_cohort_size, avoids flagging
-- noise in tiny cohorts). Same construction for the dollar version (at_risk_dollar).
-- Restricted to month_k IN (1,3,6) -- the ages requested in the brief (M1/M3/M6) -- but the
-- window/benchmark itself is computed over all cohorts reaching that age, all months.
WITH r AS (
    SELECT * FROM mart_a1_01_cohort_retention
),
benchmarked AS (
    SELECT
        cohort_month,
        segment_group,
        month_k,
        customers_start,
        customers_active,
        logo_retention,
        mrr_start,
        mrr_active,
        dollar_retention,
        SUM(customers_active) OVER (PARTITION BY segment_group, month_k)::DOUBLE
            / NULLIF(SUM(customers_start) OVER (PARTITION BY segment_group, month_k), 0) AS avg_logo_retention_at_k,
        SUM(mrr_active) OVER (PARTITION BY segment_group, month_k)
            / NULLIF(SUM(mrr_start) OVER (PARTITION BY segment_group, month_k), 0)       AS avg_dollar_retention_at_k,
        COUNT(*) OVER (PARTITION BY segment_group, month_k)                              AS n_cohorts_at_k
    FROM r
    WHERE month_k IN (1, 3, 6)
)
SELECT
    cohort_month,
    segment_group,
    month_k,
    customers_start,
    customers_active,
    logo_retention,
    avg_logo_retention_at_k,
    logo_retention - avg_logo_retention_at_k AS logo_gap_pp,
    mrr_start,
    mrr_active,
    dollar_retention,
    avg_dollar_retention_at_k,
    dollar_retention - avg_dollar_retention_at_k AS dollar_gap_pp,
    n_cohorts_at_k,
    (customers_start >= 20 AND logo_retention - avg_logo_retention_at_k <= -0.10)     AS at_risk_logo,
    (customers_start >= 20 AND dollar_retention - avg_dollar_retention_at_k <= -0.10) AS at_risk_dollar
FROM benchmarked
ORDER BY segment_group, month_k, logo_gap_pp
