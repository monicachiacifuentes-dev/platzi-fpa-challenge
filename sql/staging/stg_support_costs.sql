-- stg_support_costs: month (YYYY-MM string) -> DATE of first day of month
SELECT
    CAST(trim(CAST(month AS VARCHAR)) || '-01' AS DATE) AS month,
    trim(category)          AS category,
    CAST(amount AS DOUBLE)  AS amount
FROM raw_support_costs
