# WP33 — Bonus B4: Streamlit executive dashboard

## Answer (numbers first)

Built `app/streamlit_app.py`, a single-file Streamlit app with 5 tabs and one
sidebar segment filter (All / B2C / SMB / Enterprise) that scopes every chart
and table. It reads **only** `outputs/marts/*.csv` (no database connection, no
writes) — every mart the dashboard needed already had a CSV export from the
WP30 DuckDB pipeline, so no `app/export_data.py` / `app/data/` was necessary.

Headline numbers reproduced in the app (All-segments view), reconciled to
`outputs/Platzi_FPA_Executive_Summary.html`:

| KPI | App value | Exec summary |
|---|---:|---:|
| MRR, Apr-24 | $204,709 | $204.7k |
| Active subscriptions | 1,941 | 1,941 |
| Q1-24 retention (logo) | 90.1% | 90.1% |
| NDR, trailing 12 mo | 63.7% (caption: T6M 81.6%) | 63.7% (T6M 81.6%) |
| Gross margin, Apr-24 | 40.9% | 41% |

Segment-scoped KPIs also reconcile exactly to the marts (tested, see below):
MRR B2C $64,365 / SMB $53,869 / Enterprise $86,475; subs 1,536 / 303 / 102.

## App structure

```
app/
├── streamlit_app.py   -- the app (single file, st.tabs)
├── requirements.txt   -- streamlit, pandas, plotly, numpy
├── README.md          -- run / deploy instructions
└── test_app.py        -- streamlit.testing.v1.AppTest verification suite
```

**Sidebar:** one radio filter, `All / B2C / SMB / Enterprise`, mapped to the
mart's own rollup rows (`Total`, `B2C`, `SMB`, `Enterprise` — every mart used
already carries these four rows, so no re-aggregation was needed anywhere
except the interactive scenario panel and the in-period-engagement chart,
noted below).

### Tab 1 — Overview
- KPI tiles: MRR Apr-24, active subs, Q1-24 logo retention (dollar rate in the
  tooltip), NDR T12M (T6M in the tooltip), GM Apr-24.
- MRR by segment: stacked monthly bars, segment colors fixed.
- MRR bridge: monthly new / expansion / contraction / churn (stacked, signed)
  + a closing-MRR line overlay.
- Sources: `mart_mrr_bridge.csv`, `mart_q3_active_subs_apr24.csv`,
  `mart_q2_retention_q1_24.csv`, `mart_q4_ndr_t12m.csv`,
  `mart_a3_03_t6m_decomposition.csv`, `mart_a2_08_gm_monthly.csv`.

### Tab 2 — Retention
- Cohort retention heatmap (logo / $ toggle) from `mart_a1_01_cohort_retention.csv`.
- NDR waterfall (T12M / T6M toggle) from `mart_a3_02_t12m_waterfall_long.csv` /
  `mart_a3_04_t6m_waterfall_long.csv` (Plotly native `Waterfall` trace).
- Churn rate by in-period engagement bucket, recomputed live from
  `mart_a1_03_churn_indicators_base.csv` (has `segment` + `active_days_bucket`
  + `churned`, so it can be scoped by the sidebar filter — verified it
  reproduces `mart_a1_04_churn_rate_by_bucket.csv`'s company-wide numbers
  exactly when unfiltered: e.g. bucket 0-5 n=612, churn=50.8%). Simulated-data
  caveat shown as a `st.warning` (D-18).

### Tab 3 — Unit economics
- LTV:CAC by segment, 3× benchmark line, GM-basis toggle (T6M 29.3% base vs.
  Apr-24 40.9% run-rate, D-17) from `mart_a2_12_unit_economics_summary.csv`.
- CAC & payback table (T6M / T16M, benchmark pass/fail flags), same mart.
- Acquisition funnel (sign-ups → paying customers, Plotly `Funnel`), T6M
  aggregate from `mart_a2_03_funnel_segment_monthly.csv`.
- Sensitivity table from `mart_a2_13_sensitivity.csv`.

### Tab 4 — Churn risk (May-24)
- Tier summary (count, MRR, expected churned MRR = Σ mrr×prob_churn) by
  tier × segment, from `mart_a1_06_may24_churn_risk.csv`.
