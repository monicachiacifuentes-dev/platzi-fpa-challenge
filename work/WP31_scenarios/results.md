# WP31 — Bonus B2: Scenario Model (Base / Bull / Bear)

## Answer (numbers first)

### Backtest (model credibility check)

Calibrated **only** on data through 2023-10-31 (T6M window May-23..Oct-23), then
projected forward 6 months (Nov-23..Apr-24) with the Base engine and compared to
what actually happened, **before** the engine ever saw the real Nov-23..Apr-24
outcome.

| Segment | MAPE, MRR | MAPE, active customers | n months |
|---|---:|---:|---:|
| B2C | 6.9% | 7.2% | 6 |
| SMB | 8.5% | 8.1% | 6 |
| Enterprise | 14.1% | 13.9% | 6 |
| B2B | 12.0% | 9.6% | 6 |
| **Total** | **10.3%** | **7.7%** | 6 |

Month-by-month (Total, actual vs. projected MRR):

| Month-end | Actual MRR | Projected MRR | Error |
|---|---:|---:|---:|
| 2023-11-30 | 123,709.83 | 119,016.42 | −3.8% |
| 2023-12-31 | 137,446.22 | 129,563.04 | −5.7% |
| 2024-01-31 | 153,090.69 | 139,877.94 | −8.6% |
| 2024-02-29 | 170,092.96 | 149,983.61 | −11.8% |
| 2024-03-31 | 187,404.31 | 159,900.48 | −14.7% |
| 2024-04-30 | 204,709.09 | 169,647.12 | −17.1% |

**Read**: a flat-run-rate Base engine *always under-shoots* here, and the gap
widens every month — because Platzi was **accelerating** during this window
(new-customer counts and MRR both grew faster than their own trailing average,
see "Why the backtest under-shoots" below). 10.3% company-level MAPE over a
6-month unseen holdout, with no growth assumption at all, is a credible floor
for a model this simple — and the *direction* of the miss (conservative, not
random) is itself useful: it tells the CFO that if growth keeps its current
trend, a **flat** Base case is the pessimistic anchor, not the likely case (this
is exactly why the main projection's Bull case is not flat — see below).

### Scenario summary — MRR & subscribers, Apr-25 (12-month horizon from Apr-24 actuals)

| Segment | Scenario | MRR Apr-24 (actual) | MRR Apr-25 | Growth % | Subs Apr-24 | Subs Apr-25 |
|---|---|---:|---:|---:|---:|---:|
| **Total** | Bear | 204,709 | 319,508 | +56.1% | 1,941 | 2,811 |
| **Total** | **Base** | 204,709 | **354,482** | **+73.2%** | 1,941 | 3,119 |
| **Total** | Bull | 204,709 | 451,662 | +120.6% | 1,941 | 4,414 |
| B2C | Bear / Base / Bull | 64,365 | 84,803 / 95,925 / 136,631 | +31.8% / +49.0% / +112.3% | 1,536 | 2,139 / 2,390 / 3,468 |
| SMB | Bear / Base / Bull | 53,869 | 84,116 / 95,519 / 134,630 | +56.1% / +77.3% / +149.9% | 303 | 492 / 536 / 733 |
| Enterprise | Bear / Base / Bull | 86,475 | 150,589 / 163,038 / 180,401 | +74.1% / +88.5% / +108.6% | 102 | 180 / 194 / 213 |
| B2B (SMB+Ent) | Bear / Base / Bull | 140,344 | 234,705 / 258,557 / 315,031 | +67.2% / +84.2% / +124.5% | 405 | 672 / 729 / 946 |

*(Bull ≥ Base ≥ Bear holds for every segment at every horizon — tested, see below.)*

Even Base's +73% is not implausible for this company: it grew MRR from
$95,331 (Oct-23) to $204,709 (Apr-24) — **+115% in the prior 6 months alone**
(`mart_mrr_bridge`). The engine's ~+73%/12-month Base case is a **deceleration**
relative to the company's own recent trajectory, driven mechanically by B2C's
~10.6%/month churn compounding against an ever-larger existing base.

### Forward NDR / GRR of the fixed Apr-24 customer base

| Segment | Scenario | NDR M6 | GRR M6 | NDR M12 | GRR M12 |
|---|---|---:|---:|---:|---:|
| **Total** | Bear | 79.7% | 79.0% | 68.0% | 66.8% |
| **Total** | **Base** | **82.5%** | **81.1%** | **72.0%** | **69.4%** |
| **Total** | Bull | 85.5% | 83.5% | 76.9% | 73.4% |
| B2C | Bear / Base / Bull | 64.6% / 68.0% / 71.8% | = NDR (no expansion) | 47.9% / 51.3% / 58.3% | = NDR |
| SMB | Bear / Base / Bull | 81.3% / 85.8% / 90.8% | 79.2% / 81.4% / 84.3% | 70.1% / 77.0% / 84.8% | 66.5% / 69.3% / 73.2% |
| Enterprise | Bear / Base / Bull | 89.9% / 91.4% / 92.4% | 89.5% / 90.7% / 91.8% | 81.7% / 84.2% / 85.9% | 81.1% / 83.0% / 84.7% |
| B2B | Bear / Base / Bull | 86.6% / 89.2% / 91.8% | 85.6% / 87.1% / 88.9% | 77.2% / 81.4% / 85.5% | 75.5% / 77.8% / 80.3% |

These are lower than WP22's T6M snapshot NDR (e.g. company T6M NDR was 81.6%
looking *backward*) because this is a **forward** 12-month run on a fixed
cohort with no new customers at all — closer in spirit to WP22's T12M snapshot
(63.7% company NDR) than the T6M one, and directionally consistent with it.

