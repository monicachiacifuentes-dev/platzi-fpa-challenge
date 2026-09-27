-- mart_q1_mrr_apr24: Q1 -- MRR at 2024-04-30 by segment, plus B2B roll-up and Total,
-- with % mix. Per M-01..M-04. Expected total ~= 204,709.09.
WITH by_segment AS (
    SELECT segment, SUM(mrr) AS mrr
    FROM fct_customer_mrr_monthly
    WHERE month_end = DATE '2024-04-30'
    GROUP BY segment
),
b2b AS (
    SELECT 'B2B' AS segment, SUM(mrr) AS mrr
    FROM fct_customer_mrr_monthly
    WHERE month_end = DATE '2024-04-30' AND customer_type = 'B2B'
),
total AS (
    SELECT 'Total' AS segment, SUM(mrr) AS mrr
    FROM fct_customer_mrr_monthly
    WHERE month_end = DATE '2024-04-30'
),
unioned AS (
    SELECT * FROM by_segment
    UNION ALL SELECT * FROM b2b
    UNION ALL SELECT * FROM total
)
SELECT
    segment,
    mrr,
    ROUND(100.0 * mrr / (SELECT mrr FROM total), 2) AS pct_of_total
FROM unioned
ORDER BY CASE segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'B2B' THEN 4 WHEN 'Total' THEN 5 END
