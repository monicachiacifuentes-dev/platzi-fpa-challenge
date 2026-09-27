# WP40 -- Financial model workbook (D1)

## Answer (numbers first)

**Deliverable:** `outputs/Platzi_FPA_Model.xlsx`, built reproducibly by `work/WP40_model/build_model.py`
from `db/platzi.duckdb` (read-only) + `work/WP21_unit_economics/sheet_inputs.csv` +
`work/WP31_scenarios/sheet_inputs.csv`. Verified by evaluating every formula with the `formulas`
Python engine in `work/WP40_model/verify_model.py` (openpyxl does not calculate formulas).

**Verification: 44/46 checks passed** (see full detail below). The two failures share one root cause:
the Bull/SMB scenario cell is 3.7% away from the Python engine (target <=3%), which trips the
`Checks!B22` scenario-reconciliation check and, transitively, the master `ALL CHECKS PASS` cell. Every
other reconciliation -- Q1/Q3 totals, the MRR bridge identity, CAC/LTV/GM%/ARPA vs.
`mart_a2_12_unit_economics_summary` (all 3 segments), all 11 other scenario cells, and the
retention-adjusted-payback population check -- passes.

### Key numbers (verified via the `formulas` engine against `outputs/Platzi_FPA_Model.xlsx`)

**Unit economics (T6M CAC basis, T6M-avg GM% = 29.3%, 60-month lifetime cap):**

| Segment | ARPA (T6M avg) | GM% | CAC (T6M) | Lifetime, 60mo ($ curve) | LTV | LTV:CAC | CAC payback (mo) | **Retention-adj. payback (60mo curve)** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B2C | $42.21 | 29.3% | $392.22 | 15.9 | $196.94 | 0.50x | 31.7 | **> 60** |
| SMB | $177.94 | 29.3% | $759.41 | 42.5 | $2,215.01 | 2.92x | 14.6 | **17** |
| Enterprise | $847.75 | 29.3% | $4,249.00 | 36.9 | $9,178.81 | 2.16x | 17.1 | **21** |

All five figures per segment tie to `mart_a2_12_unit_economics_summary` within 1% (the required
tolerance) -- see the CAC/LTV rows in the verification detail below.

**Retention-adjusted payback resolves the WP40 open issue.** WP21's version was capped at the observed
survival-curve horizon (11-15 months) and therefore always said "never." Computed here on the full
extrapolated 60-month curve, B2C still never recoups its CAC (`"> 60"`) -- its $392 CAC combined with a
~10.6%/month raw churn rate on the monthly plan means cumulative gross profit per customer never
catches up -- but **SMB now resolves at month 17** and **Enterprise at month 21**, both later than
their simple CAC-payback figures (14.6 / 17.1 months) because the retention-adjusted version accounts
for the shrinking customer base as gross profit accrues, not just a flat monthly run-rate.

**Scenario summary (Apr-25, 12-month horizon from Apr-24 actuals) -- Sheet vs. Python engine:**

| Segment | Scenario | Sheet MRR Apr-25 | Engine MRR Apr-25 | Delta % | Within 3%? |
|---|---|---:|---:|---:|---|
| B2C | Base | 98,242.9 | 95,925.1 | +2.42% | Yes |
| B2C | Bull | 132,855.5 | 136,630.6 | -2.76% | Yes |
| B2C | Bear | 85,507.8 | 84,803.3 | +0.83% | Yes |
| SMB | Base | 97,998.4 | 95,519.2 | +2.60% | Yes |
| SMB | Bull | 129,626.0 | 134,630.0 | **-3.72%** | **No** |
| SMB | Bear | 85,734.9 | 84,115.8 | +1.92% | Yes |
| Enterprise | Base | 163,799.4 | 163,037.6 | +0.47% | Yes |
| Enterprise | Bull | 177,333.4 | 180,401.4 | -1.70% | Yes |
| Enterprise | Bear | 151,066.7 | 150,588.8 | +0.32% | Yes |
| **Total** | **Base** | **360,040.7** | **354,482.0** | **+1.57%** | Yes |
| **Total** | **Bull** | **439,814.9** | **451,662.0** | **-2.62%** | Yes |
| **Total** | **Bear** | **322,309.3** | **319,507.8** | **+0.88%** | Yes |

