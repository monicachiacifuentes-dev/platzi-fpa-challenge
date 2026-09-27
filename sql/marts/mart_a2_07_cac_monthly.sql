-- mart_a2_07_cac_monthly: WP21 -- month x segment CAC table (deliverable
-- requirement: "a monthly CAC table by segment"). Marketing-spend-only (no G&A
-- allocation at monthly grain -- G&A allocation is only meaningful pooled over
-- a period, D-05/mart_a2_05/06; single-month Enterprise/SMB customer counts are
-- small and can be zero, so this view is noisy by design -- see results.md).
SELECT
    m.month,
    m.segment,
    m.marketing_spend,
    c.new_paying_customers,
    ROUND(m.marketing_spend / NULLIF(c.new_paying_customers, 0), 2) AS cac_marketing_only
FROM mart_a2_02_marketing_spend_segment_monthly m
JOIN mart_a2_01_new_paying_customers c
    ON c.month = m.month AND c.segment = m.segment
WHERE m.segment IN ('B2C', 'SMB', 'Enterprise', 'B2B', 'Total')
ORDER BY m.month,
    CASE m.segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'B2B' THEN 4 WHEN 'Total' THEN 5 END
