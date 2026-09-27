-- PASS if zero rows: the T12M and T6M waterfall long-format tables (mart_a3_02,
-- mart_a3_04) reconstruct to End MRR = Start - Churn - Contraction + Expansion,
-- for every segment.
WITH t12m AS (
    SELECT segment,
           SUM(CASE WHEN step = 'Start MRR'   THEN amount END) AS start_amt,
           SUM(CASE WHEN step = 'Churn'       THEN amount END) AS churn_amt,
           SUM(CASE WHEN step = 'Contraction' THEN amount END) AS contraction_amt,
           SUM(CASE WHEN step = 'Expansion'   THEN amount END) AS expansion_amt,
           SUM(CASE WHEN step = 'End MRR'     THEN amount END) AS end_amt
    FROM mart_a3_02_t12m_waterfall_long
    GROUP BY segment
),
t6m AS (
    SELECT segment,
           SUM(CASE WHEN step = 'Start MRR'   THEN amount END) AS start_amt,
           SUM(CASE WHEN step = 'Churn'       THEN amount END) AS churn_amt,
           SUM(CASE WHEN step = 'Contraction' THEN amount END) AS contraction_amt,
           SUM(CASE WHEN step = 'Expansion'   THEN amount END) AS expansion_amt,
           SUM(CASE WHEN step = 'End MRR'     THEN amount END) AS end_amt
    FROM mart_a3_04_t6m_waterfall_long
    GROUP BY segment
),
unioned AS (
    SELECT * FROM t12m
    UNION ALL
    SELECT * FROM t6m
)
SELECT *
FROM unioned
WHERE ABS(start_amt + churn_amt + contraction_amt + expansion_amt - end_amt) > 0.01
