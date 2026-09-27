-- mart_a2_08_gm_monthly: WP21 -- M-12 gross margin by segment x month.
-- Revenue = MRR (M-03) from fct_customer_mrr_monthly.
-- COGS = CS Salaries + Infrastructure + Content Production (support_costs.csv;
-- G&A excluded here -- it goes to CAC per D-05/M-13, not COGS).
--
-- REVISED base case (lead-analyst review, see results.md "GM allocation"):
--   BASE (neutral default, no cost-driver data available): ALL THREE categories
--   allocated by segment's share of MRR that month. This is allocation-neutral
--   by construction -- it cannot, by itself, show any segment as more or less
--   profitable than the company average (see gm_pct_base identity below) -- but
--   it avoids an indefensible assumption (that a B2C learner consumes as much
--   support/infra as an Enterprise account) that the previous base produced.
--   DOWNSIDE SENSITIVITY ("_sens_customer_weighted"): CS Salaries & Infrastructure
--   by segment's share of ACTIVE CUSTOMERS (a customer-count cost driver, e.g. if
--   support headcount scales with ticket/customer volume rather than revenue);
--   Content Production stays by MRR share in both cases (identical, one column).
--   This was the OLD base case (Proposed D-07 update, now demoted to sensitivity)
--   -- it drove B2C to a -37% GM% because B2C is ~79% of active customers but
--   only ~31% of revenue; kept as the explicit downside case, not the default.
WITH seg_month AS (
    SELECT month_end AS month, segment, customer_type,
           SUM(mrr) AS revenue,
           SUM(CASE WHEN mrr > 0 THEN 1 ELSE 0 END) AS active_customers
    FROM fct_customer_mrr_monthly
    GROUP BY month_end, segment, customer_type
),
seg_month_expanded AS (
    SELECT month, segment AS segment_group, revenue, active_customers FROM seg_month
    UNION ALL
    SELECT month, 'B2B' AS segment_group, revenue, active_customers FROM seg_month WHERE customer_type = 'B2B'
    UNION ALL
    SELECT month, 'Total' AS segment_group, revenue, active_customers FROM seg_month
),
seg_agg AS (
    SELECT month, segment_group, SUM(revenue) AS revenue, SUM(active_customers) AS active_customers
    FROM seg_month_expanded
    GROUP BY month, segment_group
),
company AS (
    SELECT month, revenue AS total_revenue, active_customers AS total_active_customers
    FROM seg_agg WHERE segment_group = 'Total'
),
costs AS (
    SELECT month,
           SUM(CASE WHEN category = 'CS Salaries' THEN amount ELSE 0 END)          AS cs_salaries,
           SUM(CASE WHEN category = 'Infrastructure' THEN amount ELSE 0 END)       AS infrastructure,
           SUM(CASE WHEN category = 'Content Production' THEN amount ELSE 0 END)  AS content_production
    FROM stg_support_costs
    GROUP BY month
)
SELECT
    s.month,
    s.segment_group AS segment,
    s.revenue,
    s.active_customers,
    co.cs_salaries,
    co.infrastructure,
    co.content_production,
    -- Content Production: always by MRR share (same in base and sensitivity)
    ROUND(co.content_production * s.revenue / NULLIF(c.total_revenue, 0), 2) AS cogs_content,
    -- BASE (neutral): all three categories by MRR share
    ROUND(co.cs_salaries    * s.revenue / NULLIF(c.total_revenue, 0), 2) AS cogs_cs_salaries_base,
    ROUND(co.infrastructure * s.revenue / NULLIF(c.total_revenue, 0), 2) AS cogs_infrastructure_base,
    ROUND(
        (co.cs_salaries + co.infrastructure + co.content_production) * s.revenue / NULLIF(c.total_revenue, 0)
    , 2) AS cogs_total_base,
    ROUND(
        s.revenue - (co.cs_salaries + co.infrastructure + co.content_production) * s.revenue / NULLIF(c.total_revenue, 0)
    , 2) AS gross_profit_base,
    ROUND(
        (s.revenue - (co.cs_salaries + co.infrastructure + co.content_production) * s.revenue / NULLIF(c.total_revenue, 0))
        / NULLIF(s.revenue, 0)
    , 4) AS gm_pct_base,
    -- DOWNSIDE SENSITIVITY: CS Salaries & Infrastructure by active-customer share
    ROUND(co.cs_salaries    * s.active_customers / NULLIF(c.total_active_customers, 0), 2) AS cogs_cs_salaries_sens_customer_weighted,
    ROUND(co.infrastructure * s.active_customers / NULLIF(c.total_active_customers, 0), 2) AS cogs_infrastructure_sens_customer_weighted,
    ROUND(
        co.cs_salaries    * s.active_customers / NULLIF(c.total_active_customers, 0)
      + co.infrastructure * s.active_customers / NULLIF(c.total_active_customers, 0)
      + co.content_production * s.revenue / NULLIF(c.total_revenue, 0)
    , 2) AS cogs_total_sens_customer_weighted,
    ROUND(
        s.revenue - (
            co.cs_salaries    * s.active_customers / NULLIF(c.total_active_customers, 0)
          + co.infrastructure * s.active_customers / NULLIF(c.total_active_customers, 0)
          + co.content_production * s.revenue / NULLIF(c.total_revenue, 0)
        )
    , 2) AS gross_profit_sens_customer_weighted,
    ROUND(
        (s.revenue - (
            co.cs_salaries    * s.active_customers / NULLIF(c.total_active_customers, 0)
          + co.infrastructure * s.active_customers / NULLIF(c.total_active_customers, 0)
          + co.content_production * s.revenue / NULLIF(c.total_revenue, 0)
        )) / NULLIF(s.revenue, 0)
    , 4) AS gm_pct_sens_customer_weighted
FROM seg_agg s
JOIN company c ON c.month = s.month
JOIN costs co ON co.month = date_trunc('month', s.month)::DATE
WHERE s.segment_group IN ('B2C', 'SMB', 'Enterprise', 'B2B', 'Total')
ORDER BY s.month,
    CASE s.segment_group WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'B2B' THEN 4 WHEN 'Total' THEN 5 END