11 of 12 cells clear the 3% target, including all three **Total** rows (the headline company-level
numbers). The one miss, **SMB/Bull at -3.72%**, is explained on the Scenarios tab and below.

### Tab map

| Tab | Contents |
|---|---|
| `README` | Purpose, tab map, conventions, data window, SQL-pipeline linkage, caveats |
| `Assumptions` | Selectors (scenario, GM basis, lifetime cap), horizon dates, benchmarks, Apr-24 starting stock, survival tail parameters, scenario engine drivers (linked to the WP31 register), Bear/Bull constants, and the full WP21 (99 rows, A2-001..A2-099) and WP31 (58 rows, S-001..S-058) assumption registers |
| `Data_MRR` | `mart_mrr_bridge` verbatim (80 rows: 5 segments x 16 months) + a bridge-identity check column |
| `Data_Costs` | `stg_marketing_spend` (144 rows), `stg_support_costs` (64 rows), `mart_a2_01_new_paying_customers` (80 rows) |
| `Data_Survival` | `mart_a2_10_survival_curve` verbatim (80 rows: 5 segments x k=0..15) |
| `Answers_Q1_Q4` | Q1 (formula from Data_MRR), Q3 (formula from Assumptions starting stock), Q2/Q4 (linked data blocks from `mart_q2_retention_q1_24` / `mart_q4_ndr_t12m` -- stated as not formula-rebuilt) |
| `UnitEconomics` | G&A allocation build, monthly ARPA/GM% helper, headline CAC/GM/ARPA/LTV/LTV:CAC by segment, the 60-month survival-based lifetime curve (built on-tab), CAC payback + retention-adjusted payback, and the GM-basis x lifetime-cap sensitivity grid |
| `Scenarios` | Blended driver build, 3 parallel 12-month Base/Bull/Bear blocks x 3 segments, scenario summary, reconciliation vs. `mart_s_03_scenario_summary` |
| `Strategies` | WP23 table linked from `mart_s_04_strategy_impact` ("from engine"), plus one illustrative simple-formula cross-check |
| `Checks` | TRUE/FALSE checks + master `ALL CHECKS PASS` cell |

## Method

1. **Assumptions.** Every driver used by a downstream formula is either (a) a direct blue input (dates,
   benchmarks, tolerances, survival-curve tail rate/k_rel per segment -- Proposed **A-23**, since the SQL
   layer's cascading tail-rate selection logic is not re-derived in the Sheet), or (b) an `INDEX/MATCH`
   lookup by ID against the full WP21 (`A2-xxx`) or WP31 (`S-xxx`) register dumped further down the same
   tab. No formula anywhere in the workbook contains a hard-coded number except structural constants
   (12, 1, and the month index 0..59 / 1..12 used as row labels).
2. **Data_* tabs** are verbatim exports of named SQL marts/staging tables (blue font, "input" by the
   workbook's own convention, even though they are themselves SQL-computed -- the Sheet's job is the
   assumptions/unit-economics/scenario *calculation* layer, not re-deriving the SQL).
3. **UnitEconomics** rebuilds D-05 (G&A allocation), D-06 (CAC denominator), M-12 (gross margin) and
   M-14/M-15 (LTV, LTV:CAC, CAC payback) with `SUMIFS` over `Data_Costs`/`Data_MRR`, replicating the SQL
   marts' own logic month by month rather than looking up the finished mart values. The one exception is
   the survival-curve **tail rate itself**, which is consumed as an Assumptions input (per the WP40 spec:
   "build the 60-row monthly curve on the tab itself ... using the tail churn from Assumptions").
4. **The 60-month lifetime curve** is built as an explicit 60-row block per segment: observed dollar
   retention for k=0..k_rel (looked up from `Data_Survival`), then `curve(k) = curve(k-1) * (1-tail_decay)`
   for k>k_rel. Lifetime = the cumulative sum through k=59 (60mo cap) or k=35 (36mo cap, sensitivity).
   This reproduces `mart_a2_11_lifetime`'s `lifetime_dollar_60`/`_36` exactly (verified in Python before
   building the formulas -- see "Verification approach" below).
