-- mart_a2_13_sensitivity: WP21 -- long-format sensitivity grid (segment, lever,
-- scenario -> cac, gm_pct, lifetime_months, ltv, ltv_cac, cac_payback_months).
-- Levers: gna_split_method, gna_pct_allocated, cac_period, gm_allocation,
-- retention_curve, lifetime_cap (Proposed A-18), and a combined
-- gm_x_lifetime_grid (SMB/Enterprise only, as requested in review) crossing the
-- GM-allocation choice with the lifetime-cap choice.
WITH base AS (
    SELECT
        c6.segment,
        c6.marketing_spend, c6.new_paying_customers,
        c6.cac_fully_loaded_base            AS cac6_base,
        c6.cac_fully_loaded_sens_customer_share AS cac6_sens_customer_share,
        c6.cac_fully_loaded_scenario_0pct   AS cac6_scenario_0pct,
        c6.cac_fully_loaded_scenario_25pct  AS cac6_scenario_25pct,
        c6.cac_fully_loaded_scenario_50pct  AS cac6_scenario_50pct,
        c16.cac_fully_loaded_base           AS cac16_base,
        a.arpa_t6m_avg,
        g.gm_pct_t6m_base,
        g.gm_pct_t6m_sens_customer_weighted,
        l.lifetime_dollar_60, l.lifetime_dollar_36, l.lifetime_dollar_uncapped,
        l.lifetime_logo_60
    FROM mart_a2_06_cac_fully_loaded c6
    JOIN mart_a2_06_cac_fully_loaded c16 ON c16.segment = c6.segment AND c16.period = 'T16M'
    JOIN (SELECT segment, MAX(CASE WHEN period='T6M_avg' THEN arpa END) AS arpa_t6m_avg FROM mart_a2_09_arpa GROUP BY segment) a
        ON a.segment = c6.segment
    JOIN (SELECT segment, AVG(gm_pct_base) AS gm_pct_t6m_base, AVG(gm_pct_sens_customer_weighted) AS gm_pct_t6m_sens_customer_weighted
          FROM mart_a2_08_gm_monthly WHERE month BETWEEN DATE '2023-11-30' AND DATE '2024-04-30' GROUP BY segment) g
        ON g.segment = c6.segment
    JOIN mart_a2_11_lifetime l ON l.segment = c6.segment
    WHERE c6.period = 'T6M' AND c6.segment IN ('B2C', 'SMB', 'Enterprise', 'Total')
),
rows_ AS (
    -- gna_split_method
    SELECT segment, 'gna_split_method' AS lever, 'base_by_marketing_share (T6M)' AS scenario,
           cac6_base AS cac, gm_pct_t6m_base AS gm_pct, lifetime_dollar_60 AS lifetime_months FROM base
    UNION ALL
    SELECT segment, 'gna_split_method', 'sens_by_customer_share (T6M)',
           cac6_sens_customer_share, gm_pct_t6m_base, lifetime_dollar_60 FROM base
    -- gna_pct_allocated
    UNION ALL
    SELECT segment, 'gna_pct_allocated', '0% of G&A (T6M)', cac6_scenario_0pct, gm_pct_t6m_base, lifetime_dollar_60 FROM base
    UNION ALL
    SELECT segment, 'gna_pct_allocated', '25% of G&A (T6M)', cac6_scenario_25pct, gm_pct_t6m_base, lifetime_dollar_60 FROM base
    UNION ALL
    SELECT segment, 'gna_pct_allocated', '50% of G&A (T6M)', cac6_scenario_50pct, gm_pct_t6m_base, lifetime_dollar_60 FROM base
    -- cac_period
    UNION ALL
    SELECT segment, 'cac_period', 'T6M (base)', cac6_base, gm_pct_t6m_base, lifetime_dollar_60 FROM base
    UNION ALL
    SELECT segment, 'cac_period', 'T16M', cac16_base, gm_pct_t6m_base, lifetime_dollar_60 FROM base
    -- gm_allocation
    UNION ALL
    SELECT segment, 'gm_allocation', 'base (all COGS by MRR share, neutral)', cac6_base, gm_pct_t6m_base, lifetime_dollar_60 FROM base
    UNION ALL
    SELECT segment, 'gm_allocation', 'downside sensitivity (CS/Infra by customers)', cac6_base, gm_pct_t6m_sens_customer_weighted, lifetime_dollar_60 FROM base
    -- retention_curve (curve shape, at the base 60mo cap)
    UNION ALL
    SELECT segment, 'retention_curve', 'base ($ / dollar retention curve)', cac6_base, gm_pct_t6m_base, lifetime_dollar_60 FROM base
    UNION ALL
    SELECT segment, 'retention_curve', 'sensitivity (logo survival curve)', cac6_base, gm_pct_t6m_base, lifetime_logo_60 FROM base
    -- lifetime_cap (Proposed A-18)
    UNION ALL
    SELECT segment, 'lifetime_cap', '60 months (base)', cac6_base, gm_pct_t6m_base, lifetime_dollar_60 FROM base
    UNION ALL
    SELECT segment, 'lifetime_cap', '36 months', cac6_base, gm_pct_t6m_base, lifetime_dollar_36 FROM base
    UNION ALL
    SELECT segment, 'lifetime_cap', 'uncapped (reference only)', cac6_base, gm_pct_t6m_base, lifetime_dollar_uncapped FROM base
    -- gm_x_lifetime_grid (SMB/Enterprise only, per review request): GM allocation x lifetime cap
    UNION ALL
    SELECT segment, 'gm_x_lifetime_grid', 'base GM x 60mo cap', cac6_base, gm_pct_t6m_base, lifetime_dollar_60 FROM base WHERE segment IN ('SMB', 'Enterprise')
    UNION ALL
    SELECT segment, 'gm_x_lifetime_grid', 'base GM x 36mo cap', cac6_base, gm_pct_t6m_base, lifetime_dollar_36 FROM base WHERE segment IN ('SMB', 'Enterprise')
    UNION ALL
    SELECT segment, 'gm_x_lifetime_grid', 'base GM x uncapped', cac6_base, gm_pct_t6m_base, lifetime_dollar_uncapped FROM base WHERE segment IN ('SMB', 'Enterprise')
    UNION ALL
    SELECT segment, 'gm_x_lifetime_grid', 'downside GM x 60mo cap', cac6_base, gm_pct_t6m_sens_customer_weighted, lifetime_dollar_60 FROM base WHERE segment IN ('SMB', 'Enterprise')
    UNION ALL
    SELECT segment, 'gm_x_lifetime_grid', 'downside GM x 36mo cap', cac6_base, gm_pct_t6m_sens_customer_weighted, lifetime_dollar_36 FROM base WHERE segment IN ('SMB', 'Enterprise')
    UNION ALL
    SELECT segment, 'gm_x_lifetime_grid', 'downside GM x uncapped', cac6_base, gm_pct_t6m_sens_customer_weighted, lifetime_dollar_uncapped FROM base WHERE segment IN ('SMB', 'Enterprise')
)
SELECT
    r.segment, r.lever, r.scenario,
    ROUND(r.cac, 2)              AS cac,
    ROUND(r.gm_pct, 4)           AS gm_pct,
    ROUND(r.lifetime_months, 2)  AS lifetime_months,
    ROUND(b.arpa_t6m_avg * r.gm_pct * r.lifetime_months, 2) AS ltv,
    ROUND(b.arpa_t6m_avg * r.gm_pct * r.lifetime_months / NULLIF(r.cac, 0), 2) AS ltv_cac,
    ROUND(r.cac / NULLIF(b.arpa_t6m_avg * r.gm_pct, 0), 1) AS cac_payback_months
FROM rows_ r
JOIN base b ON b.segment = r.segment
ORDER BY
    CASE r.segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'Total' THEN 5 END,
    r.lever, r.scenario
