-- mart_a3_08_renewal_pctchange_bins: distribution of % MRR change at renewal
-- (mrr_delta / prev_mrr) in bins, by segment. Same renewal-event population as
-- mart_a3_07_renewal_segmentation (period_number > 1, start_date in
-- 2023-05-01..2024-04-30).
WITH renewals AS (
    SELECT
        segment,
        mrr_delta / NULLIF(prev_mrr, 0) AS pct_change
    FROM fct_subscriptions
    WHERE period_number > 1
      AND start_date BETWEEN DATE '2023-05-01' AND DATE '2024-04-30'
),
binned AS (
    SELECT
        segment,
        CASE
            WHEN pct_change <= -0.20 THEN '1_<=-20%'
            WHEN pct_change <= -0.05 THEN '2_-20% to -5%'
            WHEN pct_change <  0     THEN '3_-5% to 0% (excl.)'
            WHEN pct_change  = 0     THEN '4_0% (flat)'
            WHEN pct_change <  0.05  THEN '5_0% to 5%'
            WHEN pct_change <  0.20  THEN '6_5% to 20%'
            ELSE '7_>=20%'
        END AS pct_change_bin
    FROM renewals
)
SELECT segment, pct_change_bin, CAST(COUNT(*) AS BIGINT) AS n_events
FROM binned
GROUP BY segment, pct_change_bin
ORDER BY segment, pct_change_bin
