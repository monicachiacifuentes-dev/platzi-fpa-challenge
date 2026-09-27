# sql/ — dbt-style DuckDB pipeline (WP01 + WP30)

## How to run

```bash
export PYTHONIOENCODING=utf-8
./.venv/Scripts/python.exe sql/run_pipeline.py
```

This is idempotent: it deletes `db/platzi.duckdb` if present and rebuilds it
from scratch every run, in one command. It prints PASS/FAIL for every file in
`sql/tests/`, and exports every `fct_*` / `mart_*` table to
`outputs/marts/<name>.csv`.

To explore the warehouse interactively:

```bash
./.venv/Scripts/python.exe -c "import duckdb; con = duckdb.connect('db/platzi.duckdb'); print(con.sql('SELECT * FROM mart_q1_mrr_apr24'))"
```

## Layers (dbt convention)

```
raw_*            <- read_csv_auto() straight off Docs/Originals/*.csv (7 tables)
  |
  v
staging/stg_*    <- 1:1 with raw tables. Casts types (DATE, DOUBLE, INTEGER),
  |                 trims strings, lower-cases emails, derives
  |                 users.customer_type ('B2C' vs 'B2B' = SMB+Enterprise),
  |                 and turns marketing_spend.month / support_costs.month
  |                 ("YYYY-MM" strings) into DATE (first of month).
  v
intermediate/
  int_month_spine            <- 16 month-end/month-start rows, 2023-01-31..2024-04-30
  int_subscription_periods   <- one row per subscription, joined to stg_users (segment,
                                 customer_type) and stg_engagement, with window
                                 functions for period_number, prev_mrr, next_mrr,
                                 mrr_delta, renewal_change, tenure_months, period_days
  v
marts/
  fct_subscriptions          <- int_subscription_periods + payment rollups
                                 (n_payments, amount_paid, main_gateway) per subscription
  fct_customer_mrr_monthly   <- user x month-end grid (from signup month to 2024-04-30)
                                 with mrr (M-02), prev_mrr, movement
  mart_mrr_bridge            <- fct_customer_mrr_monthly aggregated to month x segment
                                 (+ B2B, + Total): opening/new/expansion/contraction/
                                 churn/closing MRR, active customers
  mart_q1_mrr_apr24          <- Q1: MRR at 2024-04-30 by segment (+B2B, +Total), % mix
  mart_q2_retention_q1_24    <- Q2: M-06 primary (renewal-event, logo & $) +
                                 M-07 cross-check (customer snapshot), incl. monthly/annual split
  mart_q3_active_subs_apr24  <- Q3: active subs at 2024-04-30 by segment x plan_type + totals
  mart_q4_ndr_t12m           <- Q4: M-08 NDR, M-09 GRR, M-10 bridge, + renewal-event cross-check
  v
tests/           <- sql/tests/*.sql, each must return 0 rows to PASS (row counts,
                     unique keys, referential integrity, bridge identity, Q1=fct
                     cross-check, Q3 sums to 1,941, NDR identity / GRR<=1 / NDR>=GRR)
  |
  v
python_models/   <- sql/python_models/*.py (WP31 bonus). run_pipeline.py imports
                     every file here that exposes build(con), sorted by filename,
                     AFTER the SQL marts above and BEFORE sql/tests/ runs. Needed
                     because the scenario engine is an iterative monthly
                     simulation (12 compartments x 12 months x 3 scenarios x 3
                     strategies x 3 cases), which isn't expressible as a single
                     SELECT. Currently one file: scenarios.py, writing
                     mart_s_01_drivers .. mart_s_06_backtest_summary (WP31
                     scenario model + WP23 strategy sizing) -- see
                     work/WP31_scenarios/results.md and
                     work/WP23_strategies/results.md.
```

Mermaid lineage diagram:

