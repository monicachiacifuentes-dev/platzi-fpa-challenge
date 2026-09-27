-- WP31: Base scenario's first projected month (May-24) must open exactly on
-- the actual Apr-24 company MRR (M-01/M-03) -- i.e. the engine's starting
-- stock ties to mart_q1_mrr_apr24 / mart_mrr_bridge. Returns offending rows
-- (should be none) -> PASS means 0 rows.
SELECT scenario, segment, month_index, opening_mrr
FROM mart_s_02_projection_monthly
WHERE scenario = 'base' AND segment = 'Total' AND plan_type = 'ALL' AND month_index = 1
  AND ABS(opening_mrr - 204709.09) > 0.5
