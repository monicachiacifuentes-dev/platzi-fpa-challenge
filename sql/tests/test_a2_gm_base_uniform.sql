-- PASS if empty: the BASE gross-margin case allocates 100% of COGS strictly by
-- share of MRR, which mathematically forces every native segment (B2C/SMB/
-- Enterprise) to the same GM% as the company average, for any given month
-- (this is the documented, expected property that motivates keeping the
-- customer-weighted allocation as a sensitivity instead -- see mart_a2_08 /
-- results.md "GM allocation"). Tolerance 0.0005 (rounding).
WITH per_month AS (
    SELECT month, MAX(gm_pct_base) AS max_gm, MIN(gm_pct_base) AS min_gm
    FROM mart_a2_08_gm_monthly
    WHERE segment IN ('B2C', 'SMB', 'Enterprise')
    GROUP BY month
)
SELECT * FROM per_month
WHERE ABS(max_gm - min_gm) > 0.0005
