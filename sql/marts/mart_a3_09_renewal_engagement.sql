-- mart_a3_09_renewal_engagement: engagement (active_days, courses_seen) of the
-- period that ENDED -- i.e. the period immediately before the renewal, whose
-- behaviour presumably drove the renewal outcome -- by segment x renewal_change.
-- Same renewal-event population as mart_a3_07/08. The LAG window runs over the
-- FULL subscription history per user (not pre-filtered) so the "ended period" is
-- always the true immediately-preceding period, then the result is filtered down
-- to renewal events in the 2023-05-01..2024-04-30 window.
WITH ordered AS (
    SELECT
        user_id, segment, start_date, period_number, renewal_change,
        LAG(active_days)  OVER (PARTITION BY user_id ORDER BY start_date) AS ended_active_days,
        LAG(courses_seen) OVER (PARTITION BY user_id ORDER BY start_date) AS ended_courses_seen
    FROM fct_subscriptions
),
renewals AS (
    SELECT *
    FROM ordered
    WHERE period_number > 1
      AND start_date BETWEEN DATE '2023-05-01' AND DATE '2024-04-30'
)
SELECT
    segment,
    renewal_change,
    CAST(COUNT(*) AS BIGINT)              AS n_events,
    ROUND(AVG(ended_active_days), 2)      AS avg_ended_active_days,
    ROUND(AVG(ended_courses_seen), 2)     AS avg_ended_courses_seen
FROM renewals
GROUP BY segment, renewal_change
ORDER BY segment, renewal_change
