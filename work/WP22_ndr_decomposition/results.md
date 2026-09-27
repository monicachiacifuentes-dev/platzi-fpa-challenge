# WP22 — Analysis 3: NDR Decomposition

## Answer (numbers first)

### 1. T12M decomposition (base: 417 customers active 2023-04-30, evaluated 2024-04-30)

| Segment | Base cust. | Start MRR | − Churn | − Contraction | + Expansion | = End MRR | NDR | GRR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B2C | 353 | 15,470.00 | 8,806.00 (56.9%) | 0.00 | 0.00 | 6,664.00 | **43.08%** | **43.08%** |
| SMB | 52 | 9,071.54 | 2,171.57 (23.9%) | 40.78 (0.4%) | 1,286.80 (14.2%) | 8,145.99 | **89.80%** | **75.61%** |
| Enterprise | 12 | 10,230.00 | 2,805.00 (27.4%) | 127.64 (1.2%) | 42.63 (0.4%) | 7,339.99 | **71.75%** | **71.33%** |
| **B2B** | **64** | **19,301.54** | **4,976.57 (25.8%)** | **168.42 (0.9%)** | **1,329.43 (6.9%)** | **15,485.98** | **80.23%** | **73.34%** |
| **Total** | **417** | **34,771.54** | **13,782.57 (39.6%)** | **168.42 (0.5%)** | **1,329.43 (3.8%)** | **22,149.98** | **63.70%** | **59.88%** |

Customer counts behind the $ (per segment: expansion / contraction / churn / flat customers): B2C 0/0/181/172 · SMB 18/1/11/22 · Enterprise 1/1/3/7 · B2B 19/2/14/29 · Total 19/2/195/201.
Identical to `mart_q4_ndr_t12m` (WP13) on every column — see Checks.
Waterfall-ready long format: `mart_a3_02_t12m_waterfall_long` (segment, step, step_order, amount).

### 2a. T6M decomposition (base: customers active 2023-10-31, evaluated 2024-04-30 — robustness, ~2.7× the T12M base)

| Segment | Base cust. | Start MRR | − Churn | − Contraction | + Expansion | = End MRR | NDR | GRR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B2C | 917 | 39,373.25 | 13,706.00 (34.8%) | 0.00 | 0.00 | 25,667.25 | **65.19%** | **65.19%** |
| SMB | 159 | 27,999.63 | 4,617.39 (16.5%) | 108.20 (0.4%) | 1,482.85 (5.3%) | 24,756.89 | **88.42%** | **83.12%** |
| Enterprise | 48 | 40,840.42 | 2,946.39 (7.2%) | 275.34 (0.7%) | 285.82 (0.7%) | 37,904.51 | **92.81%** | **92.11%** |
| **B2B** | **207** | **68,840.05** | **7,563.78 (11.0%)** | **383.54 (0.6%)** | **1,768.67 (2.6%)** | **62,661.40** | **91.02%** | **88.46%** |
| **Total** | **1,124** | **108,213.30** | **21,269.78 (19.7%)** | **383.54 (0.4%)** | **1,768.67 (1.6%)** | **88,328.65** | **81.62%** | **79.99%** |

T6M NDR/GRR is materially higher than T12M for every segment — half the exposure window and a much larger, later-signed-up (more mature product/onboarding) base. Waterfall long format: `mart_a3_04_t6m_waterfall_long`.

### 2b. Monthly-compounded T12M vs. snapshot T12M (May-23 → Apr-24, 12 monthly transitions)

| Segment | NDR compounded (monthly) | NDR snapshot (T12M) | Diff | GRR compounded | GRR snapshot | Diff |
|---|---:|---:|---:|---:|---:|---:|
| B2C | 40.62% | 43.08% | −2.5pp | 40.62% | 43.08% | −2.5pp |
| SMB | 73.81% | 89.80% | **−16.0pp** | 63.42% | 75.61% | −12.2pp |
| Enterprise | 83.04% | 71.75% | **+11.3pp** | 81.04% | 71.33% | +9.7pp |
| B2B | 79.45% | 80.23% | −0.8pp | 73.59% | 73.34% | +0.3pp |
| Total | 62.44% | 63.70% | −1.3pp | 59.43% | 59.88% | −0.5pp |