```mermaid
flowchart LR
    subgraph raw
        ru[raw_users] --- rs[raw_subscriptions] --- rp[raw_payments]
        rpg[raw_payment_gateways] --- re[raw_engagement]
        rm[raw_marketing_spend] --- rc[raw_support_costs]
    end
    ru --> su[stg_users]
    rs --> ss[stg_subscriptions]
    rp --> sp[stg_payments]
    rpg --> spg[stg_payment_gateways]
    re --> se[stg_engagement]
    rm --> sm[stg_marketing_spend]
    rc --> sc[stg_support_costs]

    su --> isp[int_subscription_periods]
    ss --> isp
    se --> isp

    isp --> fs[fct_subscriptions]
    sp --> fs
    spg --> fs

    su --> fmm[fct_customer_mrr_monthly]
    ss --> fmm
    ims[int_month_spine] --> fmm

    fmm --> bridge[mart_mrr_bridge]
    fmm --> q1[mart_q1_mrr_apr24]
    fs --> q2[mart_q2_retention_q1_24]
    ss --> q2
    su --> q2
    ss --> q3[mart_q3_active_subs_apr24]
    su --> q3
    fmm --> q4[mart_q4_ndr_t12m]
    fs --> q4
```

## Design notes / implementation decisions (not M-xx metrics, documented here)

- **`next_status`** in `int_subscription_periods` / `fct_subscriptions` is a
  pass-through of `subscriptions.status`: the status field already encodes what
  happens at `end_date` (renewed = a next period exists, active = still open at
  the data snapshot, churned = chain ends). It is aliased/duplicated as
  `next_status` for self-documentation in downstream marts.
- **`main_gateway`** (in `fct_subscriptions`) = the payment gateway used on the
  largest number of payments for that subscription_id; ties broken by the
  lowest `payment_gateway_id`.
- **`movement`** categories in `fct_customer_mrr_monthly` (`new`, `expansion`,
  `contraction`, `churn`, `retained_flat`, `inactive`) extend the M-10
  vocabulary to a full monthly grid (M-10 itself only defines expansion /
  contraction / churn for a fixed start/end pair). `retained_flat` = no MRR
  change while active; `inactive` = no coverage before signup / after churn.
- Q1/Q2/Q3/Q4 marts add `B2B` (= SMB + Enterprise) and `Total` roll-up rows
  alongside the native `segment` values, using `UNION ALL` expansions — this
  keeps one flat table per question instead of several near-duplicate tables.

## DuckDB-specific functions (isolate before a BigQuery port, WP34)

| Used here | DuckDB | BigQuery equivalent |
|---|---|---|
| `int_month_spine.sql` | `generate_series(DATE, DATE, INTERVAL 1 MONTH)` | `GENERATE_DATE_ARRAY(start, end, INTERVAL 1 MONTH)` (returns an ARRAY; needs `UNNEST`) |
| `int_month_spine.sql` | `date_trunc('month', d)` | `DATE_TRUNC(d, MONTH)` (args reversed) |
| `int_subscription_periods.sql` | `DATE_DIFF('day', start_date, end_date)` | `DATE_DIFF(end_date, start_date, DAY)` (dates first, unit last — reversed argument order and no bare `date - date` subtraction) |
| `run_pipeline.py` (loader) | `read_csv_auto('...')` | `bq load` / `LOAD DATA` from GCS, or an external table |
| everywhere | `CREATE OR REPLACE TABLE x AS <select>` | same syntax works in BigQuery; only the two functions above need editing |

Everything else (window functions `ROW_NUMBER`/`LAG`/`LEAD`, `CASE`, standard
joins, `CAST`, string `TRIM`/`LOWER`/`||`) is ANSI-portable and should run
unmodified in BigQuery Standard SQL.

## Row counts (post-staging, verified by `test_row_counts.sql`)

users 2,695 · subscriptions 9,683 · payments 17,209 · engagement 9,683 ·
marketing_spend 144 · support_costs 64.
