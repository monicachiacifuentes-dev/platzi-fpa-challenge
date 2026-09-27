-- PASS if this returns zero rows: grand total of active subs at 2024-04-30 must be 1,941
SELECT * FROM mart_q3_active_subs_apr24
WHERE segment = 'Total' AND plan_type = 'Total' AND active_subs <> 1941