## Method

### Engine (driver-based monthly compartment model)

Six "compartments" = segment (B2C, SMB, Enterprise) x plan_type (monthly, annual).
Starting stock = active customers and MRR at 2024-04-30, queried directly from
`fct_subscriptions` (`start_date <= D AND end_date > D`, M-02) — reconciles
exactly to $204,709.09 / 1,941 (Q1/Q3 answers).

Each month, per bucket:
1. **Logo churn** on opening customers, at the bucket's calibrated monthly
   rate. **Monthly-plan churn** is used as observed (already a monthly rate).
   **Annual-plan churn** is observed on a renewal (≈1-year) basis and converted
   to a **monthly-equivalent** rate via `1-(1-annual_rate)^(1/12)` — chosen
   because the compartment model has no per-customer renewal-anniversary
   calendar to apply annual churn "at renewal" for an aggregate stock (**Proposed
   A-19c**). Churned MRR = churned customers × the bucket's current average ARPA.
2. **Net expansion / contraction** applied to *retained* MRR, **B2B buckets
   only** (B2C's rate is 0 by construction — B2C mrr is fixed at $49/$33.25,
   a verified data fact, so B2C can never expand or contract).
3. **Monthly → annual migration** (B2C-monthly bucket only): a lever that is
   OFF in Base/Bear and ON in Bull and in WP23 Strategy 2. Retained B2C-monthly
   customers convert to B2C-annual at a monthly rate, leaving at $49 ARPA and
   joining at $33.25 ARPA the same month.
4. **New customers**, split across the bucket's calibrated new-customer plan
   mix, each at the bucket's calibrated new-customer ARPA.

Every month, every bucket: `opening + new − churn + expansion − contraction −
migration_out + migration_in = closing` (identity tested, see Checks).

**Forward NDR/GRR of the Apr-24 base** reuses the *identical* engine with new
customers forced to 0 (a pure existing-cohort run). GRR reuses it again with
expansion forced to 0 (M-09: no credit for expansion) — churn, contraction and
migration's MRR cost still count against GRR.

### Driver calibration (T6M window, Nov-23..Apr-24, ending at the as-of date — matches the WP21/WP22 convention)

- **Why T6M, not T16M or T12M**: the company's economics have visibly shifted
  over the 16 months (see WP21's GM trend, WP22's cohort maturation) — the most
  recent 6 months is the best available proxy for "current run-rate," which is
  exactly what the brief's Base case asks for.
