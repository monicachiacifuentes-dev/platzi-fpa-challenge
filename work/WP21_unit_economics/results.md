# WP21 — A2: Unit Economics Deep-Dive

> **Revision note (lead-analyst review):** this version (1) makes the GM **base
> case allocate all COGS by share of MRR** (neutral default; the previous base —
> CS Salaries/Infrastructure by customer count — is now a labelled **downside
> sensitivity**), (2) **caps the base-case LTV lifetime at 60 months** (Proposed
> A-18; 36-month sensitivity and an uncapped reference are also reported), and
> (3) moves **all** synthesis (lifetime, LTV, CAC payback, the sensitivity grid)
> into pure SQL marts so `sql/run_pipeline.py` produces them with no code change
> — see "Pipeline integration" in Method. Everything else (CAC, D-05/D-06,
> funnel, ARPA, survival curve construction) is unchanged from the prior draft.

## Answer (numbers first)

### Headline table (base case: GM% = all COGS by MRR share; lifetime capped at 60 months; CAC = T6M fully loaded)

| Segment | ARPA (T6M avg, $/mo) | GM% (base, neutral) | CAC fully loaded (T6M) | Lifetime (base, $ curve, 60mo cap) | LTV (base) | LTV:CAC | CAC payback (months) | Retention-adj. payback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B2C | 42.21 | 29.3% | 392.22 | 15.9 | 197 | **0.50x** | 31.7 | never (15-mo horizon) |
| SMB | 177.94 | 29.3% | 759.41 | 42.5 | 2,215 | **2.92x** | 14.6 | never (14-mo horizon) |
| Enterprise | 847.75 | 29.3% | 4,249.00 | 36.9 | 9,178 | **2.16x** | 17.1 | never (11-mo horizon) |
| **Total** | 102.72 | 29.3% | 617.19 | 26.6 | 800 | 1.30x | 20.5 | never (15-mo horizon) |

Benchmarks: LTV:CAC ≥ 3x, payback < 12 months (B2C/SMB) / < 18 months (Enterprise).
**Under this neutral base case, no segment clears the LTV:CAC ≥ 3x bar (SMB comes
closest at 2.92x); only Enterprise clears the payback bar (17.1 < 18 months).**
This is a materially more conservative headline than a differentiated-cost-driver
allocation would give (see the sensitivity below) — that is the intended effect
of removing the customer-count cost-driver assumption from the base case.

### Downside sensitivity (CS Salaries & Infrastructure by active-customer share — the *previous* base)

| Segment | GM% (sensitivity) | Lifetime (60mo cap) | LTV (sensitivity) | LTV:CAC | CAC payback (months) |
|---|---:|---:|---:|---:|---:|
| B2C | **-37.0%** | 15.9 | **-249** | **-0.63x** | n/a (negative GM) |
| SMB | 49.1% | 42.5 | 3,709 | **4.88x** | 8.7 |
| Enterprise | 70.2% | 36.9 | 21,997 | **5.18x** | 7.1 |
| Total | 29.3% | 26.6 | 800 | 1.30x | 20.5 |

**This sensitivity is not uniformly a "downside"**: it worsens B2C sharply (its
82%-of-customers-but-31%-of-revenue mix means a per-head cost split hits it
hard) but it is an *upside* for SMB and Enterprise (higher margin than the
neutral 29.3% base) — so read it as "the differentiated, but assumption-heavy,
case" rather than a one-directional pessimistic scenario. See Open issues for
why we did not make this the headline.

### CAC by segment (M-13, D-05/D-06) — unchanged from the prior draft

