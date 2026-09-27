-- mart_a2_11_lifetime: WP21 -- M-14 expected lifetime by segment, from the
-- pooled survival curve (mart_a2_10), with a capped-horizon LTV input
-- (Proposed A-18: 60-month base cap, 36-month sensitivity, uncapped reference).
--
-- Reliability (Proposed A-15): a k-point is trusted only while exposed_n >= 20;
-- k_rel = the largest such k per segment (15 B2C/Total, 14 SMB, 11 Enterprise).
--
-- Tail decay rate (per curve, logo and dollar): cascading average of the
-- period-over-period ratio value(k)/value(k-1) over the last 3 reliable
-- transitions; if that average is not a positive decay (pooled cross-cohort
-- curves are noisy/non-monotonic at high k with small n), fall back to the
-- last 6, then the full reliable range.
--   Proposed A-16: if the DOLLAR curve shows no net decay in ANY window (net
--     expansion in the tail, e.g. small-n B2B), fall back to the segment's own
--     LOGO tail churn rate.
--   Proposed A-17: floor the dollar tail decay rate at the logo tail churn rate
--     whenever it comes out lower -- a near-zero observed dollar decay on a
--     small sample (SMB) otherwise makes the geometric tail explode into an
--     implausible multi-decade lifetime; dollar retention cannot structurally
--     out-decay logo retention forever, since every eventually churned logo
--     takes its dollars with it.
--
-- Lifetime = Sigma(curve, k=0..k_rel) + a geometric tail from the last observed
-- value at the tail decay rate, truncated at a total horizon (Proposed A-18):
--   *_60         : capped at 60 total months (base, used in mart_a2_12 LTV)
--   *_36         : capped at 36 total months (sensitivity)
--   *_uncapped   : full infinite geometric tail (reference only, not used in LTV)
WITH reliable AS (
    SELECT segment, MAX(k) AS k_rel
    FROM mart_a2_10_survival_curve
    WHERE exposed_n >= 20
    GROUP BY segment
),
curve_rel AS (
    SELECT c.segment, c.k, c.logo_survival, c.dollar_retention, c.arpa_at_signup, r.k_rel
    FROM mart_a2_10_survival_curve c
    JOIN reliable r ON r.segment = c.segment
    WHERE c.k <= r.k_rel
),
ratios AS (
    SELECT
        segment, k, k_rel,
        logo_survival / NULLIF(LAG(logo_survival) OVER (PARTITION BY segment ORDER BY k), 0)     AS logo_ratio,
        dollar_retention / NULLIF(LAG(dollar_retention) OVER (PARTITION BY segment ORDER BY k), 0) AS dollar_ratio
    FROM curve_rel
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY segment ORDER BY k DESC) AS rn
    FROM ratios
    WHERE k >= 1
),
rate_candidates AS (
    SELECT
        segment,
        1 - AVG(CASE WHEN rn <= 3 THEN logo_ratio END)   AS logo_rate3,
        1 - AVG(CASE WHEN rn <= 6 THEN logo_ratio END)   AS logo_rate6,
        1 - AVG(logo_ratio)                              AS logo_rate_full,
        1 - AVG(CASE WHEN rn <= 3 THEN dollar_ratio END) AS dollar_rate3,
        1 - AVG(CASE WHEN rn <= 6 THEN dollar_ratio END) AS dollar_rate6,
        1 - AVG(dollar_ratio)                             AS dollar_rate_full
    FROM ranked
    GROUP BY segment
),
rates AS (
    SELECT
        segment,
        CASE WHEN logo_rate3 > 0.001 THEN logo_rate3
             WHEN logo_rate6 > 0.001 THEN logo_rate6
             WHEN logo_rate_full > 0.001 THEN logo_rate_full
             ELSE NULL END AS logo_rate,
        CASE WHEN logo_rate3 > 0.001 THEN 'last3'
             WHEN logo_rate6 > 0.001 THEN 'last6'
             WHEN logo_rate_full > 0.001 THEN 'full_range'
             ELSE 'no_decay_observed' END AS logo_method,
        CASE WHEN dollar_rate3 > 0.001 THEN dollar_rate3
             WHEN dollar_rate6 > 0.001 THEN dollar_rate6
             WHEN dollar_rate_full > 0.001 THEN dollar_rate_full
             ELSE NULL END AS dollar_rate_raw,
        CASE WHEN dollar_rate3 > 0.001 THEN 'last3'
             WHEN dollar_rate6 > 0.001 THEN 'last6'
             WHEN dollar_rate_full > 0.001 THEN 'full_range'
             ELSE NULL END AS dollar_method_raw
    FROM rate_candidates
),
rates_final AS (
    SELECT
        segment,
        logo_rate,
        logo_method,
        -- A-16: fallback to logo rate if the dollar curve shows no net decay in any window
        CASE WHEN dollar_rate_raw IS NULL THEN logo_rate
             WHEN logo_rate IS NOT NULL AND dollar_rate_raw < logo_rate THEN logo_rate  -- A-17: floor at logo
             ELSE dollar_rate_raw END AS dollar_rate,
        CASE WHEN dollar_rate_raw IS NULL THEN 'fallback_to_logo_' || logo_method
             WHEN logo_rate IS NOT NULL AND dollar_rate_raw < logo_rate THEN dollar_method_raw || '+floored_at_logo_' || logo_method
             ELSE dollar_method_raw END AS dollar_method
    FROM rates
),
last_obs AS (
    SELECT
        cr.segment, cr.k_rel,
        MAX(CASE WHEN cr.k = cr.k_rel THEN cr.logo_survival END)    AS logo_at_krel,
        MAX(CASE WHEN cr.k = cr.k_rel THEN cr.dollar_retention END) AS dollar_at_krel,
        MAX(CASE WHEN cr.k = 0 THEN cr.arpa_at_signup END)          AS arpa_at_signup,
        SUM(cr.logo_survival)                                        AS observed_sum_logo,
        SUM(cr.dollar_retention)                                     AS observed_sum_dollar
    FROM curve_rel cr
    GROUP BY cr.segment, cr.k_rel
)
SELECT
    lo.segment,
    lo.k_rel,
    lo.arpa_at_signup,
    rf.logo_rate  AS logo_tail_churn,
    rf.logo_method AS logo_tail_method,
    rf.dollar_rate AS dollar_tail_decay,
    rf.dollar_method AS dollar_tail_method,
    lo.observed_sum_logo,
    lo.observed_sum_dollar,
    -- cross-checks (simple 1/rate, independent of the curve shape / cap)
    ROUND(1.0 / NULLIF(rf.logo_rate, 0), 2)   AS crosscheck_logo_1_over_churn,
    ROUND(1.0 / NULLIF(rf.dollar_rate, 0), 2) AS crosscheck_dollar_1_over_decay,
    -- lifetime, logo curve, at each horizon cap (Proposed A-18)
    ROUND(lo.observed_sum_logo + CASE WHEN rf.logo_rate > 0 THEN
        lo.logo_at_krel * (1 - rf.logo_rate) * (1 - POWER(1 - rf.logo_rate, GREATEST(36 - 1 - lo.k_rel, 0))) / rf.logo_rate
        ELSE 0 END, 2) AS lifetime_logo_36,
    ROUND(lo.observed_sum_logo + CASE WHEN rf.logo_rate > 0 THEN
        lo.logo_at_krel * (1 - rf.logo_rate) * (1 - POWER(1 - rf.logo_rate, GREATEST(60 - 1 - lo.k_rel, 0))) / rf.logo_rate
        ELSE 0 END, 2) AS lifetime_logo_60,
    ROUND(lo.observed_sum_logo + CASE WHEN rf.logo_rate > 0 THEN
        lo.logo_at_krel * (1 - rf.logo_rate) / rf.logo_rate
        ELSE 0 END, 2) AS lifetime_logo_uncapped,
    -- lifetime, dollar curve, at each horizon cap (Proposed A-18)
    ROUND(lo.observed_sum_dollar + CASE WHEN rf.dollar_rate > 0 THEN
        lo.dollar_at_krel * (1 - rf.dollar_rate) * (1 - POWER(1 - rf.dollar_rate, GREATEST(36 - 1 - lo.k_rel, 0))) / rf.dollar_rate
        ELSE 0 END, 2) AS lifetime_dollar_36,
    ROUND(lo.observed_sum_dollar + CASE WHEN rf.dollar_rate > 0 THEN
        lo.dollar_at_krel * (1 - rf.dollar_rate) * (1 - POWER(1 - rf.dollar_rate, GREATEST(60 - 1 - lo.k_rel, 0))) / rf.dollar_rate
        ELSE 0 END, 2) AS lifetime_dollar_60,
    ROUND(lo.observed_sum_dollar + CASE WHEN rf.dollar_rate > 0 THEN
        lo.dollar_at_krel * (1 - rf.dollar_rate) / rf.dollar_rate
        ELSE 0 END, 2) AS lifetime_dollar_uncapped
FROM last_obs lo
JOIN rates_final rf ON rf.segment = lo.segment
ORDER BY
    CASE lo.segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'B2B' THEN 4 WHEN 'Total' THEN 5 END
