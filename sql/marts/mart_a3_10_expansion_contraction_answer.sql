-- mart_a3_10_expansion_contraction_answer: segment-level summary answering "which
-- segment drives the most expansion revenue, and where does contraction
-- concentrate?" -- from the larger renewal-event population (mart_a3_07, all
-- renewals in the window) plus the T12M snapshot cohort (mart_a3_01, 417
-- customers) for cross-reference. Expansion/contraction $ are also shown as a %
-- of that segment's own MRR at 2024-04-30 (mart_q1_mrr_apr24) for scale context.
WITH renewal_agg AS (
    SELECT
        segment,
        SUM(expansion_amt)                                                        AS renewal_expansion_mrr,
        SUM(contraction_amt)                                                      AS renewal_contraction_mrr,
        SUM(CASE WHEN renewal_change = 'expansion'   THEN n_events ELSE 0 END)     AS n_expansion_events,
        SUM(CASE WHEN renewal_change = 'contraction' THEN n_events ELSE 0 END)     AS n_contraction_events
    FROM mart_a3_07_renewal_segmentation
    GROUP BY segment
),
cohort AS (
    SELECT segment, expansion_mrr AS cohort_expansion_mrr, contraction_mrr AS cohort_contraction_mrr
    FROM mart_a3_01_t12m_decomposition
    WHERE segment IN ('B2C', 'SMB', 'Enterprise')
),
current_mrr AS (
    SELECT segment, mrr AS current_mrr_apr24
    FROM mart_q1_mrr_apr24
    WHERE segment IN ('B2C', 'SMB', 'Enterprise')
)
SELECT
    r.segment,
    r.n_expansion_events,
    r.renewal_expansion_mrr,
    r.n_contraction_events,
    r.renewal_contraction_mrr,
    c.cohort_expansion_mrr,
    c.cohort_contraction_mrr,
    m.current_mrr_apr24,
    ROUND(100.0 * r.renewal_expansion_mrr   / NULLIF(m.current_mrr_apr24, 0), 2) AS renewal_expansion_pct_of_current_mrr,
    ROUND(100.0 * r.renewal_contraction_mrr / NULLIF(m.current_mrr_apr24, 0), 2) AS renewal_contraction_pct_of_current_mrr
FROM renewal_agg r
JOIN cohort c      ON c.segment = r.segment
JOIN current_mrr m ON m.segment = r.segment
ORDER BY CASE r.segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 END