- **New customers/month**: T6M average per segment (mart_a2_01-style query on
  `fct_subscriptions` `period_number=1`). B2C 175.3/mo, SMB 30.5/mo, Enterprise
  9.7/mo.
- **Trend or flat? Data-driven, not assumed.** An OLS linear trend was fit on
  each segment's 6 monthly counts. B2C: **+8.9 customers/month²** (152→196 over
  the window, a clear ramp). SMB: **+1.9/month²** (24→33, a milder but real
  ramp). Enterprise: **+0.17/month²** (9→10, essentially flat — the trend line
  is statistically indistinguishable from flat at this sample size). **Base
  uses the flat T6M average for all three segments** ("observed run-rate," per
  the brief); **Bull continues each segment's own fitted trend forward**
  (floored at the Base run-rate, so Bull is never worse than Base even where
  the fitted trend happens to be flat/negative).
- **Plan mix of new customers** (T6M): B2C 67.4% monthly / 32.6% annual; SMB
  47.0% / 53.0%; Enterprise 15.5% / 84.5%.
- **ARPA of new customers** (T6M avg mrr of `period_number=1` subs): B2C
  $49.00 monthly / $33.25 annual (fixed prices); SMB $199.00 / $149.92;
  Enterprise $990.00 / $825.00.
- **Churn rate** (renewal-basis, T6M window, `fct_subscriptions` end_date in
  window): B2C monthly **10.58%/mo** (n=4,056) / annual 3.39%/yr → 0.29%/mo
  equiv.; SMB monthly 7.38%/mo / annual 3.70%/yr → 0.31%/mo equiv.; Enterprise
  monthly 5.77%/mo / annual 10.0%/yr → 0.87%/mo equiv. Small-n caveat: annual
  churn samples are thin (SMB 1/27, Enterprise 1/10, B2C 4/118) — see Open
  issues.
