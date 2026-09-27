# Datasets — Data Dictionary & Profile

> Source: `Docs/Originals/*.csv`. Small tables are copied in full below. The three large tables (users, subscriptions, payments — ~1.4 MB / ~29k rows) are summarized as a profile instead of copied, because a Markdown copy would cost *more* tokens than the CSV. **For any calculation, read the original CSVs.**
> Profiled on 2026-09-26.

## Files
All 7 datasets are now in `Docs/Originals/` (engagement.csv and marketing_spend.csv were added later). All cross-checks below were verified.

## ⚠️ Key data issues (state as assumptions)
1. **Scale mismatch (marketing vs. users):** marketing_spend reports 21,573 new B2C / 695 SMB / 82 Enterprise users acquired over 16 months, but users.csv has 2,225 B2C / 361 SMB / 109 Enterprise. B2C is ~10× → users.csv looks like a **sample** of B2C, while Enterprise has *more* users than marketing claims. The CAC denominator must be an explicit assumption (see `Docs/Plan_and_Index.md` → D-06).
2. **Scale is consistent for costs vs. revenue:** MRR at 2024-04-30 ≈ $204.7k, support costs Apr-24 ≈ $153.7k → costs and the subscription data are on the same scale.
3. Payment amounts = list prices (they don't reflect B2B MRR changes); ~2 payments per subscription period.
4. 3 duplicate emails in users.csv (payments join by email).

---

## users.csv — 2,695 rows
`user_id, first_name, email, age, segment, signup_date`

| Field | Profile |
|---|---|
| user_id | U01000 … (unique, 2,695) |
| segment | B2C 2,225 · SMB 361 · Enterprise 109 |
| age | 18–54, mean 36.7 |
| signup_date | 2023-01-01 → 2024-04-30 |
| email | 2,692 unique — **3 duplicated emails** (dakota764@gmail.com, liam970@outlook.com, peyton52@live.com) → risk when joining payments by email |

Sample: `U01000,Ingrid,ingrid291@hotmail.com,32,B2C,2023-01-05`

## subscriptions.csv — 9,683 rows
`subscription_id, user_id, plan_type, start_date, end_date, mrr, status`

One row per billing period; a renewal creates a new row. All 2,695 users have ≥1 subscription.

| Field | Profile |
|---|---|
| plan_type | monthly 8,556 · annual 1,127 |
| status | renewed 6,988 · active 1,941 · churned 754 |
| plan × status | monthly: renewed 6,839 / active 969 / churned 748 · annual: renewed 149 / active 972 / churned 6 |
| start_date | 2023-01-01 → 2024-04-30 |
| end_date | 2023-01-31 → 2025-04-30 (monthly ≈ +30 days, annual ≈ +365 days) |
| no blanks | ✔ |

**MRR by segment × plan (from join with users):**

| Segment | Plan | Rows | MRR range |
|---|---|---|---|
| B2C | monthly | 7,541 | 49 (fixed) |
| B2C | annual | 810 | 33.25 (fixed = 399/12) |
| SMB | monthly | 929 | 134.70 – 515.30 (base 199) |
| SMB | annual | 217 | 149.92 – 185.76 (base 149.92 = 1,799/12) |
| Enterprise | monthly | 86 | 795.26 – 1,293.77 (base 990) |
| Enterprise | annual | 100 | 697.36 – 867.63 (base 825 = 9,900/12) |

B2C MRR never changes → expansion/contraction lives only in B2B.

Subscriptions per user: 1:1,117 · 2:425 · 3:226 · 4:158 · 5:148 · 6:125 · 7:107 · 8:85 · 9:61 · 10:63 · 11:53 · 12:35 · 13:28 · 14:34 · 15:18 · 16:9 · 17:3

Sample (monthly chain then churn):
```
S05000,U01000,monthly,2023-01-05,2023-02-04,49,renewed
S05001,U01000,monthly,2023-02-04,2023-03-06,49,renewed
S05002,U01000,monthly,2023-03-06,2023-04-05,49,renewed
S05003,U01000,monthly,2023-04-05,2023-05-05,49,churned
S05040,U01004,annual,2023-01-14,2024-01-14,33.25,renewed
S05041,U01004,annual,2024-01-14,2025-01-13,33.25,active
```

## payments.csv — 17,209 rows
`email, subscription_id, amount, payment_date, payment_gateway_id`

| Field | Profile |
|---|---|
| payment_date | 2023-01-01 → 2024-04-30 |
| total amount | $2,885,718 |
| amount values | 49 (14,199) · 199 (1,737) · 399 (800) · 1,799 (216) · 990 (158) · 9,900 (99) — **list prices only** |
| gateway | 1 Stripe 6,286 · 2 PayPal 4,332 · 3 MercadoPago 4,986 · 4 Payoneer 1,510 · 5 Wire 95 |
| coverage | 9,643 unique subscription_ids (40 subs have no payment) · 2,679 unique emails |
| payments per sub | 1 payment: 2,077 subs · 2 payments: 7,566 subs |
| no blanks | ✔ |

Data quirks to state as assumptions:
- Payment `amount` = list price; does **not** reflect B2B MRR changes (e.g., SMB mrr 263.31 is still paid as 199) → use `subscriptions.mrr` for MRR/NDR, payments for cash/billings.
- Most monthly subscriptions show 2 payments (near start and near end of period) — possible double-count/overlap with the next period; check before using payments as revenue.
- Payments join to users by email (3 duplicate emails in users).

Sample: `ingrid291@hotmail.com,S05000,49,2023-01-07,1`

**Sanity check:** subscriptions covering 2024-04-30 (start ≤ date < end) = 1,941 rows, MRR $204,709.09. This matches `status = active` exactly (1,941 / $204,709.09).

Payments per month (volume growth): 2023-01:102 · 02:215 · 03:363 · 04:498 · 05:650 · 06:743 · 07:885 · 08:1,065 · 09:1,162 · 10:1,314 · 11:1,391 · 12:1,561 · 2024-01:1,671 · 02:1,690 · 03:1,911 · 04:1,988

## engagement.csv — 9,683 rows
`user_id, subscription_id, active_days, courses_seen, materials_seen, favorite_category`

One row per subscription period. It maps 1:1 to subscriptions.csv (0 missing, 0 user_id mismatches). No blanks.

| Field | Profile |
|---|---|
| active_days | 1–28, mean 14.0 |
| courses_seen | 0–18, mean 6.4 |
| materials_seen | 0–97, mean 29.6 |
| favorite_category | 12 values, ~770–860 each: Cloud Computing, Product Management, Leadership, Data Science, Marketing, AI & Machine Learning, Business, Startup, DevOps, Software Development, Design, English |

**Churn signal (strong):**

| Plan / status | n | avg active_days | avg courses_seen |
|---|---|---|---|
| monthly renewed | 6,839 | 14.8 | 7.1 |
| monthly churned | 748 | **6.5** | **1.5** |
| monthly active | 969 | 13.6 | 5.7 |
| annual renewed | 149 | 15.6 | 7.7 |
| annual churned | 6 | **5.8** | **1.3** |
| annual active | 972 | 14.2 | 6.0 |

Sample: `U01000,S05000,9,10,13,Software Development`

## marketing_spend.csv — 144 rows (full summary)
`month, channel, spend, new_users_acquired, segment`: 16 months × 9 segment-channel combos. Total spend **$1,524,838.93**.

| Segment | Channel | Spend (16 mo) | New users |
|---|---|---|---|
| B2C | Paid Search | 345,766.52 | 7,746 |
| B2C | Paid Social | 255,155.43 | 4,801 |
| B2C | Content | 116,712.76 | 4,039 |
| B2C | Organic | 72,159.60 | 4,987 |
| **B2C total** | | **789,794.31** | **21,573** |
| SMB | Paid Search | 124,953.22 | 325 |
| SMB | Paid Social | 77,601.45 | 181 |
| SMB | Content | 51,254.36 | 189 |
| **SMB total** | | **253,809.03** | **695** |
| Enterprise | Sales Team | 407,228.33 | 67 |
| Enterprise | Content | 74,007.26 | 15 |
| **Enterprise total** | | **481,235.59** | **82** |

Monthly B2C spend grows from ~$34.9k (Jan-23) to ~$66.2k (Apr-24); Enterprise Sales Team runs $17.5k–$32.2k/month. "Sales Team" appears only for Enterprise. Read the CSV for monthly detail (144 rows).

## payment_gateways.csv — 5 rows (full)

| payment_gateway_id | payment_gateway_name |
|---|---|
| 1 | Stripe |
| 2 | PayPal |
| 3 | MercadoPago |
| 4 | Payoneer |
| 5 | Wire Transfer |

## support_costs.csv — 64 rows (full)
16 months × 4 categories (CS Salaries, Infrastructure, Content Production, G&A). Amounts in USD.

| Month | CS Salaries | Infrastructure | Content Production | G&A | Total |
|---|---|---|---|---|---|
| 2023-01 | 30,417.51 | 19,317.85 | 23,288.62 | 22,014.85 | 95,038.83 |
| 2023-02 | 33,890.33 | 17,941.03 | 26,492.33 | 21,940.26 | 100,263.95 |
| 2023-03 | 34,952.80 | 20,105.10 | 28,516.62 | 24,450.65 | 108,025.17 |
| 2023-04 | 35,632.22 | 21,192.85 | 29,590.04 | 25,182.47 | 111,597.58 |
| 2023-05 | 36,921.85 | 22,739.58 | 28,251.22 | 24,074.78 | 111,987.43 |
| 2023-06 | 37,974.50 | 24,009.13 | 30,976.46 | 25,040.72 | 118,000.81 |
| 2023-07 | 37,494.55 | 24,486.54 | 33,426.70 | 25,289.26 | 120,697.05 |
| 2023-08 | 39,569.58 | 22,803.31 | 34,156.26 | 26,583.47 | 123,112.62 |
| 2023-09 | 42,424.68 | 26,101.89 | 32,939.87 | 27,512.52 | 128,978.96 |
| 2023-10 | 42,975.93 | 25,048.67 | 34,486.15 | 29,643.90 | 132,154.65 |
| 2023-11 | 45,673.15 | 24,504.86 | 36,269.25 | 30,254.05 | 136,701.31 |
| 2023-12 | 45,316.66 | 27,116.83 | 36,450.78 | 30,802.45 | 139,686.72 |
| 2024-01 | 44,168.09 | 25,386.41 | 36,211.43 | 30,840.31 | 136,606.24 |
| 2024-02 | 48,707.77 | 27,762.18 | 39,864.83 | 31,649.73 | 147,984.51 |
| 2024-03 | 47,666.62 | 29,706.84 | 39,445.36 | 30,766.60 | 147,585.42 |
| 2024-04 | 47,709.67 | 30,597.71 | 42,620.05 | 32,807.97 | 153,735.40 |
