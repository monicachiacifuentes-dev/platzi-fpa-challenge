# WP10 — Q1: MRR at 2024-04-30 by segment

## Answer (numbers first)

| Segment | MRR ($) | % of total |
|---|---:|---:|
| B2C | 64,365.00 | 31.44% |
| SMB | 53,869.37 | 26.32% |
| Enterprise | 86,474.72 | 42.24% |
| **B2B (SMB + Enterprise)** | **140,344.09** | **68.56%** |
| **Total** | **204,709.09** | **100.00%** |

Matches the expected total of ≈ $204,709.09 exactly (to the cent).

## Method

- Built `sql/marts/fct_customer_mrr_monthly.sql`: a user × month-end grid where MRR at a
  given month-end = `SUM(subscriptions.mrr)` for subscriptions with
  `start_date ≤ month_end < end_date` (M-02), 0 otherwise.
- Filtered to `month_end = 2024-04-30` and grouped by `users.segment` (M-04); added a
  `B2B` roll-up (SMB + Enterprise, per M-04) and a `Total` row.
- `%_of_total` = segment MRR ÷ Total MRR, rounded to 2 decimals.
- Materialized in `sql/marts/mart_q1_mrr_apr24.sql`.

## Assumptions used (IDs)

- M-01 (as-of date = 2024-04-30), M-02 (active-on-date definition), M-03 (MRR = `subscriptions.mrr`,
  annual plans already monthly-normalized), M-04 (segment via `users.segment`; B2B = SMB + Enterprise).

## Checks performed (reconciliations, row counts)

- `sql/tests/test_q1_matches_fct.sql`: Total MRR in `mart_q1_mrr_apr24` equals
  `SUM(mrr)` from `fct_customer_mrr_monthly` at `month_end = 2024-04-30` (diff ≤ 0.01). **PASS**.
- Cross-checked against `Docs/Datasets.md`'s independent sanity check: "subscriptions
  covering 2024-04-30 = 1,941 rows, MRR $204,709.09" — matches exactly.
- `sql/tests/test_row_counts.sql` and `test_referential_integrity.sql` on the underlying
  staging tables: **PASS** (see `sql/README.md` / pipeline run log).

## Open issues / sensitivities

- None. This is a direct, unambiguous read of `subscriptions.mrr` for active subscriptions;
  no assumption choices affect this number (unlike Q2/Q4, which have primary vs.
  cross-check definitions).

## Files produced

- `sql/marts/fct_customer_mrr_monthly.sql`, `sql/marts/mart_q1_mrr_apr24.sql`
- `outputs/marts/mart_q1_mrr_apr24.csv`, `outputs/marts/fct_customer_mrr_monthly.csv`
