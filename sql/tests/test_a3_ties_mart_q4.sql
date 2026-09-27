-- PASS if zero rows: mart_a3_01's T12M snapshot ties exactly to
-- mart_q4_ndr_t12m (method='M08_M09_M10') on every $ and rate column, for every
-- segment (B2C, SMB, Enterprise, B2B, Total).
SELECT a.segment,
       a.base_customers, q.base_customers,
       a.start_mrr, q.start_mrr,
       a.expansion_mrr, q.expansion_mrr,
       a.contraction_mrr, q.contraction_mrr,
       a.churn_mrr, q.churn_mrr,
       a.end_mrr, q.end_mrr,
       a.ndr, q.ndr,
       a.grr, q.grr
FROM mart_a3_01_t12m_decomposition a
JOIN mart_q4_ndr_t12m q
  ON q.segment = a.segment AND q.method = 'M08_M09_M10'
WHERE a.base_customers <> q.base_customers
   OR ABS(a.start_mrr - q.start_mrr) > 0.01
   OR ABS(a.expansion_mrr - q.expansion_mrr) > 0.01
   OR ABS(a.contraction_mrr - q.contraction_mrr) > 0.01
   OR ABS(a.churn_mrr - q.churn_mrr) > 0.01
   OR ABS(a.end_mrr - q.end_mrr) > 0.01
   OR ABS(a.ndr - q.ndr) > 0.0002
   OR ABS(a.grr - q.grr) > 0.0002
