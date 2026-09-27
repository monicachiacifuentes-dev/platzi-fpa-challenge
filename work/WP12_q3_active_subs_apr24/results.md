# WP12 — Q3: Active subscriptions at 2024-04-30 by segment × plan type

## Answer (numbers first)

| Segment | Monthly | Annual | Total |
|---|---:|---:|---:|
| B2C | 844 | 692 | 1,536 |
| SMB | 113 | 190 | 303 |
| Enterprise | 12 | 90 | 102 |
| **Total** | **969** | **972** | **1,941** |

Grand total = **1,941**, matching M-02's verified data fact (equals `status = 'active'` count exactly).

## Method

- `sql/marts/mart_q3_active_subs_apr24.sql`, on `stg_subscriptions` joined to `stg_users`.
- Active on 2024-04-30 per M-02: `start_date ≤ 2024-04-30 < end_date`.
- Grouped by `users.segment` × `subscriptions.plan_type`, with segment totals, plan totals,
  and a grand total row added via `UNION ALL`.

## Assumptions used (IDs)

- M-01 (as-of date), M-02 (active-on-date definition), M-04 (segment via `users.segment`).

## Checks performed (reconciliations, row counts)

- `sql/tests/test_q3_sum_1941.sql`: grand total = 1,941. **PASS**.
- Cross-checked against `Docs/Datasets.md`: "subscriptions covering 2024-04-30 ... = 1,941 rows.
  This matches status = active exactly (1,941)" and the plan × status profile (monthly active 969,
  annual active 972) — matches exactly.
- Segment totals (1,536 + 303 + 102 = 1,941) and plan totals (969 + 972 = 1,941) both tie to the
  grand total.

## Open issues / sensitivities

- None — this is a direct point-in-time count with no definitional ambiguity. Worth flagging
  as an observation (not an issue): Enterprise is almost entirely annual (90/102 = 88%), while
  B2C is roughly even (692/1,536 = 45% annual) and SMB skews annual too (190/303 = 63%) —
  annual-plan mix rises with segment size/contract value, as expected for a B2B motion.

## Files produced

- `sql/marts/mart_q3_active_subs_apr24.sql`
- `outputs/marts/mart_q3_active_subs_apr24.csv`
