# Platzi FP&A Dashboard (WP33, bonus B4)

Streamlit app over the DuckDB pipeline's CSV exports (`outputs/marts/*.csv`). It is
read-only: no database connection, no writes anywhere except the browser session.

## Run locally

```bash
export PYTHONIOENCODING=utf-8
./.venv/Scripts/streamlit run app/streamlit_app.py
```

Then open the URL Streamlit prints (default `http://localhost:8501`).

Requirements (already in the project `.venv`): `streamlit`, `pandas`, `plotly`,
`numpy`. A minimal `app/requirements.txt` is provided for a clean environment.

## Deploy free on Streamlit Community Cloud

1. Push this repo to a GitHub repository, **including** `outputs/marts/*.csv`
   (the app's only data source) and the `app/` folder. `db/platzi.duckdb` is
   NOT needed and should not be pushed (it's large and the app never reads it).
2. Go to [share.streamlit.io](https://share.streamlit.io) -> **New app**.
3. Point it at this repo/branch, main file path: `app/streamlit_app.py`.
4. Community Cloud auto-installs `app/requirements.txt` if it's the closest
   `requirements.txt` to the main file (Streamlit Cloud searches the main
   file's directory first). If it picks up the repo-root `requirements.txt`
   instead, either remove/rename it for the deploy or set the app's
   "Advanced settings -> requirements file" to `app/requirements.txt`.
5. Deploy. First boot takes ~1-2 minutes.

## Data sources

Every chart reads directly from `outputs/marts/*.csv` (produced by
`sql/run_pipeline.py`, already checked into the repo). No new CSVs were needed
for this app -- every table the dashboard uses already had a mart export. See
`work/WP33_dashboard/results.md` for the exact file-to-chart mapping.

The one exception is the "Interactive projection" panel in the Scenarios tab,
which re-derives its starting inputs from `outputs/marts/mart_s_01_drivers.csv`
and `outputs/marts/fct_subscriptions.csv` (both plain CSVs) and reuses the pure
`simulate()` function from `sql/python_models/scenarios.py` -- still no
database access.

## Tests

```bash
export PYTHONIOENCODING=utf-8
./.venv/Scripts/python.exe -m pytest app/test_app.py -v
```

Uses `streamlit.testing.v1.AppTest` to load the app, exercise every segment
filter and toggle, and assert headline KPIs (MRR $204,709, 1,941 active subs)
match the executive summary.
