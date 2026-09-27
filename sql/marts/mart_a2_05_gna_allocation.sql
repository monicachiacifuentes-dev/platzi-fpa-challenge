-- mart_a2_05_gna_allocation: WP21 -- D-05 G&A allocation to acquisition (CAC).
-- acquisition_share_of_gna = total marketing spend / (total marketing spend +
-- total support costs [CS Salaries + Infrastructure + Content Production]),
-- applied to total G&A -> allocated_gna_pool. Split to segments:
--   gna_alloc_base           : by segment's share of marketing spend (base, per D-05/brief)
--   gna_alloc_sens_customers : sensitivity -- by segment's share of new paying customers
-- Plus a fixed-percentage sensitivity table (0% / 25% / 50% of G&A allocated to
-- acquisition, still split across segments by share of marketing spend).
-- Two periods: T16M (all 16 months) and T6M (2023-11 .. 2024-04).
WITH mkt AS (
    SELECT month, segment, marketing_spend
    FROM mart_a2_02_marketing_spend_segment_monthly
),
cust AS (
    SELECT month, segment, new_paying_customers
    FROM mart_a2_01_new_paying_customers
),
support AS (
    SELECT month, category, amount FROM stg_support_costs
),
mkt_p AS (
    SELECT 'T16M' AS period, segment, SUM(marketing_spend) AS marketing_spend FROM mkt GROUP BY segment
    UNION ALL
    SELECT 'T6M' AS period, segment, SUM(marketing_spend) AS marketing_spend FROM mkt
    WHERE month BETWEEN DATE '2023-11-01' AND DATE '2024-04-01' GROUP BY segment
),
cust_p AS (
    SELECT 'T16M' AS period, segment, SUM(new_paying_customers) AS new_paying_customers FROM cust GROUP BY segment
    UNION ALL
    SELECT 'T6M' AS period, segment, SUM(new_paying_customers) AS new_paying_customers FROM cust
    WHERE month BETWEEN DATE '2023-11-01' AND DATE '2024-04-01' GROUP BY segment
),
support_p AS (
    SELECT 'T16M' AS period,
           SUM(CASE WHEN category IN ('CS Salaries', 'Infrastructure', 'Content Production') THEN amount ELSE 0 END) AS total_support_costs_non_gna,
           SUM(CASE WHEN category = 'G&A' THEN amount ELSE 0 END) AS total_gna
    FROM support
    UNION ALL
    SELECT 'T6M' AS period,
           SUM(CASE WHEN category IN ('CS Salaries', 'Infrastructure', 'Content Production') THEN amount ELSE 0 END) AS total_support_costs_non_gna,
           SUM(CASE WHEN category = 'G&A' THEN amount ELSE 0 END) AS total_gna
    FROM support
    WHERE month BETWEEN DATE '2023-11-01' AND DATE '2024-04-01'
),
company AS (
    SELECT
        s.period,
        (SELECT marketing_spend FROM mkt_p WHERE mkt_p.period = s.period AND segment = 'Total') AS total_marketing_spend,
        (SELECT new_paying_customers FROM cust_p WHERE cust_p.period = s.period AND segment = 'Total') AS total_new_customers,
        s.total_support_costs_non_gna,
        s.total_gna
    FROM support_p s
),
joined AS (
    SELECT
        m.period,
        m.segment,
        m.marketing_spend,
        c.new_paying_customers,
        co.total_marketing_spend,
        co.total_new_customers,
        co.total_support_costs_non_gna,
        co.total_gna,
        ROUND(co.total_marketing_spend / NULLIF(co.total_marketing_spend + co.total_support_costs_non_gna, 0), 4) AS acquisition_share_of_gna,
        co.total_marketing_spend / NULLIF(co.total_marketing_spend + co.total_support_costs_non_gna, 0) * co.total_gna AS allocated_gna_pool
    FROM mkt_p m
    JOIN cust_p c ON c.period = m.period AND c.segment = m.segment
    JOIN company co ON co.period = m.period
    WHERE m.segment IN ('B2C', 'SMB', 'Enterprise', 'Total')
)
SELECT
    period,
    segment,
    marketing_spend,
    new_paying_customers,
    total_marketing_spend,
    total_new_customers,
    total_support_costs_non_gna,
    total_gna,
    acquisition_share_of_gna,
    allocated_gna_pool,
    ROUND(allocated_gna_pool * marketing_spend / NULLIF(total_marketing_spend, 0), 2)      AS gna_alloc_base_by_marketing_share,
    ROUND(allocated_gna_pool * new_paying_customers / NULLIF(total_new_customers, 0), 2)   AS gna_alloc_sens_by_customer_share,
    ROUND(0.00 * total_gna * marketing_spend / NULLIF(total_marketing_spend, 0), 2)        AS gna_alloc_scenario_0pct,
    ROUND(0.25 * total_gna * marketing_spend / NULLIF(total_marketing_spend, 0), 2)        AS gna_alloc_scenario_25pct,
    ROUND(0.50 * total_gna * marketing_spend / NULLIF(total_marketing_spend, 0), 2)        AS gna_alloc_scenario_50pct
FROM joined
ORDER BY period DESC,
    CASE segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'Total' THEN 5 END
