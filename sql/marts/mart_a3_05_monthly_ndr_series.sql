-- mart_a3_05_monthly_ndr_series: month-over-month NDR/GRR by segment (+B2B+Total).
-- Base each month = customers active at the PRIOR month-end (prev_mrr > 0 in
-- fct_customer_mrr_monthly, i.e. M-08's snapshot method applied to a 1-month window
-- instead of 12); end = their MRR at this month-end (0 if churned in between).
-- Covers every available month transition (2023-02-28 .. 2024-04-30, 15 rows per
-- segment); 2023-05-31..2024-04-30 is the 12-transition window compounded into a
-- T12M figure by mart_a3_06_monthly_compounded_t12m.
WITH base AS (
    SELECT month_end, segment, customer_type, prev_mrr AS start_mrr, mrr AS end_mrr
    FROM fct_customer_mrr_monthly
    WHERE prev_mrr > 0
),
expanded AS (
    SELECT month_end, segment AS segment_group, start_mrr, end_mrr FROM base
    UNION ALL
    SELECT month_end, 'B2B', start_mrr, end_mrr FROM base WHERE customer_type = 'B2B'
    UNION ALL
    SELECT month_end, 'Total', start_mrr, end_mrr FROM base
)
SELECT
    month_end,
    segment_group AS segment,
    CAST(COUNT(*) AS BIGINT)                                                    AS base_customers,
    SUM(start_mrr)                                                              AS start_mrr,
    SUM(CASE WHEN end_mrr > start_mrr THEN end_mrr - start_mrr ELSE 0 END)      AS expansion_mrr,
    SUM(CASE WHEN end_mrr > 0 AND end_mrr < start_mrr THEN start_mrr - end_mrr ELSE 0 END) AS contraction_mrr,
    SUM(CASE WHEN end_mrr = 0 THEN start_mrr ELSE 0 END)                        AS churn_mrr,
    SUM(end_mrr)                                                                AS end_mrr,
    ROUND(SUM(end_mrr) / NULLIF(SUM(start_mrr), 0), 4)                          AS ndr,
    ROUND(SUM(LEAST(end_mrr, start_mrr)) / NULLIF(SUM(start_mrr), 0), 4)        AS grr
FROM expanded
GROUP BY month_end, segment_group
ORDER BY segment_group, month_end
