-- PASS if empty: at k=0 (signup month) nearly every customer is active with
-- mrr = mrr_at_0 (dollar_retention = 1.0 exactly, by construction). logo_survival
-- is allowed a small tolerance below 1.0: a handful of subscriptions (4 of 2,695,
-- verified) start and churn within the same calendar month with end_date landing
-- exactly on that month's last day, so M-02's strict "start <= D < end" excludes
-- them from "active" at their own signup month-end -- a genuine artifact of the
-- M-02 definition applied at k=0, not a bug (see results.md).
SELECT * FROM mart_a2_10_survival_curve
WHERE k = 0
  AND (logo_survival < 0.99 OR ABS(dollar_retention - 1.0) > 0.0001)