5. **Retention-adjusted payback** (resolves the WP40 open issue) = the first month k+1 where cumulative
   gross profit per acquired customer (`ARPA x GM% x cumulative curve`) >= CAC, evaluated over the full
   60-month curve via `SUMPRODUCT((cum_gp_range < CAC)*1) + 1`, or `"> 60"` if never reached in 60 months.
   Unlike WP21's version (limited to the observed 11-15 month horizon, which is why it always said
   "never"), this can now actually resolve to a finite month once the extrapolated tail is included.
6. **Scenarios** is a deliberately simplified single-bucket-per-segment model (not the SQL engine's six
   plan-type compartments): it blends monthly/annual rates using the Apr-24 stock mix (churn) and the T6M
   new-customer plan mix (ARPA), holds both mixes constant for 12 months, and does not model the B2C
   monthly->annual migration lever. This was validated in Python against `mart_s_03_scenario_summary`
   *before* being built as spreadsheet formulas (see "Scenario-engine simplification" below); the
   simplification was chosen specifically because it keeps every scenario cell auditable as a single
   visible formula chain, at the cost of an expected few-percent gap to the full engine.
7. **Strategies** links WP23's company-wide, low/base/high strategy table straight from
   `mart_s_04_strategy_impact` (labelled "from engine," since it is the output of the same monthly
   compartment simulation used for Scenarios) and adds one illustrative simple-formula cross-check
   (Strategy-1's save rate applied once to the concrete May-24 at-risk list).
8. **Checks** re-derives every reconciliation as a `TRUE/FALSE` formula (MRR bridge identity, Q1/Q3
   totals, CAC/LTV vs. `mart_a2_12_unit_economics_summary` within 1%, scenario reconciliation within 3%,
   retention-adjusted payback populated) and rolls them into one master cell.

### Scenario-engine simplification -- validated in Python first

Before writing any spreadsheet formula, the simplified single-bucket engine was prototyped in plain
Python against the T6M driver values from `work/WP31_scenarios/sheet_inputs.csv`, using:
- a **fixed** (not month-by-month-updated) Apr-24 stock plan-mix weight to blend monthly/annual churn,
- a **fixed** T6M new-customer plan-mix weight to blend monthly/annual new-customer ARPA,
- segment-level (not plan-type-split) expansion/contraction rates -- valid because the underlying WP31
  $ decomposition already assigns the *same* rate to a segment's monthly and annual buckets.

Result vs. `mart_s_03_scenario_summary`'s Apr-25 total company MRR:

| Scenario | Simplified-model Total MRR | Engine Total MRR | Delta % |
|---|---:|---:|---:|
| Base | 360,040.7 | 354,481.96 | +1.57% |
| Bull | 439,814.9 | 451,662.02 | -2.62% |
| Bear | 322,309.3 | 319,507.82 | +0.88% |

All three within the 3% target *before* a single spreadsheet formula was written, which is why the
Scenarios tab was built exactly this way (see `build_scenarios()` in `build_model.py`). An
update-stock-mix-every-month variant was also tested and gave a *worse* fit (Base +3.8%, Bear +4.3%),
so the simpler fixed-mix version was kept.

## Assumptions used (IDs)

M-01..M-15 (all metric definitions), D-05, D-06, D-07, D-17, D-19, A-15..A-22. **Proposed A-23 (new):**
the survival-curve tail decay/churn rate and reliable horizon k_rel, computed in SQL
(`mart_a2_11_lifetime.sql`'s cascading last3->last6->full_range fallback logic), are exposed as plain
Assumptions inputs per segment so the 60-month lifetime curve can be rebuilt with formulas on the
UnitEconomics tab, per the WP40 spec's explicit instruction to do so.

## Checks performed (reconciliations, row counts)

All in `work/WP40_model/verify_model.py`, run against `outputs/Platzi_FPA_Model.xlsx` with the
`formulas` engine (full log: `work/WP40_model/verify_output.log`). **44 of 46 assertions passed.**

| # | Check | Result |
|---|---|---|
| 1-4 | Q1 total + B2C/SMB/Enterprise MRR Apr-24 = $204,709.09 / $64,365.00 / $53,869.37 / $86,474.72 | PASS (exact, within $0.01) |
| 5 | Q3 total active subs Apr-24 = 1,941 | PASS (exact) |
| 6-7 | Q2 B2C logo retention = 89.55%; Q4 B2C NDR = 43.08%, Q4 Total NDR = 63.70% (sanity vs. linked marts) | PASS |
| 8-22 | CAC (T6M), LTV (60mo, T6M GM), LTV:CAC, ARPA (T6M avg), GM% selected -- B2C/SMB/Enterprise -- vs. `mart_a2_12_unit_economics_summary` | **PASS, all 15** (within 1% / 2% tolerance as specified) |
| 23 | MRR bridge identity (`Checks!B7`): all 80 `Data_MRR` rows satisfy opening+new+exp-contr-churn=closing | PASS |
| 24-25 | Q1/Q3 totals match the Assumptions QA targets (`Checks!B10`, `B11`) | PASS |
| 26-31 | CAC/LTV within 1% of the mart, by segment (`Checks!B14..B19`) | PASS, all 6 |
| 32-43 | Scenario reconciliation, 12 cells (3 scenarios x [B2C, SMB, Enterprise, Total]) vs. `mart_s_03_scenario_summary`, target <=3% | **11/12 PASS**; SMB/Bull FAILS at -3.72% (see explanation below) |
| 44 | `Checks!B22` (aggregate: all scenario cells within tolerance) | **FAIL** (driven entirely by the one SMB/Bull cell) |
| 45 | `Checks!B25`: retention-adjusted payback populated (a number or "> 60") for B2C/SMB/Enterprise | PASS |
| 46 | `Checks!B4` master "ALL CHECKS PASS" | **FALSE** -- see failing rows below (i.e. the sheet's own Checks tab correctly and honestly reports the one known gap rather than being rigged to always say TRUE) |

### The one gap: SMB/Bull scenario reconciliation (-3.72% vs. the 3% target)

The Scenarios tab's simplified single-bucket-per-segment engine (see Method #6) was validated in plain
Python **before** being built as formulas, and came in at -2.62% (Bull, company total) -- comfortably
under the 3% target. At the individual segment level, B2C (-2.76%) and Enterprise (-1.70%) also clear
3%, but **SMB/Bull lands at -3.72%**, because SMB's Bull case is the only one where three compounding
levers apply simultaneously to the same (small, ~303-customer) base: the acquisition trend, the
Strategy-1 churn save-rate, and the Strategy-3 SMB expansion uplift (x1.4). Two alternative
refinements were tested in Python before accepting this gap: (a) continuing the acquisition trend line
past month 6 of the calibration window instead of restarting it at month 1 (made the fit *worse* --
Bull overshoots the engine by 3-15% depending on the offset tried), and (b) applying expansion to
*retained* MRR (opening minus churn) instead of gross opening MRR (also made SMB/Bull's fit marginally
*worse*, -3.92% instead of -3.72%). Neither is an improvement, so the simpler, already-validated
formula was kept. This is a genuine, disclosed limitation of a single-bucket simplification asked to
carry three compounding levers for one segment at once -- not a formula bug -- and is exactly the kind
of gap the spec anticipates ("a simplified formula model won't match exactly ... show ... a one-line
explanation of any gap"). It is stated on the Scenarios tab next to the reconciliation block.

## Open issues / sensitivities

- **`formulas` (the Python verification engine) is slow on this workbook** (multi-minute full
  recalculation, given ~6,700 formula cells including a 60-row x 3-segment lifetime curve and three
  12-month x 3-segment scenario chains). This is a verification-tooling limitation, not a workbook
  correctness issue -- Excel and Google Sheets recalculate the same workbook in under a second.
- **The Scenarios tab is a deliberately simplified model** (see Method #6); it is reconciled to the full
  Python engine within the 3% target on Apr-25 total MRR per scenario, not exactly matched. The gap is
  explained on the Scenarios tab itself next to the reconciliation block.
- **Q2 and Q4 link to small SQL mart exports rather than being rebuilt as formulas** (stated on the
  Answers_Q1_Q4 tab) -- their definitions (M-06 renewal-event retention; M-08/M-09/M-10 NDR/GRR) need
  row-level subscription-period data and a customer-level cohort join that would require pasting the
  full `fct_subscriptions`/`fct_customer_mrr_monthly` tables (thousands of rows) into the workbook,
  which was judged out of scope for a Google-Sheets-friendly model.
- **GM% is uniform across segments by construction** under the base allocation (all COGS by MRR share) --
  this is a genuine WP21 finding (`test_a2_gm_base_uniform`), not a workbook bug; it means the headline
  LTV:CAC story is driven entirely by ARPA, CAC and the retention curve, not by a GM% difference.
  Restated explicitly on the UnitEconomics tab.
- **Enterprise and SMB unit-economics figures rest on small samples** (as few as 58 new customers/6mo
  for Enterprise T6M) -- carried over from WP20/21/22/31's repeated caveat.
- **The Strategies tab's company-wide 6/12-month deltas are "from engine"**, not spreadsheet formulas --
  the underlying monthly compartment simulation with isolated-lever overrides is not re-derived as
  spreadsheet formulas (same simplification boundary as the Scenarios tab).

## Files produced

- `outputs/Platzi_FPA_Model.xlsx` -- the deliverable.
- `work/WP40_model/build_model.py` -- reproducible build script (reads `db/platzi.duckdb` read-only +
  the two WP21/WP31 `sheet_inputs.csv` files; writes the workbook). Rerun with
  `.venv/Scripts/python.exe work/WP40_model/build_model.py`.
- `work/WP40_model/verify_model.py` -- formula-engine verification script. Rerun with
  `.venv/Scripts/python.exe work/WP40_model/verify_model.py` (takes several minutes; see Open issues).
- `work/WP40_model/verify_output.log` -- full verification run output.
- This file: `work/WP40_model/results.md`.

## Google Sheets upload instructions

1. Go to Google Drive -> **New -> File upload** -> select `outputs/Platzi_FPA_Model.xlsx`.
2. If Drive's Settings has **"Convert uploads"** turned on, the file opens directly as a Google Sheet --
   done.
3. If not (or if you want to keep the original .xlsx untouched), open the uploaded file with Google
   Sheets (double-click -> "Open with Google Sheets" if prompted, or right-click -> Open with -> Google
   Sheets), then **File -> Save as Google Sheets** to create a native, editable copy.
4. All formulas in this workbook use only `SUM, SUMIFS, SUMPRODUCT, INDEX/MATCH, IF, MIN/MAX, ROUND,
   AVERAGE, COUNTIFS, IFERROR` plus basic arithmetic and `AND/OR` -- no macros, no Excel data tables, no
   structured table references, no dynamic-array-only functions, no external links -- so every formula
   recalculates identically in Google Sheets. Data-validation dropdowns (the scenario and GM-basis
   selectors on the Assumptions tab) also carry over natively.
5. Conditional formatting on the Checks tab (green/red PASS/FAIL highlighting) also carries over.

## Proposed new IDs

- **A-23** (new): the survival-curve tail decay rate and reliable horizon (k_rel) per segment, computed
  in SQL by `mart_a2_11_lifetime.sql`'s cascading fallback logic (A-15/A-16/A-17), are exposed as plain
  Assumptions-tab inputs so the Google Sheet can rebuild the 60-month lifetime curve (and, on top of it,
  the retention-adjusted payback) with visible formulas rather than re-deriving the fallback-selection
  logic itself in the spreadsheet.
