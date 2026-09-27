-- WP31: backtest sanity bound -- the Base engine, calibrated on data through
-- 2023-10-31 and projected 6 months forward (Nov-23..Apr-24) with NO knowledge
-- of the actual outcome, should land within a generous 30% MAPE of actual
-- company MRR and active-customer counts (a flat-run-rate engine will
-- structurally under-shoot an accelerating company -- see results.md -- so
-- this is a loose credibility bound, not a tight-fit target).
-- Returns offending rows -> PASS means 0 rows.
SELECT segment, mape_mrr_pct, mape_customers_pct
FROM mart_s_06_backtest_summary
WHERE segment = 'Total' AND (mape_mrr_pct > 30 OR mape_customers_pct > 30)
