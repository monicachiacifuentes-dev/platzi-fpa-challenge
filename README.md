# Platzi FP&A Take-Home Challenge

An end-to-end FP&A analysis of a B2C + B2B subscription EdTech business (simulated data, Jan 2023 – Apr 2024): the MRR, retention, NDR, cohort, unit-economics, churn-risk and scenario analyses, delivered as a reproducible SQL data model, a verified financial model, dashboards and a 2-page executive summary.

## Deliverables
| Deliverable | Where |
|---|---|
| **Executive summary** (2 pages, for the CEO/CFO) | [`outputs/Platzi_FPA_Executive_Summary.pdf`](outputs/Platzi_FPA_Executive_Summary.pdf) |
| **Financial model**: assumptions, unit economics, scenarios, with formulas visible; opens as a Google Sheet | [`outputs/Platzi_FPA_Model.xlsx`](outputs/Platzi_FPA_Model.xlsx) |
| **Interactive dashboard** (Streamlit) | `app/streamlit_app.py` (live link: *add after deploying*) |
| **Looker Studio dashboard** on BigQuery | build guide: [`outputs/Looker_Studio_Guide.md`](outputs/Looker_Studio_Guide.md) |
| **SQL data model** (dbt-style: staging → intermediate → marts, 31 tests) | [`sql/`](sql/README.md) |
| **Charts** | [`outputs/charts/`](outputs/charts/) |

## Headline results
- **MRR, Apr-24: $204,709** (B2C $64.4k · SMB $53.9k · Enterprise $86.5k); **1,941** active subscribers.
- **Q1-24 retention: 90.1%** (B2C 89.6% vs. B2B 93.8%). **NDR, trailing 12 months: 63.7%** (81.6% on a trailing 6-month base).
- **LTV:CAC**: B2C 0.5–0.7× · SMB 2.9–4.1× · Enterprise 2.2–3.0×. B2B carries the economics; paid B2C acquisition doesn't pay back.
- **Churn is predictable within the billing period** (engagement). A mid-cycle alert-and-save program is the top recommendation (+$7.7k MRR in 6 months).

## How it's built
```
CSVs ─► DuckDB (sql/run_pipeline.py: staging → intermediate → marts + tests + Python models)
          ├─► outputs/marts/*.csv ─► Streamlit app · financial model (xlsx) · charts
          └─► BigQuery (sql/bigquery/load_to_bigquery.ps1) ─► Looker Studio
```
Quality: 130 automated checks pass (SQL 31 · model 46 · app 9 · summary figures 44). See [`work/WP50_qa/results.md`](work/WP50_qa/results.md).
Methodology, metric definitions and every assumption: [`Docs/Plan_and_Index.md`](Docs/Plan_and_Index.md). Detailed results for each analysis: `work/WP*/results.md`.

## Run it locally
```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Windows paths
# The raw data is not included (Platzi's challenge materials): put the 7 CSVs in Docs/Originals/
.venv/Scripts/python sql/run_pipeline.py            # rebuilds db/platzi.duckdb + outputs/marts/
.venv/Scripts/streamlit run app/streamlit_app.py    # dashboard at http://localhost:8501
```
The Streamlit app only needs `outputs/marts/` (included), so it runs without the raw data.

## Deploy the dashboard (Streamlit Community Cloud)
share.streamlit.io → Create app → this repository → branch `main` → main file **`app/streamlit_app.py`** → Deploy.