| Segment | Period | Marketing spend | New paying customers | Allocated G&A (base) | CAC marketing-only | **CAC fully loaded (base)** |
|---|---|---:|---:|---:|---:|---:|
| B2C | T16M | 789,794.31 | 2,225 | 111,874.93 | 354.96 | 405.24 |
| B2C | T6M | 363,276.25 | 1,052 | 49,337.69 | 345.32 | **392.22** |
| SMB | T16M | 253,809.03 | 361 | 35,952.23 | 703.07 | 802.66 |
| SMB | T6M | 122,354.57 | 183 | 16,617.36 | 668.60 | **759.41** |
| Enterprise | T16M | 481,235.59 | 109 | 68,167.37 | 4,415.01 | 5,040.39 |
| Enterprise | T6M | 216,974.21 | 58 | 29,467.95 | 3,740.93 | **4,249.00** |
| Total | T16M | 1,524,838.93 | 2,695 | 215,994.53 | 565.80 | 645.95 |
| Total | T6M | 702,605.03 | 1,293 | 95,423.00 | 543.39 | **617.19** |

Acquisition share of G&A = marketing / (marketing + support costs) → **49.2% (T16M) / 51.0% (T6M)**
of total G&A is allocated to acquisition; split across segments by share of marketing spend.

### D-06 funnel view (marketing's `new_users_acquired`, T16M) — unchanged

| Segment | Marketing spend | Signups (marketing) | Paying customers (users.csv) | Cost per signup | Signup→paid conversion |
|---|---:|---:|---:|---:|---:|
| B2C | 789,794.31 | 21,573 | 2,225 | $36.61 | **10.3%** |
| SMB | 253,809.03 | 695 | 361 | $365.19 | **51.9%** |
| Enterprise | 481,235.59 | 82 | 109 | $5,868.73 | **132.9%** ⚠ |

⚠ **Enterprise caveat (D-11):** users.csv has *more* Enterprise customers (109) than marketing
claims it acquired (82) — marketing's Enterprise count likely tracks closed *deals*, not the same
population as `users.csv` signups (1 user_id = 1 customer, D-11; a deal can add several named
users). We never use marketing's Enterprise signup count as a CAC denominator.

