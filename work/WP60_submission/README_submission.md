# Platzi FP&A Take-Home: Submission

Prepared by **{{NAME}}** · Data: Jan 2023 – Apr 2024 (simulated datasets provided by Platzi)

## Start here
1. **`01_Executive_Summary.pdf`**: the 2-page summary for the CEO & CFO (findings, the 4 answers, recommendations, outlook).
2. **`02_Financial_Model.xlsx`**: the financial model (opens in Excel or as a Google Sheet).
3. **`03_Dashboards.md`**: links to the interactive dashboards (Streamlit and Looker Studio).

## How the deliverables map to the brief
| Brief requirement | Deliverable | What to look at |
|---|---|---|
| 1. Financial model: all calculations, formulas visible, assumptions labeled | `02_Financial_Model.xlsx` | Tab `README` (map & color legend: **blue = input**, black = formula, green = link) → `Assumptions` (every driver with an ID and source) → `UnitEconomics`, `Scenarios`, `Strategies` → `Checks` (**ALL CHECKS PASS**). The data work behind it is in SQL (`05_SQL/`). |
| 2. Executive summary, 1–2 pages | `01_Executive_Summary.pdf` | Bottom line, KPI strip, the 4 required answers, 4 findings, 3 ranked strategies with 6-month MRR/NDR impact, 12-month outlook, caveats |
| 3. Supporting visualizations | Embedded in the PDF + `04_Charts/` + dashboards | Streamlit (5 tabs, segment filter, interactive scenario sliders) and Looker Studio on BigQuery |

## Bonus sections covered
| Bonus | Where |
|---|---|
| SQL & data modeling | `05_SQL/`: a dbt-style DuckDB model (staging → intermediate → marts) with **31 automated tests**; the denormalized fact tables `fct_subscriptions`, `fct_customer_mrr_monthly` |
| Scenario modeling | `Scenarios` tab + `05_SQL/python_models/scenarios.py`: base / bull / bear 12-month MRR & subscribers, back-tested (≈10% MAPE) |
| Predictive model | Churn logistic regression, time-based validation, May-24 at-risk list (in the dashboard, *Churn risk* tab) |
| Dashboard | Streamlit (public link) + Looker Studio (see `03_Dashboards.md`) |
| Cloud warehouse | 49 tables loaded to **BigQuery**; the Apr-24 MRR recomputed there matches (`05_SQL/bigquery/`) |

## Quality
130 automated checks pass across the SQL model (31), the financial model (46, recomputed by a formula engine), the dashboard (9) and every figure quoted in the summary (44).

## Full reproducible project
Code, methodology, metric definitions and the detailed write-up of each analysis:
**https://github.com/monicachiacifuentes-dev/platzi-fpa-challenge**
