-- int_month_spine: one row per calendar month-end from 2023-01-31 to 2024-04-30 (16 rows).
-- Portability note: generate_series over DATE with an INTERVAL step is DuckDB syntax.
-- BigQuery equivalent: GENERATE_DATE_ARRAY('2023-01-01','2024-04-01', INTERVAL 1 MONTH).
SELECT
    CAST(date_trunc('month', d) AS DATE)                                   AS month_start,
    CAST(date_trunc('month', d) + INTERVAL 1 MONTH - INTERVAL 1 DAY AS DATE) AS month_end
FROM generate_series(DATE '2023-01-01', DATE '2024-04-01', INTERVAL 1 MONTH) AS t(d)
ORDER BY 1
