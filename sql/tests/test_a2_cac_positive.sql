-- PASS if empty: fully loaded CAC (base case) must be a positive, non-null
-- number for every native segment over the full T16M period.
SELECT * FROM mart_a2_06_cac_fully_loaded
WHERE period = 'T16M'
  AND segment IN ('B2C', 'SMB', 'Enterprise', 'Total')
  AND (cac_fully_loaded_base IS NULL OR cac_fully_loaded_base <= 0)
