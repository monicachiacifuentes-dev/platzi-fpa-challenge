-- PASS if empty: lifetime must be monotonically non-decreasing as the horizon
-- cap widens (Proposed A-18: 36 <= 60 <= uncapped), for both the logo and the
-- dollar curve, every segment. Tolerance 0.01 month (rounding).
SELECT * FROM mart_a2_11_lifetime
WHERE lifetime_logo_36   > lifetime_logo_60 + 0.01
   OR lifetime_logo_60   > lifetime_logo_uncapped + 0.01
   OR lifetime_dollar_36 > lifetime_dollar_60 + 0.01
   OR lifetime_dollar_60 > lifetime_dollar_uncapped + 0.01
