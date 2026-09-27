-- mart_a3_06_monthly_compounded_t12m: compounds the 12 monthly NDR/GRR rates from
-- mart_a3_05_monthly_ndr_series (2023-05-31 .. 2024-04-30) per segment and compares
-- the result with the snapshot T12M NDR/GRR from mart_a3_01_t12m_decomposition
-- (same base -- customers active 2023-04-30 -- evaluated the fixed-cohort way).
-- Approximation note (see results.md Open issues, proposed A-xx): compounding
-- monthly ratios treats each month's rolling base (customers active at the PRIOR
-- month-end) as if it were the same fixed cohort throughout, so new signups
-- entering/leaving the rolling base month to month mean this is NOT algebraically
-- identical to the fixed 12-month-lookback snapshot method (M-08); it is a
-- robustness comparison, not a reconciliation target.
WITH monthly AS (
    SELECT segment, month_end, ndr, grr
    FROM mart_a3_05_monthly_ndr_series
    WHERE month_end BETWEEN DATE '2023-05-31' AND DATE '2024-04-30'
),
compounded AS (
    SELECT
        segment,
        CAST(COUNT(*) AS BIGINT) AS n_months,
        EXP(SUM(LN(ndr)))        AS ndr_compounded,
        EXP(SUM(LN(grr)))        AS grr_compounded
    FROM monthly
    GROUP BY segment
)
SELECT
    c.segment,
    c.n_months,
    ROUND(c.ndr_compounded, 4)         AS ndr_compounded_monthly,
    ROUND(s.ndr, 4)                    AS ndr_snapshot_t12m,
    ROUND(c.ndr_compounded - s.ndr, 4) AS ndr_diff,
    ROUND(c.grr_compounded, 4)         AS grr_compounded_monthly,
    ROUND(s.grr, 4)                    AS grr_snapshot_t12m,
    ROUND(c.grr_compounded - s.grr, 4) AS grr_diff
FROM compounded c
JOIN mart_a3_01_t12m_decomposition s ON s.segment = c.segment
ORDER BY CASE c.segment WHEN 'B2C' THEN 1 WHEN 'SMB' THEN 2 WHEN 'Enterprise' THEN 3 WHEN 'B2B' THEN 4 WHEN 'Total' THEN 5 END
