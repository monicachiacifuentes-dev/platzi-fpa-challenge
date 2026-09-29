# WP34b — BigQuery port (raw-table SQL) + reconciliation

## Answer (numbers first)

**242 / 242 reconciliation rows PASS** (0 FAIL). Full row-level detail in
`outputs/bigquery_reconciliation.csv`. Headline figures, DuckDB vs. BigQuery
(computed independently in BigQuery from `raw_users` / `raw_subscriptions`
only):

| Question | Metric | DuckDB | BigQuery | abs diff | Tolerance | Status |
|---|---|---|---|---|---|---|
| Q1 | Total MRR Apr-24 | 204,709.09 | 204,709.09 | 0.00 | 0.01 | PASS |
| Q1 | B2C MRR | 64,365.00 | 64,365.00 | 0.00 | 0.01 | PASS |
| Q1 | SMB MRR | 53,869.37 | 53,869.37 | 0.00 | 0.01 | PASS |
| Q1 | Enterprise MRR | 86,474.72 | 86,474.72 | 0.00 | 0.01 | PASS |
| Q2 | Logo retention, Total, M06 all | 0.9009 | 0.9009 | 0.0000 | 0.0001 | PASS |
| Q2 | $ retention, Total, M06 all | 0.9219 | 0.9219 | 0.0000 | 0.0001 | PASS |
| Q3 | Active subs, grand total | 1,941 | 1,941 | 0 | exact | PASS |
| Q4 | NDR T12M, Total | 0.6370 | 0.6370 | 0.0000 | 0.0001 | PASS |
| Q4 | GRR T12M, Total | 0.5988 | 0.5988 | 0.0000 | 0.0001 | PASS |
| Q4 | Base customers, Total | 417 | 417 | 0 | exact | PASS |

All 242 rows across Q1 (10 rows: 5 segments × 2 metrics), Q2 (135 rows: 2
methods × segments × splits × up-to-7 metrics), Q3 (12 rows: segment×plan ×
1 metric), and Q4 (95 rows: 2 methods × segments × up-to-8 metrics) pass at
the tolerances specified in the task (money 0.01, rates 0.0001, counts
exact). No genuine definitional differences were found — every discrepancy
during development was a dialect bug (see Method), not a metric-definition
mismatch, so no sensitivity/alternative needed to be logged.

## Method

1. Inspected `raw_users` / `raw_subscriptions` schemas with `bq show
   --schema` — both `signup_date` and `start_date`/`end_date`/`mrr` were
   already autodetected as `DATE`/`FLOAT` by `bq load --autodetect`
   (`sql/bigquery/load_to_bigquery.ps1`, run previously for WP34), so no
   `SAFE.PARSE_DATE` from STRING was needed.
2. Ported the DuckDB logic for each of the 4 challenge marts
   (`sql/marts/mart_q1..q4_*.sql`) into one self-contained BigQuery file per
   question, each rebuilding the needed slice of `stg_users` /
   `stg_subscriptions` / `int_subscription_periods` /
   `fct_customer_mrr_monthly` as inline CTEs **from `raw_users` /
   `raw_subscriptions` only** — no `mart_*`/`fct_*` table is read by any of
   the four queries (verified by inspection: every `FROM`/`JOIN` in
   `sql/bigquery/q1..q4*.sql` targets a CTE or a `raw_*` table).
   - Q1/Q4 needed MRR at fixed snapshot dates only (2023-04-30, 2024-04-30),
     so the DuckDB `int_month_spine`/full monthly grid was replaced with a
     direct "active MRR as of D" computation per date — mathematically
     equivalent, and avoids the one truly non-portable DuckDB function
     (`generate_series` over dates).
   - Q2/Q4's renewal-based metrics needed `LAG`/`LEAD`/`ROW_NUMBER` window
     functions per user ordered by `start_date` — these are ANSI-portable
     and used unchanged.
   - `stg_payments`, `stg_payment_gateways`, `stg_engagement` were not ported
     because none of Q1–Q4's output columns depend on them.
3. Ran each file with `bq query --use_legacy_sql=false`, ending in `CREATE OR
   REPLACE TABLE platzi_fpa.bq_q1_mrr_apr24 AS ...` (and q2/q3/q4
   equivalents), so results persist as BigQuery tables.
