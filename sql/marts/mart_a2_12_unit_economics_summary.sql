-- mart_a2_12_unit_economics_summary: WP21 -- final segment-level unit economics
-- (M-13/M-14/M-15). Base case: GM% = all-COGS-by-MRR (neutral, mart_a2_08
-- gm_pct_base); lifetime = dollar retention curve capped at 60 months (Proposed
-- A-18, mart_a2_11 lifetime_dollar_60); CAC = fully loaded, T6M (mart_a2_06).
-- LTV = ARPA(T6M avg) x GM%(T6M avg, base) x lifetime(dollar, 60mo cap).
-- Retention-adjusted payback: months until cumulative gross profit per acquired
-- customer (arpa_at_signup x dollar_retention(k) x GM%, summed k=0..k_rel) >=
-- CAC; 'never' if not reached within the observed reliable horizon, or if GM% <= 0.
WITH gm_t6m AS (
    SELECT segment,
           AVG(gm_pct_base)                    AS gm_pct_t6m_base,
           AVG(gm_pct_sens_customer_weighted)  AS gm_pct_t6m_sens_customer_weighted
    FROM mart_a2_08_gm_monthly
    WHERE month BETWEEN DATE '2023-11-30' AND DATE '2024-04-30'
    GROUP BY segment
),
arpa_p AS (
    SELECT segment,
           MAX(CASE WHEN period = 'T6M_avg' THEN arpa END) AS arpa_t6m_avg,
           MAX(CASE WHEN period = 'Apr-24'  THEN arpa END) AS arpa_apr24
    FROM mart_a2_09_arpa
    GROUP BY segment
),
cac6 AS (SELECT * FROM mart_a2_06_cac_fully_loaded WHERE period = 'T6M'),
cac16 AS (SELECT * FROM mart_a2_06_cac_fully_loaded WHERE period = 'T16M'),
life AS (SELECT * FROM mart_a2_11_lifetime),
ra_curve AS (
    SELECT
        c.segment, c.k,
        SUM(l.arpa_at_signup * c.dollar_retention * g.gm_pct_t6m_base) OVER (PARTITION BY c.segment ORDER BY c.k) AS cum_gross_profit
    FROM mart_a2_10_survival_curve c
    JOIN life l ON l.segment = c.segment
    JOIN gm_t6m g ON g.segment = c.segment
    WHERE c.k <= l.k_rel
),
ra_result AS (
    SELECT rc.segment, MIN(rc.k) AS retention_adjusted_payback_months
    FROM ra_curve rc
    JOIN cac6 ON cac6.segment = rc.segment
    WHERE rc.cum_gross_profit >= cac6.cac_fully_loaded_base
    GROUP BY rc.segment
),
joined AS (
    SELECT
        c6.segment,
        a.arpa_t6m_avg,
        a.arpa_apr24,
        g.gm_pct_t6m_base,
        g.gm_pct_t6m_sens_customer_weighted,
        c6.cac_fully_loaded_base AS cac_fully_loaded_t6m,
        c16.cac_fully_loaded_base AS cac_fully_loaded_t16m,
        l.k_rel AS reliable_k_max_months,
        l.arpa_at_signup,
        l.logo_tail_churn, l.logo_tail_method,
        l.dollar_tail_decay, l.dollar_tail_method,
        l.lifetime_logo_36, l.lifetime_logo_60, l.lifetime_logo_uncapped,
        l.lifetime_dollar_36, l.lifetime_dollar_60, l.lifetime_dollar_uncapped,
        l.crosscheck_logo_1_over_churn, l.crosscheck_dollar_1_over_decay,
        r.retention_adjusted_payback_months
    FROM cac6 c6
    JOIN cac16 c16 ON c16.segment = c6.segment
    JOIN arpa_p a ON a.segment = c6.segment
    JOIN gm_t6m g ON g.segment = c6.segment
    JOIN life l ON l.segment = c6.segment
    LEFT JOIN ra_result r ON r.segment = c6.segment
    WHERE c6.segment IN ('B2C', 'SMB', 'Enterprise', 'Total')
)
SELECT
    segment,
    ROUND(arpa_t6m_avg, 2)  AS arpa_t6m_avg,
    ROUND(arpa_apr24, 2)    AS arpa_apr24,
    ROUND(gm_pct_t6m_base, 4) AS gm_pct_t6m_base,
    ROUND(gm_pct_t6m_sens_customer_weighted, 4) AS gm_pct_t6m_sens_customer_weighted,
    cac_fully_loaded_t6m,
    cac_fully_loaded_t16m,
    reliable_k_max_months,
    ROUND(logo_tail_churn, 4)  AS logo_tail_churn,
    logo_tail_method,
    ROUND(dollar_tail_decay, 4) AS dollar_tail_decay,
    dollar_tail_method,
    lifetime_logo_60          AS lifetime_logo_months,      -- base cap (A-18)
    lifetime_dollar_60        AS lifetime_dollar_months,    -- base cap (A-18), used in ltv_base
    lifetime_dollar_36,
    lifetime_dollar_uncapped,
    lifetime_logo_36,
    lifetime_logo_uncapped,
    crosscheck_logo_1_over_churn,
    crosscheck_dollar_1_over_decay,
    ROUND(arpa_t6m_avg * gm_pct_t6m_base * lifetime_dollar_60, 2)       AS ltv_base,
    ROUND(arpa_t6m_avg * gm_pct_t6m_base * lifetime_dollar_36, 2)       AS ltv_36cap,
    ROUND(arpa_t6m_avg * gm_pct_t6m_base * lifetime_dollar_uncapped, 2) AS ltv_uncapped,
    ROUND(arpa_t6m_avg * gm_pct_t6m_base * lifetime_logo_60, 2)         AS ltv_sens_logo_curve,
    ROUND(arpa_t6m_avg * gm_pct_t6m_sens_customer_weighted * lifetime_dollar_60, 2) AS ltv_sens_gm_customer_weighted,
    ROUND(arpa_t6m_avg * gm_pct_t6m_base * lifetime_dollar_60 / NULLIF(cac_fully_loaded_t6m, 0), 2)  AS ltv_cac_t6m,
    ROUND(arpa_t6m_avg * gm_pct_t6m_base * lifetime_dollar_60 / NULLIF(cac_fully_loaded_t16m, 0), 2) AS ltv_cac_t16m,
    ROUND(cac_fully_loaded_t6m  / NULLIF(arpa_t6m_avg * gm_pct_t6m_base, 0), 1) AS cac_payback_months_t6m,
    ROUND(cac_fully_loaded_t16m / NULLIF(arpa_t6m_avg * gm_pct_t6m_base, 0), 1) AS cac_payback_months_t16m,
    retention_adjusted_payback_months,
    CASE
        WHEN gm_pct_t6m_base <= 0 THEN 'never (non-positive gross margin)'
        WHEN retention_adjusted_payback_months IS NULL THEN 'never (not reached within observed ' || reliable_k_max_months || '-month horizon)'
        ELSE 'reached at k=' || retention_adjusted_payback_months
    END AS retention_adjusted_payback_note,
    CASE WHEN segment = 'Enterprise' THEN 18.0 ELSE 12.0 END AS benchmark_payback_threshold_months,
    (arpa_t6m_avg * gm_pct_t6m_base * lifetime_dollar_60 / NULLIF(cac_fully_loaded_t6m, 0)) >= 3 AS benchmark_ltv_cac_pass_ge3,
    (cac_fully_loaded_t6m / NULLIF(arpa_t6m_avg * gm_pct_t6m_base, 0)) BETWEEN 0 AND (CASE WHEN segment = 'Enterprise' THEN 18.0 ELSE 12.0 END) AS benchmark_payback_pass
FROM joined
ORDER BY CASE segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'Total' THEN 5 END
