-- PASS if empty: for the Total segment row, both the base (all-by-MRR) and the
-- sensitivity (customer-weighted) allocated COGS must equal the company's
-- actual CS Salaries + Infrastructure + Content Production for that month
-- (allocation shares sum to 100% of company costs by construction, regardless
-- of the allocation method -- true for the Total row under either method), and
-- gross_profit = revenue - cogs_total, every month, for both columns.
SELECT month, segment, revenue, cogs_total_base, gross_profit_base,
       cogs_total_sens_customer_weighted, gross_profit_sens_customer_weighted,
       cs_salaries, infrastructure, content_production
FROM mart_a2_08_gm_monthly
WHERE segment = 'Total'
  AND (
      ABS(cogs_total_base - (cs_salaries + infrastructure + content_production)) > 0.05
      OR ABS(gross_profit_base - (revenue - cogs_total_base)) > 0.05
      OR ABS(cogs_total_sens_customer_weighted - (cs_salaries + infrastructure + content_production)) > 0.05
      OR ABS(gross_profit_sens_customer_weighted - (revenue - cogs_total_sens_customer_weighted)) > 0.05
  )