4. Wrote `sql/bigquery/reconcile.py`: pulls each `bq_*` table via `bq query
   --format=csv` and the matching `outputs/marts/mart_q*.csv`, joins rows on
   the natural key columns (e.g. `segment`, or `method`+`segment`+`split`),
   diffs every numeric column at the tolerance appropriate to its kind (money
   0.01 / rate 0.0001 / count exact), prints a PASS/FAIL table, and writes
   `outputs/bigquery_reconciliation.csv`.
5. Wrote `sql/bigquery/run_bigquery.ps1` to run the 4 `.sql` files then
   `reconcile.py` in one command (same PATH trick as `load_to_bigquery.ps1`).
6. First run hit an encoding bug, not a logic bug (see Checks performed) —
   fixed in the runner script, not in the SQL.
7. Verified the four spot-checked headline numbers (Q1 total MRR, Q3 grand
   total, Q4 Total NDR/GRR/base, Q2 Total logo/$ rate) via direct `bq query`
   against `bq_q1..q4_*` before running the full reconciliation, then ran
   `reconcile.py` for the full 242-row comparison.

## Assumptions used (IDs)

- M-01..M-04 (Q1), M-02 (Q3), M-06/M-07 (Q2), M-08/M-09/M-10 (Q4) — same
  definitions as the DuckDB marts, no new assumptions introduced.
- No new A-xx assumption was needed: this WP is a dialect port of already-
  approved logic, not a new analytical decision.

## Checks performed (reconciliations, row counts)

- `bq show --schema` on `raw_users` and `raw_subscriptions` confirmed DATE/
  FLOAT autodetection (no STRING date parsing branch was needed, though the
  SQL still includes defensive `CAST(... AS DATE)` in case that ever
  changes).
- Full 242-row reconciliation via `sql/bigquery/reconcile.py`: 242 PASS, 0
  FAIL (`outputs/bigquery_reconciliation.csv`).
- Encoding gotcha found and fixed during testing: piping a `.sql` file's text
  directly into `bq.cmd` from PowerShell (`Get-Content -Raw | bq query`)
  fails with `Syntax error: Illegal input character "\357" at [1:1]` — `bq`'s
  parser treats a UTF-8 BOM on stdin as an illegal character rather than
  skipping it, and PowerShell's string-to-native-stdin pipe re-introduces a
  BOM even after stripping it from the in-memory string. Fixed in
  `run_bigquery.ps1` by writing the (BOM-stripped) query to a temp file with
  explicit BOM-less UTF-8 and redirecting `bq`'s stdin from that file via
  `cmd /c "... < file"` instead of piping. This is a Windows/PowerShell/bq-
  CLI encoding quirk, not a SQL dialect difference — documented here so it
  isn't re-debugged next time.
- Ran the full `run_bigquery.ps1` end to end after the fix: all 4 queries
  created their `bq_*` tables and the reconciliation printed 242/242 PASS.

## Open issues / sensitivities

- None. No genuine definitional difference between DuckDB and BigQuery was
  found; every number matches within tolerance (most match to the last
  floating-point digit, well inside the 0.01/0.0001 bands — the tiny
  residual differences visible in `outputs/bigquery_reconciliation.csv`,
  e.g. `8145.990000000002` vs `8145.990000000001`, are ordinary
  floating-point summation-order noise, far under tolerance).
- BigQuery Sandbox has a 60-day table expiry (per the environment brief) —
  the `bq_q1..q4_*` tables will need re-running past that window if anyone
  revisits this for screenshots.

## Files produced

- `sql/bigquery/q1_mrr_apr24.sql`, `q2_retention_q1_24.sql`,
  `q3_active_subs_apr24.sql`, `q4_ndr_t12m.sql`
- `sql/bigquery/reconcile.py`
- `sql/bigquery/run_bigquery.ps1`
- `sql/README.md` — new "BigQuery port (WP34b)" section
- `outputs/bigquery_reconciliation.csv`
- Mirrored to `Deliverables/05_SQL/bigquery/` (the 4 `.sql`, `reconcile.py`,
  `run_bigquery.ps1`)
- BigQuery tables (persisted, dataset `platzi_fpa`, project
  `project-b7f9b2e4-dcdc-4e36-b89`): `bq_q1_mrr_apr24`,
  `bq_q2_retention_q1_24`, `bq_q3_active_subs_apr24`, `bq_q4_ndr_t12m`