Cost per signup by channel (B2C/SMB only — paying customers can't be split by channel, T16M):

| Segment | Channel | Spend | Signups | Cost/signup |
|---|---|---:|---:|---:|
| B2C | Organic | 72,159.60 | 4,987 | **$14.47** |
| B2C | Content | 116,712.76 | 4,039 | $28.90 |
| B2C | Paid Search | 345,766.52 | 7,746 | $44.64 |
| B2C | Paid Social | 255,155.43 | 4,801 | $53.15 |
| SMB | Content | 51,254.36 | 189 | **$271.19** |
| SMB | Paid Search | 124,953.22 | 325 | $384.47 |
| SMB | Paid Social | 77,601.45 | 181 | $428.74 |

### Gross margin by segment (M-12; base **revised** per review) — Apr-24 snapshot

| Segment | Revenue Apr-24 | Active cust. Apr-24 | GM% base (all COGS by MRR) | GM% downside sensitivity (customer-weighted) |
|---|---:|---:|---:|---:|
| B2C | 64,365.00 | 1,536 | **40.9%** | -17.1% |
| SMB | 53,869.37 | 303 | 40.9% | 56.5% |
| Enterprise | 86,474.72 | 102 | 40.9% | 74.4% |
| Total | 204,709.09 | 1,941 | 40.9% | 40.9% |

The base column is identical across every segment for a given month **by construction**:
allocating 100% of COGS strictly proportional to revenue mathematically forces every
segment to the company-average margin (new test: `test_a2_gm_base_uniform`). That is
precisely why this is the safer *default* (it injects no unverifiable claim about
which segment "deserves" more support cost) — and precisely why it cannot, by
itself, show any segment as more or less profitable than the company average.
The customer-weighted view is kept as the sensitivity that *can* show a
difference, at the cost of assuming a specific (and disputable) cost driver.

### ARPA (unchanged)

| Segment | Apr-24 | T6M avg |
|---|---:|---:|
| B2C | 41.90 | 42.21 |
| SMB | 177.79 | 177.94 |
| Enterprise | 847.79 | 847.75 |
| Total | 105.47 | 102.72 |

### Retention curve & lifetime (M-14, Proposed A-18 cap)

| Segment | Reliable horizon (exposed_n≥20) | Tail method ($ curve) | Dollar decay/mo | Lifetime, $, 36mo | Lifetime, $, **60mo (base)** | Lifetime, $, uncapped | 1/decay cross-check |
|---|---:|---|---:|---:|---:|---:|---:|
| B2C | 15 mo | last3 | 4.94% | 14.2 | **15.9** | 16.7 | 20.2 |
| SMB | 14 mo | last3, floored at logo (full_range) | 1.22% | 28.9 | **42.5** | 82.2 | 81.8 |
| Enterprise | 11 mo | last3 | 1.83% | 26.8 | **36.9** | 55.1 | 54.6 |

The cap visibly matters most for SMB (82.2 uncapped vs. 42.5 at 60 months — a
1.9x difference) because its tail decay rate is the smallest of the three
(after the A-17 floor). See Open issues for why the uncapped number is not the
base case even after applying the A-17 floor.

## Method

1. **New paying customers (D-06 base), acquisition spend, G&A allocation (D-05), CAC (M-13), ARPA, funnel view, survival curve construction (M-14):** unchanged from the prior draft. See `sql/marts/mart_a2_01..07*.sql`, `mart_a2_09_arpa.sql`, `mart_a2_10_survival_curve.sql`.
2. **Gross margin (M-12) — revised base case:** revenue = monthly MRR by segment from `fct_customer_mrr_monthly`. COGS = CS Salaries + Infrastructure + Content Production. **Base (neutral default):** all three categories allocated by segment's share of MRR that month — chosen because there is no cost-driver data in the datasets to justify any other split, and a revenue-proportional split cannot manufacture an artificial cross-segment difference. **Downside sensitivity** (was the base in the prior draft): CS Salaries & Infrastructure by segment's share of *active customers*; Content Production still by MRR share (identical in both cases — one `cogs_content` column). Both live in `mart_a2_08_gm_monthly.sql` (`*_base` vs. `*_sens_customer_weighted` columns).
3. **Lifetime cap (Proposed A-18):** expected lifetime = Σ curve over the reliable horizon (`exposed_n ≥ 20`, Proposed A-15) + a **finite** geometric tail truncated at a total horizon of 60 months (base), 36 months (sensitivity), or left uncapped (infinite geometric tail, reference only). The tail decay rate itself is unchanged (cascading last3 → last6 → full_range average transition rate; Proposed A-16 fallback-to-logo and A-17 floor-at-logo for the dollar curve — see prior draft's rationale, still fully in force, now in `mart_a2_11_lifetime.sql`). Finite-tail closed form: `last_value × (1−rate) × (1 − (1−rate)^n) / rate`, where `n = cap − 1 − k_rel`; uncapped is the same formula's `n → ∞` limit (`last_value × (1−rate) / rate`).
4. **LTV, LTV:CAC, CAC payback (M-15):** LTV = ARPA(T6M avg) × GM%(T6M avg, **base = all-by-MRR**) × lifetime($ curve, **60-month cap**). LTV:CAC and CAC payback as before. **Retention-adjusted payback** unchanged in concept (cumulative gross profit per acquired customer vs. CAC) but is evaluated only over the **observed reliable horizon** (`k_rel`, e.g. 15/14/11 months) — the 60-month LTV cap is a separate, LTV-only construct and is *not* used to extend the retention-adjusted-payback check, since that check is explicitly about what the *observed* data supports, not an extrapolated horizon.
5. **Pipeline integration (item 3 of the review):** chose **option (a) — pure SQL**. `mart_a2_11_lifetime.sql`, `mart_a2_12_unit_economics_summary.sql` and `mart_a2_13_sensitivity.sql` now hold everything that used to be a `dev_build.py` pandas step (the cascading tail-rate fallback/floor logic turned out to be expressible with bounded `CASE`/`ROW_NUMBER`/window-function SQL, since there are only 3 candidate windows and 2 fallback rules per segment — no unbounded control flow was actually needed). Because `sql/run_pipeline.py`'s own `MARTS` list building code already globs every `.sql` file in `sql/marts/` that isn't in its hardcoded list (`MARTS += sorted(p.stem for p in (SQL_DIR / "marts").glob("*.sql") if p.stem not in MARTS)`), **all 13 `mart_a2_*` files, including the new 11/12/13, will be picked up automatically** the next time `run_pipeline.py` runs — no edit to that file was needed or made. `work/WP21_unit_economics/dev_build.py` now only copies the dev db, builds the 13 marts, runs the 9 tests, exports CSVs, and regenerates `sheet_inputs.csv` by reading the finished SQL tables (no python-side numeric synthesis remains).

## Assumptions used (IDs)

- M-01, M-02, M-04, M-05/D-11, M-12, M-13, M-14, M-15; D-05, D-06 (approved, unchanged).
- **Revised GM base (supersedes the "Proposed D-07 update" in the prior draft):** all COGS by MRR share is now the base case; the customer-weighted split (previously proposed as the D-07 update) is a labelled downside sensitivity. Recorded here as the FP&A working assumption for this WP; not written into `Docs/Plan_and_Index.md` (per isolation rules) — the lead analyst should reconcile this with D-07 in the plan directly.
- Proposed A-15 (curve reliability threshold n≥20), A-16 (dollar-tail fallback to logo churn), A-17 (dollar-tail floor at logo churn) — unchanged.
- **Proposed A-18 (new): LTV horizon cap = 60 months (base); 36 months (sensitivity); uncapped (reference only, not used in any headline number).**
- Benchmark thresholds: LTV:CAC ≥ 3x; CAC payback < 12 months (B2C/SMB), < 18 months (Enterprise).

## Checks performed (reconciliations, row counts)

All in `sql/tests/test_a2_*.sql`, run by `work/WP21_unit_economics/dev_build.py` — **9/9 PASS**
(3 new tests added this revision):

- `test_a2_new_customers_totals`, `test_a2_marketing_funnel_totals`, `test_a2_cac_positive`,
  `test_a2_survival_k0` — unchanged, still PASS.
- `test_a2_gm_identity` — extended to check **both** the base and the sensitivity COGS columns
  reconcile to actual company costs for the Total segment row, every month. PASS.
- `test_a2_gm_segment_sum` — unchanged (revenue/active-customer identity, allocation-agnostic). PASS.
- **New `test_a2_gm_base_uniform`** — asserts `gm_pct_base` is identical (±0.0005) across B2C/SMB/Enterprise for every month, i.e. confirms the neutral allocation's defining property. PASS.
- **New `test_a2_lifetime_cap_monotonic`** — asserts lifetime is non-decreasing as the cap widens (36 ≤ 60 ≤ uncapped) for both curves, every segment. PASS.
- **New `test_a2_summary_ltv_consistency`** — asserts `mart_a2_12`'s base lifetime matches `mart_a2_11`'s `lifetime_dollar_60` and `ltv_base` reconstructs from `arpa × gm% × lifetime` within a $2 rounding-cascade tolerance. PASS.
- **Manual cross-check:** company Apr-24 GM% (Total row) = 40.93%, unchanged from the prior draft (allocation method never changes the *company* total, only its split across segments) — still matches `mart_q1_mrr_apr24`.

## Open issues / sensitivities

- **The neutral base case is intentionally conservative and compresses the segment story.** With
  GM% now uniform (29.3% T6M avg) across B2C/SMB/Enterprise, the remaining differentiators are
  purely ARPA, CAC and the retention curve — and under those alone, **no segment clears LTV:CAC≥3x,
  and the retention-adjusted payback is "never" for every segment** within its observed reliable
  horizon (a real change from the prior draft, where SMB/Enterprise cleared both bars comfortably
  because their assumed support-cost efficiency was baked into the base GM%). This is not a bug —
  it is the direct, expected consequence of removing an unverifiable cost-driver assumption from
  the default. **We recommend the executive summary present both tables side by side** rather than
  picking one "true" number: the neutral case is the defensible floor; the customer-weighted case
  is the more differentiated (and, we believe, economically more plausible) picture, given that
  enterprise support interactions are typically far less frequent per revenue dollar than
  self-serve B2C ones — but it rests on an assumption the data cannot itself confirm.
- **SMB is the one segment sitting right at the LTV:CAC=3x line (2.92x base / 4.88x downside
  sensitivity)** — small changes in any input (a slightly different cap, a slightly different
  G&A split) flip its benchmark verdict. Treat SMB as "borderline-pass," not a clean pass or fail,
  under the neutral base.
- **Lifetime cap trade-off (A-18):** capping at 60 months prevents the implausible SMB uncapped
  figure (82 months, itself already the product of the A-17 floor fix — the *unfloored* number was
  ~160 months) from flowing into LTV, but it also mechanically shrinks Enterprise's and SMB's LTV
  well below what their own survival curve's 1/decay cross-check (81.8 / 54.6 months) would imply.
  60 months (5 years) was chosen as a round, standard SaaS planning horizon; 36 months is provided
  as a more conservative alternative and the uncapped figure as a pure reference — none of the
  three is more "correct" than another without a business view on realistic customer lifespan.
- **Retention-adjusted payback uses the observed horizon, not the 60-month cap** (see Method #4) —
  so it can (and does) say "never" even when the capped-lifetime LTV:CAC looks reasonable (e.g.
  Enterprise's 2.16x LTV:CAC vs. "never" retention-adjusted payback). These two metrics are
  answering different questions (LTV:CAC = "is this segment worth acquiring at all, taking a
  60-month view", retention-adjusted payback = "does the *observed* data already prove we'll get
  the CAC back") and should not be expected to agree.
- **Enterprise's curve is short and thin** (max reliable k = 11 months, exposed_n as low as 20) —
  a single logo swings the tail decay rate meaningfully; treat its 60-month LTV ($9,178 base /
  $21,997 downside sensitivity) as directional.
- **Deviation avoided this revision:** the prior draft flagged a deviation from "pure SQL marts"
  (the lifetime/LTV synthesis was done in pandas). That deviation is now resolved — see Method #5;
  all 13 `mart_a2_*` files are pure SELECT statements and will be picked up by `sql/run_pipeline.py`
  automatically without any edit to that file.
- **`test_a2_survival_k0` tolerance (carried over):** 4 of 2,695 users (3 B2C, 1 SMB) have
  `mrr = 0` in their own signup month's grid row because their only/first subscription starts and
  churns within the same calendar month with `end_date` landing exactly on that month's last day —
  a genuine M-02-at-k=0 edge case, not a bug; test relaxed to `logo_survival ≥ 0.99`.
- **CAC monthly table (`mart_a2_07`) is marketing-spend-only, no G&A** (unchanged rationale: G&A
  allocation is only meaningful pooled over a period; a single month's SMB/Enterprise split would
  be noisy). Fully loaded CAC is reported only at T16M/T6M.
- Small-n caution across the board: Enterprise T6M base = only 58 new customers; SMB T6M = 183.

## Files produced

- SQL marts (`sql/marts/`): `mart_a2_01_new_paying_customers.sql`, `mart_a2_02_marketing_spend_segment_monthly.sql`, `mart_a2_03_funnel_segment_monthly.sql`, `mart_a2_04_funnel_channel_total.sql`, `mart_a2_05_gna_allocation.sql`, `mart_a2_06_cac_fully_loaded.sql`, `mart_a2_07_cac_monthly.sql`, `mart_a2_08_gm_monthly.sql` (revised base/sensitivity), `mart_a2_09_arpa.sql`, `mart_a2_10_survival_curve.sql`, **`mart_a2_11_lifetime.sql` (new, pure SQL)**, **`mart_a2_12_unit_economics_summary.sql` (new, pure SQL)**, **`mart_a2_13_sensitivity.sql` (new, pure SQL, includes the requested GM×lifetime-cap grid for SMB/Enterprise)**.
- Tests (`sql/tests/`): `test_a2_new_customers_totals.sql`, `test_a2_marketing_funnel_totals.sql`, `test_a2_gm_identity.sql` (extended), `test_a2_gm_segment_sum.sql`, `test_a2_survival_k0.sql`, `test_a2_cac_positive.sql`, **`test_a2_gm_base_uniform.sql` (new)**, **`test_a2_lifetime_cap_monotonic.sql` (new)**, **`test_a2_summary_ltv_consistency.sql` (new)**.
- `work/WP21_unit_economics/dev_build.py` — isolated build script (copies `db/platzi.duckdb` → `dev.duckdb`, builds all 13 SQL marts, runs the 9 tests, exports CSVs, writes `sheet_inputs.csv`; no python-side numeric synthesis remains).
- `work/WP21_unit_economics/dev.duckdb` — dev database (isolated copy; never overwrites `db/platzi.duckdb`).
- `work/WP21_unit_economics/marts_csv/*.csv` — CSV export of all 13 `mart_a2_*` tables.
- `work/WP21_unit_economics/sheet_inputs.csv` — 99-row tidy (id, name, value, unit, source, note) list of every input/assumption for the WP40 Google Sheet model (regenerated from the new marts).
- This file: `work/WP21_unit_economics/results.md`.

## Business insights (capital allocation)

1. **Under the neutral base case, Enterprise is the only segment that clears its payback benchmark
   (17.1 of 18 months) — but it's close, and its LTV:CAC (2.16x) still falls short of 3x.** The
   $4,249 T6M CAC is the largest lever here: it is driven mostly by Sales Team cost per closed
   account, not by the acquisition-related G&A allocation (0%/25%/50% G&A sensitivity only moves
   Enterprise CAC $498, from $3,741 to $4,239 — a rounding error next to the $848 ARPA gap). If
   Enterprise sales efficiency (deals per rep, or average deal size) can improve even modestly, the
   segment moves decisively into "clear pass" territory on both benchmarks.
2. **SMB is the fulcrum segment — its verdict genuinely depends on which GM assumption and which
   lifetime cap you believe.** At 2.92x LTV:CAC (neutral, 60mo cap) it's a hair below benchmark;
   at 4.88x (customer-weighted GM, same cap) it's a clear pass. Because SMB's own survival curve is
   the most stable and longest of the three (lowest small-n noise after the tail floor), this is
   the segment where getting the GM cost-driver question right (rather than defaulting to a
   revenue-proportional split) will most change the acquisition-budget decision — **worth a real
   cost-accounting exercise (does CS truly scale with SMB customer count or with SMB revenue?)
   before the next budget cycle**, rather than resolving it by assumption either way.
3. **B2C fails every benchmark under both allocations** (0.50x / -0.63x LTV:CAC) and is 52% of
   T16M marketing spend. Even the friendliest allocation only gets B2C to break-even-ish LTV:CAC.
   The lowest-risk move is not a blanket B2C spend cut but a **channel-level reallocation within
   B2C**: Organic ($14.47/signup) and Content ($28.90/signup) are 3–4x cheaper than Paid Social
   ($53.15/signup) for the same funnel; shifting paid B2C budget toward earned/content channels
   improves B2C's CAC directly without touching the GM debate at all.
4. **G&A allocation policy is not the lever to argue about.** Across the entire 0%/25%/50%
   sensitivity band, CAC moves by only ~$50–500 per segment (see the CAC table above) — a rounding
   error next to the GM-allocation swing (which moves SMB's LTV from $2,215 to $3,709, a $1,494
   difference, purely from a costing-methodology choice). **Prioritize resolving the GM
   cost-driver question over further G&A debate.**
5. **Use the 60-month cap (not the uncapped curve) for any external-facing LTV number, and flag the
   36-month figure whenever the audience is skeptical of long-tail SaaS retention assumptions** —
   the gap between 36-month and uncapped LTV is enormous for SMB/Enterprise (SMB: $1,504 → $4,284,
   a 2.8x range) purely from the horizon choice, with no change in any underlying driver. Any
   board-level LTV:CAC claim should always state which horizon it uses.