- Filterable at-risk table (tier multiselect, sorted by probability) with a
  `main_driver` column derived in-app as `argmax` across the mart's
  `contrib_*` columns (the mart has per-feature logit contributions but no
  single "driver" label — see D-26 below) and a CSV download button.

### Tab 5 — Scenarios & strategies
- Base/bull/bear MRR chart (actual + 12-month projection) from
  `mart_mrr_bridge.csv` + `mart_s_02_projection_monthly.csv`, ink actuals /
  blue ramp scenarios, matching `work/WP41_charts/make_charts.py`'s c2 chart.
- Scenario summary table (`mart_s_03_scenario_summary.csv`) and strategy
  impact table (`mart_s_04_strategy_impact.csv`, case selector low/base/high).
- **Interactive projection:** sliders for monthly churn multiplier, new-
  customers/month multiplier, and save rate, recomputed live. Reuses the
  official engine's pure `simulate()` / `add_rollups()` / `default_params()`
  from `sql/python_models/scenarios.py` (no `duckdb` import at module load
  time, so importing it needs no database). The `base` calibration dict it
  needs is rebuilt from two CSVs instead of `calibrate(con, ...)`:
  `mart_s_01_drivers.csv` (churn/expansion/contraction/ARPA/plan-mix rates)
  and `fct_subscriptions.csv` (Apr-24 opening stock by segment × plan,
  replicating the engine's own `stock_df` query in pandas). Labeled
  "**Simplified**; reuses the pure simulation step of the official engine…
  the official base/bull/bear scenarios and backtest are the table above" per
  the brief.

## Method

- Data access: `pd.read_csv` against `outputs/marts/*.csv`, `@st.cache_data`
  on every loader. No `duckdb.connect` anywhere in `app/`.
- Charting: Plotly `graph_objects` (not Express) for full control over the
  fixed palette, one axis per chart, recessive gridlines, `hovermode="x
  unified"`, legends only for ≥2 series, and a short "how to read" caption
  under every chart (per the dataviz skill's checklist). Every chart has an
  `st.expander` with its underlying data table.
- Palette fixed exactly as specified and matching `make_charts.py`: B2C
  `#2a78d6`, SMB `#eb6834`, Enterprise `#1baf7a`; scenario ramp bear
  `#86b6ef` / base `#2a78d6` / bull `#104281`; actuals ink `#0b0b0b`.
  MRR-bridge movement categories (new/expansion/contraction/churn) and risk
  tiers (High/Medium/Low) use a separate, consistent semantic palette not
  reused from the segment identity.

## Assumptions used (IDs)

Existing: M-01..M-15, D-05, D-06, D-07, D-16, D-17, D-18, D-19.

**New (starting at A-30 / D-25, per the plan's ID-allocation note):**

| ID | Topic | Decision |
|---|---|---|
| D-25 | Dashboard data source | The Streamlit app reads only `outputs/marts/*.csv`, never `db/platzi.duckdb` — chosen for Streamlit Community Cloud portability (no bundled binary DB, smaller repo diff, no read-lock contention). Every chart the brief asked for already had a mart export; no `app/export_data.py` was needed. |
| D-26 | "Main driver" per at-risk subscription | `mart_a1_06_may24_churn_risk.csv` stores one logit contribution per feature (`contrib_*`) but no single driver label. The app derives `main_driver` = the feature with the largest positive `contrib_*` value per row (row-wise `idxmax`), mapped to a plain-English label. This is a display-layer derivation, not a new SQL mart. |
| D-27 | Interactive scenario engine | The Scenarios tab's sliders reuse the official engine's pure functions (`simulate`, `add_rollups`, `default_params`, `compute_month_rates`) from `sql/python_models/scenarios.py` unmodified, fed by a `base` dict rebuilt from `mart_s_01_drivers.csv` + `fct_subscriptions.csv` instead of `calibrate(con, ...)`. This satisfies "no db write" and also "no db read" (stronger than required), at the cost of duplicating the ~15-line stock-snapshot query in pandas. Labeled "simplified" in the UI. |
| A-30 | Cohort heatmap segment fallback | `mart_a1_01_cohort_retention.csv` only splits cohorts into `B2C` / `B2B` / `Total` (not SMB/Enterprise separately — cohort retention was never computed at that granularity in WP20). When the sidebar filter is SMB or Enterprise, the heatmap shows the `B2B` cohort matrix with an on-screen note explaining why. |
| A-31 | Acquisition-funnel window | The funnel view aggregates `mart_a2_03_funnel_segment_monthly.csv` over the trailing 6 months (Nov-23..Apr-24), matching the T6M convention used everywhere else (WP21/WP22/WP31), rather than the full 16-month window. |

## Checks performed (reconciliations, row counts)

1. **`streamlit.testing.v1.AppTest` suite** (`app/test_app.py`), run via
   `.venv/Scripts/python.exe -m pytest app/test_app.py -v`:

   ```
   9 passed in 17.38s
   test_app_loads_without_exception PASSED
   test_headline_kpis_match_executive_summary_when_all_segments PASSED   (MRR $204,709; subs 1,941)
   test_segment_filter_options_run_without_exception PASSED              (All/B2C/SMB/Enterprise, no exceptions)
   test_segment_kpis_reconcile_to_mart_totals PASSED                     (MRR + subs match mart_mrr_bridge / mart_q3 exactly, per segment)
   test_retention_toggles_run_without_exception PASSED                   ($ toggle, T6M/T12M toggle)
   test_gm_basis_radio_runs_without_exception PASSED                     (T6M vs Apr-24 GM basis)
   test_scenario_sliders_run_without_exception PASSED                    (all 3 sliders, min/max)
   test_case_select_slider_runs_without_exception PASSED                 (low/base/high)
   test_churn_risk_download_button_present PASSED
   ```

2. **Headless server + health check**, as required:
   ```
   .venv/Scripts/streamlit.exe run app/streamlit_app.py --server.headless true --server.port 8599   (background)
   curl http://localhost:8599/_stcore/health  ->  ok      (checked at ~8s and again at ~16s)
   log shows no tracebacks; process then killed
   ```

3. Manual cross-check: churn-by-active-days-bucket recomputed in-app from
   `mart_a1_03_churn_indicators_base.csv` matches
   `mart_a1_04_churn_rate_by_bucket.csv` exactly when unfiltered (bucket
   0-5: n=612, churn=50.82% both sides; 6-10: n=1957, 16.45%; etc.).

4. `py_compile` clean; no lint run (not requested).

## Open issues / sensitivities

- The cohort heatmap cannot be split SMB vs. Enterprise (A-30) — would need a
  new WP20-layer mart (`mart_a1_01` recomputed with `segment` instead of
  `segment_group`) to fix; out of scope for WP33.
- The churn-by-engagement chart, GM% tile, and B2C expansion/contraction bars
  are flat/uniform across segments by construction of upstream decisions
  (D-07 GM allocation by MRR share; B2C fixed pricing means B2C
  expansion/contraction is always $0) — this is expected, not a bug, and is
  called out in the "how to read" captions.
- The interactive scenario sliders are a simplified reuse (D-27): they apply
  a single uniform churn multiplier / acquisition multiplier / save rate
  across all segments and plans, whereas the official engine's Bear/Bull
  cases apply segment-specific stresses (e.g., Bull only lifts SMB expansion
  and only reduces Enterprise contraction). This is intentional (three
  sliders, not twelve) and is disclosed in the UI caption.
- No `app/data/` or `app/export_data.py` was created — everything needed was
  already in `outputs/marts/`. If a future WP adds a chart needing a table
  not yet exported, that script should follow the pattern already documented
  in the WP33 brief (read `db/platzi.duckdb` with `read_only=True`, write to
  `app/data/`).
- `db/platzi.duckdb` (17 MB) is not needed by this app and should not be
  pushed to GitHub for the Streamlit Cloud deploy; only `outputs/marts/*.csv`
  and `app/` are required.
- Did not push to GitHub or deploy to Streamlit Community Cloud, per the
  work order ("Don't push or deploy anything yourself").

## Run / deploy instructions

See `app/README.md` for the full version. Summary:

```bash
export PYTHONIOENCODING=utf-8
.venv/Scripts/streamlit run app/streamlit_app.py       # local
```

Deploy: push the repo (including `outputs/marts/*.csv` and `app/`) to GitHub,
then on [share.streamlit.io](https://share.streamlit.io) → New app → main
file `app/streamlit_app.py`. Community Cloud will use `app/requirements.txt`.

## Files produced

- `app/streamlit_app.py`
- `app/requirements.txt`
- `app/README.md`
- `app/test_app.py`
- `work/WP33_dashboard/results.md` (this file)

No files were modified in `sql/**`, `Docs/**`, `outputs/*.html|pdf|xlsx`,
`work/WP40_model/**`, or `db/platzi.duckdb` (all read-only for this WP).

## Multi-select filter (2026-09-27)

The sidebar's single-choice segment radio (All / B2C / SMB / Enterprise) was
replaced with `st.sidebar.multiselect("Segments", ["B2C","SMB","Enterprise"],
default=all three)`, so the dashboard can show any one or more segments at
once (7 non-empty combinations). Clearing the widget entirely falls back to
all three segments, with a `st.sidebar.caption` explaining that.

**Resolution helper.** `resolve_group(selected)` maps the selection to
`(precomputed_group_label, display_label)`: all three → `("Total", "All
segments")`; `{SMB, Enterprise}` → `("B2B", "B2B")`; a single segment →
`(segment, segment)`; any other combination (only `{B2C, SMB}` and `{B2C,
Enterprise}` are possible with 3 base segments) → `(None, "B2C + SMB")`-style
label, signalling to callers that there is no rollup row and they must
aggregate from the base B2C/SMB/Enterprise rows.

**Per-mart handling** (a family of `..._scoped()` helpers built on top of
`resolve_group`, one per mart shape):

- **Aggregated when there's no rollup row** (sum additive $ / count columns,
  recompute ratios from summed numerators/denominators, never averaged):
  `bridge_scoped` (MRR bridge: sums opening/new/expansion/contraction/
  churn/closing MRR + active_customers, used for the Overview KPI tile, the
  MRR-bridge chart, and the Scenarios actuals line), `subs_scoped` (active
  subs; falls through to a sum even when `resolve_group` returns `"B2B"`
  because `mart_q3_active_subs_apr24` has no B2B row), `retention_scoped`
  (logo/$ retention = Σn_renewed/Σn_ended, Σ$num/Σ$den),
  `ndr_scoped`/`ndr_t6m_scoped` (NDR = Σend_mrr/Σstart_mrr; GRR =
  Σ(start-contraction-churn)/Σstart), `gm_scoped` (GM% = Σgross_profit/Σrevenue
  — additive because COGS is allocated by MRR share, D-07), `waterfall_scoped`
  (sums each waterfall step's $ amount across segments — verified additive:
  B2C+SMB+Enterprise reproduces the Total row and SMB+Enterprise reproduces
  the B2B row to floating-point precision), `proj_scoped` (projection-monthly
  $ / count flow columns, all additive), `scenario_summary_scoped` (MRR/subs
  summed; forward NDR/GRR recomputed as Σ(rate × mrr_apr24_actual) /
  Σmrr_apr24_actual, since `mrr_apr24_actual` is each segment's NDR
  denominator — verified this reconstruction reproduces the mart's own
  precomputed B2B and Total rows to 1e-10), and `panel_scoped` (the
  interactive-scenario engine's output panel — every column is an additive
  flow, so this mirrors what `scn.add_rollups()` already does for its own
  B2B/Total rows).
- **Per-segment rows, never blended, when the mart's numbers are ratios**
  (LTV:CAC, CAC, payback, GM basis sensitivities): `ue_view` (Unit economics
  tab's LTV:CAC chart and CAC/payback table) and `sens_scoped` (Sensitivity
  table) show one row/bar per selected segment for any combination without a
  precomputed rollup (sensitivity does have a `Total` row, used when all three
  are selected; there's no B2B row for either mart, so `{SMB, Enterprise}`
  also renders as two rows there). `strategy_impact_scoped` follows the same
  rule: MRR deltas are additive but %/pp deltas are not, so a custom
  combination shows one row per selected segment plus a caption explaining
  why, while the 5 precomputed combinations (Total/B2B/single) use the
  mart's own row directly. The funnel and the LTV:CAC/tier-summary bar charts
  already draw one mark per segment by construction, so they needed no
  aggregation logic at all — just iterate over the selected segments instead
  of a hardcoded list.
- **Fallback to the closest valid group, with a caption** where the mart
  simply has no finer breakdown: `cohort_group_for()` maps the selection to
  Total/B2C/B2B (the only granularity `mart_a1_01_cohort_retention` has,
  A-30) — exact for {all three}, {B2C}, {SMB, Enterprise}; falls back to B2B
  for a lone SMB or Enterprise (existing A-30 behavior, now flagged
  explicitly as non-exact); falls back to Total for the two custom
  B2C-containing combinations, with an `st.info` explaining the fallback.
- **Plain `segment.isin(selected)` filter, no rollup logic needed**: marts
  that only ever had base B2C/SMB/Enterprise rows to begin with —
  `mart_a1_03_churn_indicators_base` (churn-by-engagement chart),
  `mart_a1_06_may24_churn_risk` (tier summary, at-risk table, CSV download —
  filename now a `seg_slug()` like `b2c_smb.csv`), and
  `mart_a2_03_funnel_segment_monthly` (funnel).

**Colors follow the segment, not position**: every chart still keys off the
fixed `SEG_COLOR` dict (B2C `#2a78d6`, SMB `#eb6834`, Enterprise `#1baf7a`),
looked up by segment name in every loop (`for seg in selected_segments: ...
marker_color=SEG_COLOR[seg]`), so removing/adding a segment from the
selection never reassigns another segment's color. The BASE_LAYOUT
right-hand legend from the prior iteration was left untouched.

### Verification

Rewrote `app/test_app.py` around `AppTest`:

- `test_segment_combinations_run_without_exception_on_every_tab` drives all 7
  non-empty combinations of {B2C, SMB, Enterprise} plus the empty selection
  through every toggle (cohort $/logo, NDR T6M/T12M), the GM-basis radio, the
  case select-slider (low/base/high), and all 3 scenario sliders (at min and
  max) — asserting `at.exception` is empty at every step.
- `test_empty_selection_falls_back_to_all_with_caption` checks the sidebar
  caption text and that KPIs match the all-three-segments case.
- `test_segment_kpis_match_expected_values` checks MRR/subs for 4 required
  combinations: all three → $204,709.09 / 1,941; {SMB, Enterprise} →
  $140,344.09 / 405; {B2C, SMB} → $118,234.37 / 1,839; {B2C} → $64,365.00 /
  1,536 — the two-segment cases exercise the `bridge_scoped`/`subs_scoped`
  summation path (SMB+Enterprise is exact-match/precomputed lookup; B2C+SMB
  has no rollup row and is genuinely summed).
- `test_custom_combo_retention_matches_precomputed_rollup` reads
  `mart_q2_retention_q1_24.csv` directly, confirms the B2B row's logo_rate is
  0.9377 and the Total row's is 0.9009, then checks the app's Q1-24 retention
  KPI tile matches each to one decimal place for `{SMB, Enterprise}` and for
  the default all-three selection.

Result: `.venv/Scripts/python.exe -m pytest app/test_app.py -q` → **7 passed
in ~72s** (a transient run once took 11+ minutes with one flaky failure in
the combinations test under heavy concurrent background load on the
machine — rerun in isolation twice more, and the full suite once more,
all green in 50-75s each; no logic issue reproduced).

**Headless server check** (port 8599, not 8501): `streamlit run
app/streamlit_app.py --server.headless true --server.port 8599`, `curl
http://localhost:8599/_stcore/health` → `ok` at ~2s and again at ~10s, log
free of tracebacks, process killed by PID afterward. Port 8501 (the user's
running app) was left untouched throughout.

Only `app/streamlit_app.py`, `app/test_app.py`, and this section of
`results.md` were changed for this pass.
