-- PASS if this returns zero rows: Q1 total MRR must equal sum of fct_customer_mrr_monthly at 2024-04-30
SELECT a.total_mrr_fct, b.total_mrr_q1, a.total_mrr_fct - b.total_mrr_q1 AS diff
FROM (SELECT SUM(mrr) AS total_mrr_fct FROM fct_customer_mrr_monthly WHERE month_end = DATE '2024-04-30') a
CROSS JOIN (SELECT mrr AS total_mrr_q1 FROM mart_q1_mrr_apr24 WHERE segment = 'Total') b
WHERE ABS(a.total_mrr_fct - b.total_mrr_q1) > 0.01