Company-level (Total, B2B) the two methods agree within ~1pp — a strong robustness check. SMB and Enterprise diverge by 10–16pp in opposite directions: with only 52/12 customers in the fixed T12M cohort, one or two logos swing the snapshot NDR by several points (SMB's cohort happened to land a large expansion; Enterprise's cohort happened to hit its worst churn month later in the window). The monthly-compounded figure uses a much larger, rolling base each month (up to 368 B2B / 1,788 total customers by Apr-24) and is the more statistically stable estimate of "steady-state" NDR for the smaller segments; the snapshot remains the metric that matches M-08's definition exactly. **Recorded as Proposed D-15** (see Assumptions).
Full monthly series: `mart_a3_05_monthly_ndr_series` (75 rows: 5 segment groups × 15 months, Feb-23..Apr-24). Company-wide (Total) monthly NDR stays in a 91.8%–97.7% range every month. B2B's monthly NDR is more volatile early on (from a base of just 11 customers in Feb-23, swinging as low as 92.1% in Apr-23) and settles into a steadier ~98–99% band once the B2B base scales past ~200 customers (Nov-23 onward).

### 3. Renewal-event view (6,635 renewals, start_date 2023-05-01..2024-04-30 — ties exactly to WP13's cross-check population)

By segment (all renewals, not just the 417/64-customer snapshot cohort):

| Segment | Renewal events | Expansion events | Expansion $ | Contraction events | Contraction $ |
|---|---:|---:|---:|---:|---:|
| B2C | 5,803 | 0 | 0.00 | 0 | 0.00 |
| SMB | 757 | 129 | 3,916.71 | 26 | 793.52 |
| Enterprise | 75 | 8 | 956.19 | 3 | 470.08 |

Where contraction concentrates (of B2B renewal events, `mart_a3_07_renewal_segmentation`):
- **By MRR tier / plan:** 100% of SMB's 26 contraction events sit in the 100–300 MRR tier (SMB's base monthly tier, $199 list); 100% of Enterprise's 3 contraction events sit in the 600–1,000 tier (base monthly $990 / annual $825 level) — contraction is a "starter/base-plan" phenomenon in both segments, not a high-tier one.
- **By tenure:** SMB contraction is heaviest at the **5th–8th renewal** (12 events, $334.03 = 42% of SMB's $793.52 total; contraction rate 5.2% of renewals in that bucket vs. 2.4–3.2% elsewhere) — a mid-life "renewal fatigue" window roughly 6–8 months to a year+ in. Enterprise contraction is heaviest at the **2nd renewal** (2 of 3 events, $322.38 = 69% of Enterprise's $470.08 total; 8.3% contraction rate at renewal #2 vs. 0% from renewal #5 onward) — an early "is this delivering value" moment right after onboarding.
- **% change distribution** (`mart_a3_08_renewal_pctchange_bins`): SMB non-flat renewals skew positive — 101 events at +5–20%, 28 at ≥+20%, vs. 26 in the −5% to −20% band (none below −20%). Enterprise: 6 events at +5–20%, 2 at ≥+20%, vs. 3 in the −5%/−20% band. No renewal in either segment lost more than ~20% of its MRR at a single renewal — contraction is a moderate downgrade, not a mass cancellation-adjacent event.
- **Engagement of the ended period** (`mart_a3_09_renewal_engagement`): active_days/courses_seen of the period that ended do **not** meaningfully differ between expansion, contraction and flat renewals (SMB: 16.2 / 16.7 / 16.5 active days; Enterprise: 18.3 / 22.0 / 20.5, n=8/3/64 — Enterprise contraction customers were *more* engaged, but n=3). This is the opposite of the strong churn signal in `Docs/Datasets.md` (churned periods average 6.5 days vs. 14.8 for renewed) — **expansion/contraction at renewal looks driven by account/commercial factors (seat count, negotiated price changes) rather than product engagement**, unlike churn itself.

### 4. Which segment drives the most expansion revenue? Where is contraction concentrated?

**SMB drives the most expansion revenue, in both absolute $ and as a share of its own MRR.** Across all renewal events in the T12M window, SMB generated **$3,916.71** of expansion vs. Enterprise's **$956.19** (SMB is 4.1× Enterprise's $ expansion, and 16× more expansion events: 129 vs. 8). As a % of each segment's own MRR at 2024-04-30 (SMB $53,869.37; Enterprise $86,474.72), SMB's renewal-window expansion is **7.27%** of its current MRR vs. Enterprise's **1.11%** — SMB expands ~6.5× faster relative to its own size. B2C contributes zero expansion by construction (fixed pricing, M-verified data fact).