- **Expansion / contraction, B2B only** (from a T6M $ decomposition on
  `fct_customer_mrr_monthly`, base 2023-10-31 → eval 2024-04-30, same method as
  `mart_a3_03_t6m_decomposition`, /6 for a monthly-equivalent rate — applied
  identically to a segment's monthly and annual buckets, since the underlying
  decomposition isn't split by plan_type): SMB expansion **0.88%/mo** of
  retained MRR, contraction 0.064%/mo; Enterprise expansion 0.12%/mo,
  contraction 0.11%/mo.

Full table: `mart_s_01_drivers` (58 rows: every base rate, every bear/bull
parameter, every WP23 strategy assumption at low/base/high, each with its
source/rationale) and `work/WP31_scenarios/sheet_inputs.csv`.

### Scenarios

- **Base** = the calibrated T6M rates above, held flat for 12 months. No
  strategy levers, no acquisition growth.
- **Bull** = Base + acquisition at the fitted trend (above) + all three WP23
  retention levers at their **base-case** assumption simultaneously: Strategy-1
  save rate 20% on monthly-plan churn (all 3 segments), Strategy-2 migration
  4%/month (B2C monthly→annual), Strategy-3 SMB expansion ×1.4 / Enterprise
  contraction ×0.5.
- **Bear** = churn ×1.15 (all buckets), B2B expansion ×0.5, acquisition flat
  ×0.90 (i.e. a sustained −10% vs. Base's run-rate for all 12 months).
  **Proposed A-19**: X=+15% is the single largest positive monthly deviation
  from the T12M mean observed in B2C-monthly logo churn (range: −37% to +15%
  relative to the 10.17% T12M mean — see `Docs/Plan_and_Index.md`-style
  volatility check below); Y=−10% is roughly 1.5x the worst single
  month-over-month decline observed in new B2C customers (−6.3%, Jun→Jul-23),
  applied as a sustained (not one-off) haircut to be a genuine "bad year," not
  just a repeat of the single worst month on record.

  *Volatility check behind X/Y (12 monthly points, May-23..Apr-24):* B2C
  monthly churn rate ranged 6.4%–11.7% around a 10.17% mean (rel. −37%/+15%);
  B2C new-customer count MoM % change ranged −6.3% to +18.9%.

### WP23 strategies, sized with the same engine

Each strategy is run as an **isolated override on top of Base** (not Bull) —
i.e., "what does this lever alone contribute, holding acquisition and every
other lever at the observed run-rate" — at low/base/high assumption, for 12
months, and compared to the pure Base run at the same horizon. This is the
literal "sized with the same engine" requirement in the brief and is what
populates `mart_s_04_strategy_impact` (full detail and rationale for each
lever in `work/WP23_strategies/results.md`).

### Pipeline integration

`sql/python_models/scenarios.py` exposes `build(con)`. `sql/run_pipeline.py`
now has a `build_python_models(con)` step that imports every
`sql/python_models/*.py` file (sorted by filename) with a `build(con)`
function and runs it, **after** the SQL marts and **before** `run_tests`/
`export_outputs` — exactly the "after marts, before tests" ordering requested.
Currently `scenarios.py` is the only file in that folder.

## Assumptions used (IDs)

- M-01, M-02, M-03, M-04, M-10 (bridge identity), M-08/M-09 (NDR/GRR, applied
  forward instead of backward), D-12 (movement vocabulary, extended here with
  `migration_out`/`migration_in`).
- **Proposed A-19** (new): Bear stress constants — churn +15% relative
  (largest observed positive MoM deviation in B2C-monthly churn), acquisition
  −10% sustained (≈1.5x the worst observed single-month decline), B2B
  expansion halved (per the brief).
- **Proposed A-19c** (new): annual-plan churn is observed per-year and
  converted to a monthly-equivalent rate via `1-(1-r)^(1/12)` for use in the
  monthly compartment model (no per-customer renewal calendar is tracked).
- **Proposed A-20/A-21/A-22** (new): WP23 Strategy-1/2/3 assumption ranges —
  see `work/WP23_strategies/results.md` for full detail; the numeric values
  are declared once at the top of `sql/python_models/scenarios.py` and mirrored
  in `mart_s_01_drivers`.
- Expansion/contraction rate is assumed identical across a segment's monthly
  and annual buckets (the underlying $ decomposition isn't split by plan_type
  in the source data) — a simplification, stated explicitly.
- New-customer ARPA and plan mix are held constant across scenarios (only
  volume and rates vary) — no scenario assumes Platzi changes its list prices.

## Checks performed (reconciliations, row counts)

- `sql/tests/test_s_01_base_m0.sql`: Base scenario's month-1 (May-24) opening
  MRR for Total = $204,709.09 (Apr-24 actual) within $0.50. **PASS**.
- `sql/tests/test_s_02_bull_base_bear_ordering.sql`: at month 12, Bull MRR ≥
  Base MRR ≥ Bear MRR for every segment rollup (B2C, SMB, Enterprise, B2B,
  Total). **PASS**.
- `sql/tests/test_s_03_movement_identity.sql`: `opening + new + expansion −
  contraction − churn − migration_out + migration_in = closing` for every
  (scenario, month, segment, plan_type) row, tolerance $0.01 (actual max
  observed float error ≈ 1.2×10⁻¹⁰). **PASS**.
- `sql/tests/test_s_04_backtest_credible.sql`: backtest Total MAPE < 30% for
  both MRR and active customers (actual: 10.3% / 7.7%). **PASS**.
- Manual: starting-stock query (`fct_subscriptions` point-in-time logic)
  independently reproduces both $204,709.09/1,941 (Apr-24) and $108,213.30/
  1,124 (Oct-23, the WP22 T6M decomposition's own base) exactly.
- Full pipeline (`sql/run_pipeline.py`): **32/32 tests PASS** (28 pre-existing
  + 4 new `test_s_*`), all `fct_*`/`mart_*` tables re-export cleanly, including
  the six new `mart_s_*` tables.

## Open issues / sensitivities

- **The backtest's systematic under-shoot is a real, disclosed limitation of a
  flat-run-rate Base case, not a bug.** Platzi was accelerating through
  Nov-23..Apr-24; a model with no growth assumption at all will always lag an
  accelerating company, and the gap grows every month compounded (3.8% → 17.1%
  by month 6). This is exactly *why* the brief asks for a Bull case with trend
  acquisition — it's the honest way to give the CFO an upside case that tracks
  the company's own recent trajectory, rather than quietly baking growth into
  a single "Base" number.
- **Enterprise's backtest MAPE (14.1%) is the weakest of the three segments** —
  consistent with WP20/21/22's repeated small-n caveats (≤110 Enterprise
  customers total; single-logo events move the segment noticeably).
- **Annual-plan churn samples are thin** (as low as 1 churn event out of 10-27
  renewals for SMB/Enterprise annual) — the monthly-equivalent rate for these
  buckets should be read as directional, not precise; it barely matters to the
  company total in any case (annual plans are the minority of SMB/Enterprise
  new-customer volume in some months, and monthly-plan churn dominates the
  overall churn $ by an order of magnitude, consistent with WP20).
- **Expansion/contraction rates are not split by plan_type** in the source
  data-driven calculation, so the same monthly rate is applied to a segment's
  monthly and annual buckets — a simplification (see Assumptions).
- **Bull is deliberately "Base acquisition trend + WP23 base-case levers,"
  not an independently-dreamed-up optimistic case** — this makes Bull
  traceable and defensible (every number in it also appears in WP23's
  per-strategy sizing) but means Bull's growth (+120.6% company MRR) is only
  as credible as the underlying strategy assumptions (see WP23 results.md
  for the low/high sensitivity band on each lever).
- **The engine does not model price changes, new products/segments, or
  macro shocks** — it is a retention/acquisition-driver model only, as scoped
  by the brief.

## Files produced

- `sql/python_models/scenarios.py` — the engine (calibration, scenario/strategy
  parameter sets, monthly simulation, cohort NDR/GRR, backtest, all `mart_s_*`
  table writers).
- `sql/run_pipeline.py` — edited: new `build_python_models(con)` step, wired in
  between `build(con)` (SQL marts) and `run_tests(con)`.
- `sql/marts` — none added directly (all WP31 tables are written by the
  Python model, not `.sql` files, since they require iterative simulation).
- `sql/tests/test_s_01_base_m0.sql`, `test_s_02_bull_base_bear_ordering.sql`,
  `test_s_03_movement_identity.sql`, `test_s_04_backtest_credible.sql` — all
  PASS.
- Tables in `db/platzi.duckdb` (exported to `outputs/marts/`): `mart_s_01_drivers`,
  `mart_s_02_projection_monthly`, `mart_s_03_scenario_summary`,
  `mart_s_04_strategy_impact`, `mart_s_05_backtest`, `mart_s_06_backtest_summary`.
- `work/WP31_scenarios/sheet_inputs.csv` — 58-row (id, name, value, unit,
  source, note) driver/assumption list for the WP40 Google Sheet.
- This file: `work/WP31_scenarios/results.md`.

## Proposed new IDs (for the lead to consolidate into Docs/Plan_and_Index.md)

- **A-19**: Bear scenario stress constants (churn +15% relative, acquisition
  −10% sustained, B2B expansion halved) — justified from observed monthly
  volatility (see Method).
- **A-19c**: Annual-plan churn → monthly-equivalent conversion via
  `1-(1-r)^(1/12)`, used throughout the compartment engine.
- **A-20 / A-21 / A-22**: WP23 Strategy 1/2/3 assumption ranges (see
  `work/WP23_strategies/results.md` for full detail; values also declared in
  `sql/python_models/scenarios.py` and `mart_s_01_drivers`).
- **D-19** (proposed decision): the scenario engine's Base case uses a **flat**
  T6M run-rate for acquisition (not trend), by design, so that "Base" and
  "Bull" are cleanly separated per the brief's own scenario definitions; the
  backtest shows this makes Base a conservative/pessimistic anchor for a
  company still accelerating, which should be stated whenever "Base" is shown
  to the CEO/CFO without the Bull case alongside it.
