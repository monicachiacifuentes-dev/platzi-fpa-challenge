-- PASS if zero rows: mart_a3_07's renewal-event expansion/contraction totals tie
-- to mart_q4_ndr_t12m's renewal_crosscheck method, by (native) segment. Confirms
-- the WP22 renewal-event view reproduces WP13's cross-check population exactly.
WITH a3 AS (
    SELECT segment,
           SUM(expansion_amt)   AS expansion_mrr,
           SUM(contraction_amt) AS contraction_mrr
    FROM mart_a3_07_renewal_segmentation
    GROUP BY segment
)
SELECT a3.segment, a3.expansion_mrr, q.expansion_mrr, a3.contraction_mrr, q.contraction_mrr
FROM a3
JOIN mart_q4_ndr_t12m q ON q.segment = a3.segment AND q.method = 'renewal_crosscheck'
WHERE ABS(a3.expansion_mrr - q.expansion_mrr) > 0.01
   OR ABS(a3.contraction_mrr - q.contraction_mrr) > 0.01
