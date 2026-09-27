# WP11 — Q2: Q1 2024 retention, B2C vs B2B

## Answer (numbers first)

**M-06 primary (renewal-event basis, subscriptions with `end_date` in 2024-01-01…2024-03-31)**

| Segment | Renewed | Churned | Ended | Logo retention | $ retention |
|---|---:|---:|---:|---:|---:|
| B2C | 1,936 | 226 | 2,162 | 89.55% | 89.46% |
| SMB | 270 | 18 | 288 | 93.75% | 95.56% |
| Enterprise | 31 | 2 | 33 | 93.94% | 94.58% |
| **B2B (SMB+Ent)** | **301** | **20** | **321** | **93.77%** | **95.23%** |
| **Total** | **2,237** | **246** | **2,483** | **90.09%** | **92.19%** |

**M-06 split by plan type**

| Segment | Plan | Logo retention | $ retention |
|---|---|---:|---:|
| B2C | monthly | 89.28% | 89.28% |
| B2C | annual | 96.30% | 96.30% |
| SMB | monthly | 93.58% | 95.40% |
| SMB | annual | 95.65% | 98.36% |
| Enterprise | monthly | 96.15% | 96.84% |
| Enterprise | annual | 85.71% | 84.24% |
| B2B | monthly | 93.81% | 95.85% |
| B2B | annual | 93.33% | 89.52% |
| Total | monthly | 89.84% | 92.27% |
| Total | annual | 95.50% | 91.05% |

**M-07 cross-check (customers active 2023-12-31, still active 2024-03-31)**

| Segment | Base (active 2023-12-31) | Logo retention |
|---|---:|---:|
| B2C | 1,104 | 82.61% |
| SMB | 195 | 92.31% |
| Enterprise | 66 | 96.97% |
| **B2B** | **261** | **93.49%** |
| **Total** | **1,365** | **84.69%** |

## Method

- `sql/marts/mart_q2_retention_q1_24.sql`, built on `fct_subscriptions`
  (= `int_subscription_periods` + payment rollups) and on `stg_subscriptions`/`stg_users` directly for M-07.
- **M-06**: filtered subscriptions to `end_date BETWEEN 2024-01-01 AND 2024-03-31` and
  `status IN ('renewed','churned')` (a row with `status='active'` cannot have ended in the
  window). Logo rate = `renewed / (renewed + churned)`. $ rate = `Σ next_mrr` of renewed rows
  (the MRR of the subscription each renewal continues into) ÷ `Σ mrr` of all ended rows
  (the MRR of the ending period, for both renewed and churned). Segmented by `users.segment`,
  plus a `B2B` roll-up (SMB+Enterprise) and `Total`; also split by `plan_type`.
- **M-07**: customers active on 2023-12-31 (M-02: `start_date ≤ 2023-12-31 < end_date`) vs.
  still active on 2024-03-31 (same test). Logo rate only (M-07 is a customer-snapshot method,
  no dollar version defined).

## Assumptions used (IDs)

- M-06 (primary retention definition), M-07 (cross-check definition), M-04 (segment, B2B roll-up).

## Checks performed (reconciliations, row counts)

- Row counts of `stg_subscriptions`/`fct_subscriptions` verified against `Docs/Datasets.md`
  (9,683 rows) via `sql/tests/test_row_counts.sql` and `test_unique_keys.sql`. **PASS**.
- Segment sub-totals reconcile: B2B row = SMB + Enterprise for both `n_renewed`/`n_churned`/`n_ended`
  (301 = 270+31; 20 = 18+2), and Total = B2C + B2B (2,483 = 2,162+321).
- Directional cross-check between M-06 and M-07 (see below).

## Open issues / sensitivities

- **M-06 (90.09% total logo) is noticeably higher than M-07 (84.69% total logo).** This is
  expected, not a bug: M-06 measures the success rate of individual renewal *events* ending
  in the quarter (mostly ~30-day monthly periods, so a given customer may have 1–3 such events
  in the window, each with its own success/failure draw), while M-07 measures whether a
  customer *survives the entire 3-month window* (compounding several renewal opportunities
  into one pass/fail outcome). A rough compounding check (0.90 event-success-rate^~1.2 events
  per customer in-window ≈ 0.85–0.88) is directionally consistent with the 84.69% observed.
  Report both; do not average them.
- B2C's lower retention (89.6% logo / 82.6% M-07) vs. B2B's (~93–94% logo / ~93% M-07) is the
  most actionable single number in this WP — B2C is the highest-churn, highest-volume segment.
- Enterprise's annual-plan retention (85.71% logo, only 7 events) is the smallest sample in
  this table; treat with caution (small-n).
- Sensitivity not applied here (out of scope per the definitions), but a $-weighted view that
  also captures contraction-not-just-full-churn is covered separately in WP13/NDR (M-08..M-10).

## Files produced

- `sql/marts/mart_q2_retention_q1_24.sql`
- `outputs/marts/mart_q2_retention_q1_24.csv`
