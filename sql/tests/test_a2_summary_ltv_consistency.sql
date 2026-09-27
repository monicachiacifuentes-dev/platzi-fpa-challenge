-- PASS if empty: mart_a2_12's base-case lifetime must match mart_a2_11's
-- lifetime_dollar_60 (Proposed A-18 base cap) exactly, and ltv_base must equal
-- arpa_t6m_avg x gm_pct_t6m_base x lifetime_dollar_months. Tolerance $2.00 for
-- ltv_base: mart_a2_12 rounds arpa/gm%/lifetime to 2/4/2 decimals BEFORE
-- multiplying (so the stored ltv_base is computed from unrounded intermediates),
-- while this recomputation multiplies the already-rounded, displayed values --
-- the resulting cents-level drift is a display-rounding artifact, not a bug.
SELECT s.segment, s.lifetime_dollar_months, l.lifetime_dollar_60, s.ltv_base,
       s.arpa_t6m_avg * s.gm_pct_t6m_base * s.lifetime_dollar_months AS recomputed_ltv
FROM mart_a2_12_unit_economics_summary s
JOIN mart_a2_11_lifetime l ON l.segment = s.segment
WHERE ABS(s.lifetime_dollar_months - l.lifetime_dollar_60) > 0.01
   OR ABS(s.ltv_base - s.arpa_t6m_avg * s.gm_pct_t6m_base * s.lifetime_dollar_months) > 2.00
