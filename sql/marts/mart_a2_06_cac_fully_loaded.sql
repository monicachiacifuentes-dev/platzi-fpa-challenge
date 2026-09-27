-- mart_a2_06_cac_fully_loaded: WP21 -- M-13 fully loaded CAC by segment,
-- periods T16M (full 16 months) and T6M (2023-11 .. 2024-04), base case
-- (G&A allocated by share of marketing spend, D-05) plus sensitivity columns.
SELECT
    period,
    segment,
    marketing_spend,
    new_paying_customers,
    gna_alloc_base_by_marketing_share,
    gna_alloc_sens_by_customer_share,
    gna_alloc_scenario_0pct,
    gna_alloc_scenario_25pct,
    gna_alloc_scenario_50pct,
    ROUND(marketing_spend / NULLIF(new_paying_customers, 0), 2) AS cac_marketing_only,
    ROUND((marketing_spend + gna_alloc_base_by_marketing_share) / NULLIF(new_paying_customers, 0), 2) AS cac_fully_loaded_base,
    ROUND((marketing_spend + gna_alloc_sens_by_customer_share) / NULLIF(new_paying_customers, 0), 2)  AS cac_fully_loaded_sens_customer_share,
    ROUND((marketing_spend + gna_alloc_scenario_0pct) / NULLIF(new_paying_customers, 0), 2)  AS cac_fully_loaded_scenario_0pct,
    ROUND((marketing_spend + gna_alloc_scenario_25pct) / NULLIF(new_paying_customers, 0), 2) AS cac_fully_loaded_scenario_25pct,
    ROUND((marketing_spend + gna_alloc_scenario_50pct) / NULLIF(new_paying_customers, 0), 2) AS cac_fully_loaded_scenario_50pct
FROM mart_a2_05_gna_allocation
WHERE segment IN ('B2C', 'SMB', 'Enterprise', 'Total')
ORDER BY period DESC,
    CASE segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'Total' THEN 5 END