**Contraction is small everywhere (never the dominant flow) but concentrates differently by segment.** In $ terms SMB contraction ($793.52) is larger than Enterprise's ($470.08), but as a % of segment MRR Enterprise's is smaller still (0.54% vs. SMB's 1.47%). Structurally: SMB contraction concentrates in **base-tier accounts (100–300 MRR) at mid-tenure (5th–8th renewal)** — a slow bleed of established, low-tier accounts, roughly 5× smaller in $ than SMB's own expansion in the same window ($793.52 vs. $3,916.71). Enterprise contraction concentrates in **base-tier accounts (600–1,000 MRR) at the 2nd renewal** — an early-life risk, but Enterprise's expansion still exceeds its contraction 2:1 ($956.19 vs. $470.08). **In neither B2B segment does contraction come close to offsetting expansion; churn (logo loss), not contraction, is what drives NDR below 100% in every segment** (churn is 24–56% of start MRR vs. contraction's 0.4–1.2%).

## Method

- Built entirely in an isolated dev DB (`work/WP22_ndr_decomposition/dev.duckdb`, a copy of `db/platzi.duckdb`); `db/platzi.duckdb` was never opened for writing.
- **T12M/T6M decomposition** (`mart_a3_01_t12m_decomposition`, `mart_a3_03_t6m_decomposition`): same M-08/M-09/M-10 snapshot method as `mart_q4_ndr_t12m` (WP13) — base = customers with `mrr > 0` in `fct_customer_mrr_monthly` at the start date; end = their `mrr` at 2024-04-30 (0 if gone); per-customer movement = expansion (end>start) / contraction (0<end<start) / churn (end=0) / flat (end=start>0). Adds customer counts per movement and % of start MRR per bridge step; T12M starts 2023-04-30, T6M starts 2023-10-31.
- **Waterfall long format** (`mart_a3_02`, `mart_a3_04`): (segment, step, step_order, amount) with Start/End as level bars and Churn/Contraction/Expansion as signed deltas, so Start − Churn − Contraction + Expansion = End for every segment — ready to drop into a Looker Studio waterfall chart with no further transformation.
- **Monthly NDR series** (`mart_a3_05_monthly_ndr_series`): applies the identical M-08 logic with a rolling 1-month window instead of 12 — base = customers with `prev_mrr > 0` (i.e. active at the prior month-end, from `fct_customer_mrr_monthly`'s own `LAG`), end = `mrr` this month-end. Computed for every available transition (2023-02-28..2024-04-30, 15 months) by segment, B2B and Total.
- **Monthly-compounded T12M** (`mart_a3_06_monthly_compounded_t12m`): compounds the 12 monthly NDR (and GRR) ratios for 2023-05-31..2024-04-30 via `EXP(SUM(LN(ratio)))` (portable to BigQuery; no `PRODUCT()` aggregate in ANSI/BigQuery SQL) and compares to the T12M snapshot from `mart_a3_01`.
- **Renewal-event view** (`mart_a3_07/08/09`): from `fct_subscriptions` (built on `int_subscription_periods`), all rows with `period_number > 1` (a renewal happened) and `start_date` in `[2023-05-01, 2024-04-30]` — the same population as WP13's cross-check (verified: 6,635 events total, ties exactly). Tenure bucket from `period_number` (2 / 3-4 / 5-8 / 9+, per the WP22 brief). MRR tier from `prev_mrr` (the pre-renewal MRR): `<100 / 100-300 / 300-600 / 600-1000 / 1000+`, chosen from the observed price ranges in `Docs/Datasets.md` so B2C ($33.25/$49), SMB ($134.70–$515.30) and Enterprise ($697.36–$1,293.77) each land in distinct tiers — **Proposed A-04**. % change bins = `mrr_delta / prev_mrr` in 7 buckets (`mart_a3_08`). Ended-period engagement (`mart_a3_09`) uses `LAG(active_days)`/`LAG(courses_seen)` over the *full*, unfiltered subscription history per user (computed before filtering to the renewal window), so it always reflects the true immediately-preceding period.
- **Expansion/contraction answer** (`mart_a3_10_expansion_contraction_answer`): joins the renewal-event totals (`mart_a3_07`), the T12M cohort totals (`mart_a3_01`) and each segment's current MRR (`mart_q1_mrr_apr24`) to express $ figures as a % of that segment's own MRR.

## Assumptions used (IDs)

- M-01, M-02, M-04, M-05, M-08 (NDR), M-09 (GRR), M-10 (expansion/contraction/churn + identity), D-12 (movement vocabulary), D-14 (`next_status`/`renewal_change` semantics already in `int_subscription_periods`).
- **Proposed A-04** (new): MRR-tier cutoffs for the renewal-event segmentation — `<100 / 100-300 / 300-600 / 600-1000 / 1000+` — chosen so each segment's base and expanded/contracted price points fall into distinct, non-overlapping tiers (see `Docs/Datasets.md` MRR ranges). Purely a reporting bucketing choice; does not affect any M-08..M-10 number.
- **Proposed D-15** (new): "Monthly-compounded NDR/GRR" as a secondary, robustness definition of T12M retention — product of 12 consecutive 1-month NDR/GRR ratios (rolling base = customers active at the *prior* month-end each month), vs. M-08/M-09's fixed 12-month-lookback cohort. Not a replacement for M-08/M-09 (the primary definition stays the fixed snapshot cohort) — reported side by side because the fixed cohort is small for SMB (52) and especially Enterprise (12), and the rolling-base compounded figure is far more stable at company level (within ~1pp of the snapshot for Total/B2B) while diverging materially (10–16pp) for the small segments, which is itself the finding.

## Checks performed (reconciliations, row counts)

- `sql/tests/test_a3_t12m_identity.sql` / `test_a3_t6m_identity.sql`: for every segment row in `mart_a3_01`/`mart_a3_03`, `start + expansion − contraction − churn = end` (tol. 0.01), `GRR ≤ 1`, `NDR ≥ GRR`, and `n_expansion + n_contraction + n_churn + n_flat = base_customers`. **PASS** (5/5 rows each).
- `sql/tests/test_a3_monthly_identity.sql`: same identity + GRR/NDR bounds for all 75 rows of `mart_a3_05_monthly_ndr_series`. **PASS**.
- `sql/tests/test_a3_waterfall_reconciles.sql`: the long-format waterfall tables (`mart_a3_02`, `mart_a3_04`) reconstruct to `Start − Churn − Contraction + Expansion = End` for every segment. **PASS** (10/10 rows).
- `sql/tests/test_a3_ties_mart_q4.sql`: `mart_a3_01`'s T12M snapshot matches `mart_q4_ndr_t12m` (method='M08_M09_M10', WP13) exactly on `base_customers`, `start_mrr`, `expansion_mrr`, `contraction_mrr`, `churn_mrr`, `end_mrr`, `ndr`, `grr` for all 5 segment rows. **PASS** — confirms the T12M numbers above (417 base, 63.70% NDR, 59.88% GRR) reproduce WP13 exactly.
- `sql/tests/test_a3_renewal_crosscheck.sql`: `mart_a3_07`'s renewal-event expansion/contraction totals tie exactly to `mart_q4_ndr_t12m`'s `renewal_crosscheck` method by segment (SMB $3,916.71/$793.52, Enterprise $956.19/$470.08). **PASS**.
- Manual: total renewal events (6,635) = WP13's cross-check total (5,803 + 757 + 75). B2B cohort roll-up (SMB+Enterprise) reconciles to B2B row on every $ column in both T12M and T6M tables.
- `work/WP22_ndr_decomposition/dev_build.py` run end to end: **ALL WP22 TESTS PASSED** (6/6 test files).

## Open issues / sensitivities

- **Small-n cohorts drive the T12M vs. monthly-compounded divergence.** SMB (52) and especially Enterprise (12) in the fixed T12M cohort are small enough that a single customer event swings the segment NDR by several points (already flagged in WP13). Section 2b makes this concrete: SMB's snapshot NDR (89.80%) is 16pp above its own monthly-compounded rate (73.81%); Enterprise's snapshot (71.75%) is 11pp *below* its compounded rate (83.04%) — the two methods point in opposite directions for the two smallest segments, which is itself evidence that neither single-cohort number should be treated as a precise point estimate for those segments; the T6M and monthly views are the more defensible read for forward-looking planning.
- **The monthly-compounded T12M is a rolling-cohort approximation, not an exact answer to M-08.** Each month's base includes customers who signed up after the T12M window's start, so early months' compounded ratios reflect a different (smaller, newer) population than later months' — the identity "12-month compounding = fixed-cohort NDR" only holds exactly if the cohort never changes composition, which it does here by design (see Proposed D-15).
- **Contraction is structurally small (never the main driver of NDR loss) in this dataset.** Both segments' contraction $ (SMB $793.52, Enterprise $470.08 over 12 months) is a fraction of churn $ (SMB $2,171.57, Enterprise $2,805.00 in the T12M cohort) — the "where is contraction concentrated" answer is a second-order finding; the first-order lever for NDR improvement in every segment (including B2C, which has zero expansion or contraction by construction) is logo/MRR churn, not downgrade prevention. WP23 should weight retention initiatives accordingly.
- **B2C has no expansion or contraction at all** (verified data fact: B2C `mrr` is fixed at $49/$33.25) — its entire NDR gap from 100% is churn. This is unchanged from WP13 and confirmed again here at T6M (65.19%) and via the monthly series (40.62% compounded — even lower, reflecting more concentrated churn among the later, larger cohorts used in the rolling base).
- **MRR tier and tenure bucket boundaries are reporting choices** (Proposed A-04, and the tenure buckets given in the WP22 brief), not metric definitions — a different cut (e.g. tiers by segment-relative quantile instead of absolute $) could shift which cell looks "largest," though the qualitative concentration finding (SMB mid-tenure / base-tier; Enterprise early-tenure / base-tier) held up under both the $ and count views.
- **Engagement does not predict expansion/contraction at renewal** (unlike churn), based on the ended-period active_days/courses_seen comparison in `mart_a3_09`. This is a genuine null finding worth flagging to WP23: an engagement-based early-warning system (hypothesis 1 in the plan) is well-supported for *churn* but should not be expected to predict *upsell/downgrade* — those look driven by commercial/contractual factors not observed directly in this dataset (seat counts, negotiated renewals).

## Business insights for WP23 (retention strategy)

1. **Churn, not contraction, is the lever.** In every segment, churned MRR dwarfs contraction MRR (SMB: $2,171.57 churn vs. $793.52 contraction over 12 months on the larger renewal base; Enterprise: $2,805.00 vs. $470.08). A "prevent downgrades" playbook alone cannot move NDR much — WP23's initiatives should prioritize logo retention (especially B2C, where NDR=GRR=43.08% T12M / 65.19% T6M and there is zero expansion to offset any loss).
2. **SMB is the expansion engine — protect and replicate it.** SMB expands 7.27% of its own current MRR per year at renewal (vs. Enterprise's 1.11%) and does so across 129 renewal events (vs. Enterprise's 8) — a broad-based upsell motion (likely seat growth on a $199 base plan), not a few large deals. A lightweight, self-serve "add seats" nudge at renewal for SMB accounts already past their first renewal could extend this pattern; it is unlikely to be replicable in Enterprise, which is much more logo-concentrated (12–93 customers across the study period).
3. **Two different contraction-prevention windows by segment.** SMB contraction risk peaks at the 5th–8th renewal (roughly 6 months to just over a year of tenure) — a "re-engagement/value-realization" check-in at that renewal milestone is the highest-leverage timing. Enterprise contraction risk peaks at the 2nd renewal — an early post-onboarding QBR (quarterly business review) focused on demonstrating value before that first true renewal decision would directly target Enterprise's actual risk window (consistent with hypothesis 3 in the plan).
4. **Don't expect an engagement dashboard to catch contraction/expansion — only churn.** Since active_days/courses_seen of the ended period don't differ between expanding, contracting and flat renewals, a CS team using engagement scores to prioritize "at-risk of downgrade" accounts will likely be chasing noise for that outcome; engagement scoring should stay targeted at churn risk (where the signal is strong, per `Docs/Datasets.md`) and a separate, account/commercial-data-driven trigger (seat utilization, contract terms, price-increase timing) should be used for expansion/contraction.
5. **Use T6M or the monthly series, not the 417/64/12-customer T12M snapshot, for target-setting.** The T12M snapshot cohort is the correct number to report for M-08 compliance (and it ties exactly to WP13), but its SMB/Enterprise NDR are each driven by a few dozen customers. T6M's much larger, more current base (1,124 total, 207 B2B) and the monthly-compounded series are the more reliable inputs for setting 2024/2025 retention targets or an NDR component in the scenario model (WP31).

## Files produced

- `sql/marts/mart_a3_01_t12m_decomposition.sql`
- `sql/marts/mart_a3_02_t12m_waterfall_long.sql`
- `sql/marts/mart_a3_03_t6m_decomposition.sql`
- `sql/marts/mart_a3_04_t6m_waterfall_long.sql`
- `sql/marts/mart_a3_05_monthly_ndr_series.sql`
- `sql/marts/mart_a3_06_monthly_compounded_t12m.sql`
- `sql/marts/mart_a3_07_renewal_segmentation.sql`
- `sql/marts/mart_a3_08_renewal_pctchange_bins.sql`
- `sql/marts/mart_a3_09_renewal_engagement.sql`
- `sql/marts/mart_a3_10_expansion_contraction_answer.sql`
- `sql/tests/test_a3_t12m_identity.sql`, `test_a3_t6m_identity.sql`, `test_a3_monthly_identity.sql`, `test_a3_waterfall_reconciles.sql`, `test_a3_ties_mart_q4.sql`, `test_a3_renewal_crosscheck.sql`
- `work/WP22_ndr_decomposition/dev_build.py` (isolated build script)
- `work/WP22_ndr_decomposition/dev.duckdb` (isolated dev DB, not `db/platzi.duckdb`)
- `work/WP22_ndr_decomposition/exports/*.csv` (one CSV per mart_a3_* table, for Looker Studio / Sheets)
