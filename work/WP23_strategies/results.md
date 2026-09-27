# WP23 — Analysis 4: Retention Strategy Recommendations

*Written for the CEO/CFO. All figures below come from the same scenario engine
built for WP31 (bonus), so they are directly comparable to the Base/Bull/Bear
projection. Full engine detail: `work/WP31_scenarios/results.md`. Full numeric
table: `mart_s_04_strategy_impact`.*

## Answer (numbers first)

**Bottom line: do Strategy 1 immediately (cheapest, fastest, biggest single
lever), run Strategy 3 in parallel (steady B2B upside, no downside), and treat
Strategy 2 as a longer-horizon bet that costs MRR for ~9 months before it pays
back.**

| Strategy | 6-mo MRR impact ($) | 6-mo MRR impact (%) | 12-mo MRR impact ($) | NDR impact, 6-mo (pp) | Effort | Time to impact |
|---|---:|---:|---:|---:|---|---|
| **1. Engagement alert + save play** | **+$7,690** | **+2.71%** | +$13,783 | **+2.69 pp** | Low | 1 month |
| **3. B2B expansion/contraction playbook** | +$1,559 | +0.55% | +$3,529 | +0.61 pp | Medium | 3 months |
| **2. B2C monthly→annual migration** | **−$850** | **−0.30%** | +$1,529 | −0.18 pp (M6) / **+0.80 pp (M12)** | Medium | 6–9 months to breakeven |

(Company-wide, "base case" assumption for each strategy; low/high sensitivity
bands are in the detail tables below. All three are modeled as **isolated
levers on top of the Base scenario** — i.e., "what does this one initiative
add, holding everything else at the current run-rate.")

## Effort x impact

| | Low effort | Medium effort |
|---|---|---|
| **High 6-mo impact** | **Strategy 1** (do first) | — |
| **Positive, no downside** | — | **Strategy 3** (do in parallel) |
| **Net-negative at 6mo, positive by ~M9–M12** | — | Strategy 2 (sequence 3rd, or run alongside once cash-flow headroom exists) |

**Recommended sequence:** 1) Engagement alert (Strategy 1) — ship this month,
it is a rules-based trigger, not a model, and pays back immediately. 2) B2B
playbook (Strategy 3) — stand up the SMB QBR/seat-expansion motion and the
Enterprise 2nd-renewal save motion in parallel; no MRR downside, just needs
CSM/AM time. 3) Annual migration offer (Strategy 2) — launch once 1 and 3 are
funding the retention program, since it **reduces MRR before it helps it**;
don't launch it as the first or only initiative.

---

## Strategy 1 — In-period low-engagement alert + save play

**Mechanism**: WP20 showed churn is driven almost entirely by in-period usage
(courses_seen ≤ 3 or materials_seen ≤ 10 → churn jumps from ~0% to 50–72%),
and this signal is available **mid-period**, before the renewal date (D-18).
Flag these subs by day 10–15 of the billing cycle and intervene: automated
in-app nudges/content for B2C, a CSM call for B2B. **Target**: the May-24
High+Medium risk list is the concrete starting point — 100 subs, $5,494 MRR,
$3,812 of it expected to churn (`mart_a1_06_may24_churn_risk`) — then the same
rule runs every month going forward.
**Lever**: the save rate on flagged would-be churners. We use the industry-
typical 10–30% range (low/base/high); at the base 20% save rate, applying it
*only* to the May-24 list already saves ≈$762/month of MRR immediately;
running it every month is the $7,690/6mo, $13,783/12mo, +2.7pp NDR company
number above.

| Case | Save rate | 6-mo MRR Δ | 6-mo MRR Δ% | 12-mo MRR Δ | NDR Δ (M6/M12, pp) |
|---|---:|---:|---:|---:|---|
| Low | 10% | +$3,763 | +1.33% | +$6,608 | +1.3 / +1.6 |
| **Base** | **20%** | **+$7,690** | **+2.71%** | **+$13,783** | **+2.7 / +3.3** |
| High | 30% | +$11,787 | +4.16% | +$21,579 | +4.1 / +5.2 |

By segment (base case, 6-mo): B2C +$4,603 (biggest, since B2C is 70/72 of the
May-24 High tier), SMB +$2,210, Enterprise +$877.

**Effort**: Low — a rule (not a model) on data already in the warehouse; no
new data collection. **Time to impact**: 1 month (first flagged cohort).
**KPIs**: # flagged/month, realized save rate vs. assumed, churn rate of
flagged vs. unflagged. **Risks**: WP20's AUC (0.9997) is a simulated-data
artifact — expect real-world precision closer to 70–85% AUC; some outreach
will be wasted on customers who'd have stayed anyway (false positives), and
some flagged customers won't be saveable regardless of outreach.

---

## Strategy 2 — B2C monthly → annual migration offer

**Mechanism**: no customer ever switches plans today (verified data fact).
B2C annual customers pay **less per month** ($33.25 vs. $49) but churn at
**~0.3%/month-equivalent vs. ~10.6%/month** for monthly — a much stickier
customer once converted. **Target**: the 844 current B2C-monthly subscribers
(and the ongoing monthly base thereafter). **Lever**: the % of the monthly
base that accepts an annual offer each month (2/4/6% low/base/high — no
direct take-up data, stated as a range).
**⚠️ Honest trade-off**: converting a customer immediately *cuts* their MRR
by $15.75/month, so this strategy is **net-negative on MRR for about 9
months**, then turns positive as the churn reduction compounds.

| Case | Conversion rate | 6-mo MRR Δ | 6-mo MRR Δ% | 12-mo MRR Δ | 12-mo MRR Δ% | Breakeven month | NDR Δ M6 / M12 (pp) |
|---|---:|---:|---:|---:|---:|---:|---|
| Low | 2%/mo | −$456 | −0.56% | +$755 | +0.79% | ~M9 | −0.33 / +1.30 |
| **Base** | **4%/mo** | **−$850** | **−1.04%** | **+$1,529** | **+1.59%** | **~M9** | **−0.58 / +2.56** |
| High | 6%/mo | −$1,187 | −1.45% | +$2,309 | +2.41% | ~M9 | −0.77 / +3.77 |

**Side benefit — cash upfront**: an annual sale collects $399 in one payment
instead of $49/month spread over the year. At the base conversion rate, ≈181
customers convert in the first 6 months → **≈$72,000 of cash collected
upfront** in those 6 months alone (illustrative, gross; not netted against
the monthly cash that would otherwise have arrived anyway) — a genuine
working-capital benefit even during the MRR-dip period.
**Effort**: Medium — needs an in-app/email offer flow and (ideally) a modest
discount to justify prepaying; no new infra. **Time to impact**: 6 months to
see the trade-off, ~9 months to net-positive MRR. **KPIs**: conversion rate,
blended B2C ARPA, cash collected, annual-cohort churn vs. the 0.3%/mo
benchmark. **Risks**: cannibalizes revenue from customers who would have
stayed on monthly anyway without ever churning (the model assumes the
churn-rate benefit applies to *all* converts, which is optimistic); refund/
chargeback risk on a prepaid annual plan is higher than on monthly.

---

## Strategy 3 — B2B expansion & contraction-prevention playbook

**Mechanism**: WP22 found SMB drives 4x Enterprise's expansion $ (a broad
seat-growth pattern, 129 events) and its contraction risk peaks at the
5th–8th renewal; Enterprise's contraction risk peaks at the 2nd renewal (an
early "is this delivering value" moment) but Enterprise expansion is rare
and logo-concentrated. **Target**: SMB accounts approaching their 5th–8th
renewal (QBR / seat-expansion motion) and Enterprise accounts approaching
their 2nd renewal (a save-focused QBR). **Levers**: uplift to SMB's observed
monthly expansion rate (+20/40/60% low/base/high) and reduction to
Enterprise's observed monthly contraction rate (−30/50/70%).

| Case | SMB expansion uplift | Ent. contraction reduction | 6-mo MRR Δ (B2B) | 6-mo MRR Δ% | 12-mo MRR Δ | NDR Δ M6/M12 (pp, B2B) |
|---|---:|---:|---:|---:|---:|---|
| Low | +20% | −30% | +$810 | +0.40% | +$1,829 | +0.46 / +0.84 |
| **Base** | **+40%** | **−50%** | **+$1,559** | **+0.77%** | **+$3,529** | **+0.89 / +1.62** |
| High | +60% | −70% | +$2,313 | +1.15% | +$5,253 | +1.32 / +2.41 |

Split (base case, 6-mo): SMB +$1,228, Enterprise +$332 — SMB is the larger
lever because it starts from a much broader expansion base (129 events/year
vs. Enterprise's 8).
**Effort**: Medium — requires CSM/AM headcount time to run structured QBRs at
the right renewal milestones; no new tooling beyond a renewal-milestone
report (buildable from `fct_subscriptions.period_number`). **Time to
impact**: ~3 months (first cohort reaching the milestone after rollout).
**KPIs**: SMB seats/account, SMB expansion $ (vs. WP22's $3,917/yr baseline),
Enterprise 2nd-renewal retention rate. **Risks**: Enterprise's small base
(~100 customers) means realized results can differ a lot from the point
estimate (WP20/22's repeated small-n caveat); requires dedicated CSM/AM
capacity that competes with other priorities.

---

## Note — capital allocation (not a retention strategy, out of this WP's scope)

WP21 found B2C fails LTV:CAC under every gross-margin allocation (0.50x /
−0.63x) while SMB sits near the 3x benchmark (2.92x) and is the segment where
a modest cost-accounting change (customer-weighted GM) would clearly clear it
(4.88x). **A worthwhile follow-up (not modeled here) is shifting a slice of
B2C paid-acquisition budget toward SMB** — it doesn't change retention, so it
sits outside this WP's brief, but it directly complements Strategy 3 (a
bigger, better-retained SMB base compounds the playbook's expansion lever).

## Method

All three strategies were sized by taking `sql/python_models/scenarios.py`'s
Base driver calibration (T6M, ending 2024-04-30) and overriding **only** the
named lever(s) for that strategy — leaving acquisition, plan mix, ARPA and
every other rate at their observed Base value — then running the identical
12-month monthly compartment simulation and forward-cohort NDR/GRR calculation
used in WP31, and differencing against the pure Base run at the same month.
This guarantees strategy impacts are computed the same way the Base/Bull/Bear
scenarios are, and that Bull (WP31) is literally "all three strategies' base
case, run together" — traceable, not a separate optimistic guess.
Strategy-1's "concrete May-24 list" figure ($3,812 at-risk MRR) is read
directly off `mart_a1_06_may24_churn_risk` / WP20's tier x segment summary.
Strategy-2's cash-upfront figure sums `migration_out_customers` from the
simulation's monthly panel over months 1–6, x $399 (one annual payment).

## Assumptions used (IDs)

D-16 (May-24 risk tiers), D-18 (in-period engagement framing). **Proposed
A-20** (Strategy-1 save rate 10/20/30%), **A-21** (Strategy-2 conversion rate
2/4/6%/month), **A-22** (Strategy-3 SMB expansion uplift 20/40/60% and
Enterprise contraction reduction 30/50/70%) — full rationale and the engine
constants are declared in `sql/python_models/scenarios.py` and
`work/WP31_scenarios/results.md` (same IDs, not duplicated).

## Checks performed (reconciliations, row counts)

- All three strategies reuse WP31's engine and its 4 passing tests (base m0
  tie-out, bull≥base≥bear ordering, movement identity, backtest credibility) —
  see `work/WP31_scenarios/results.md`.
- Cross-check: Strategy-1's base-case save rate (20%) applied only to the
  May-24 High+Medium list ($3,812 expected churned MRR) gives ≈$762/month —
  independently consistent with the engine's company-wide $7,690/6-month
  figure once you account for the engine compounding the save rate across
  *every* month's flagged cohort, not just May-24's.
- `mart_s_04_strategy_impact`: 30 rows (3 strategies x 3 cases x affected
  segments incl. Total), all numeric, no nulls in the delta columns.

## Open issues / sensitivities

- **Strategy 2's short-term MRR hit is real and should be presented to the
  CFO as such** — it is the one initiative of the three where "impact on
  MRR" is negative before it's positive; don't lead with the 12-month number
  alone.
- **Strategy 1's headline numbers inherit WP20's caveat**: production save
  rates and precision will likely be lower than the in-sample model suggests,
  because the underlying churn signal is partly a simulated-data artifact
  (see WP20's reviewer note). The 10–30% save-rate range is deliberately an
  external, industry-typical benchmark rather than derived from this dataset,
  to avoid compounding that artifact into the ROI estimate.
- **Strategy 3's Enterprise leg is small-n** (~100 customers historically) —
  treat the Enterprise contraction-reduction dollars as directional, not a
  committed number.
- **None of the three strategies were tested for interaction effects** beyond
  Bull's "all three at base case" run in WP31 — e.g., a customer both flagged
  by Strategy 1 and offered the Strategy 2 migration is treated independently
  in each isolated run; in reality outreach capacity may need to be
  prioritized across overlapping target lists (the May-24 High/Medium list is
  almost entirely B2C-monthly, i.e., the same population Strategy 2 targets).
- **Capital-allocation note is explicitly out of scope** for this WP (retention
  only, per the brief) and is not sized with the engine — flagged only as a
  pointer for the CFO.

## Files produced

- Reuses `sql/python_models/scenarios.py`, `mart_s_04_strategy_impact` (and
  `mart_s_01..03/05/06`) — no new SQL/Python files; all WP23 numbers are a
  query/aggregation of WP31's outputs.
- `work/WP31_scenarios/sheet_inputs.csv` — includes the Strategy 1/2/3
  assumption rows (ids referencing `strategy_1_engagement_alert` /
  `strategy_2_annual_migration` / `strategy_3_b2b_playbook` in the `name`
  column) for the WP40 Google Sheet.
- This file: `work/WP23_strategies/results.md`.

## Proposed new IDs (mirrors WP31; not duplicated in Docs/Plan_and_Index.md by this agent — lead consolidates)

- **A-20**: Strategy-1 (engagement alert) save-rate assumption, 10/20/30%.
- **A-21**: Strategy-2 (annual migration) conversion-rate assumption, 2/4/6%/month.
- **A-22**: Strategy-3 (B2B playbook) SMB expansion uplift (20/40/60%) and
  Enterprise contraction reduction (30/50/70%) assumptions.
- **D-19** (proposed, shared with WP31): scenario Base case uses flat T6M
  acquisition by design; strategies are sized as isolated levers on top of
  Base, and Bull = Base-trend-acquisition + all three strategies' base case
  combined — this chain (strategy → Bull → scenario summary) should be kept
  intact if any strategy assumption is revised later.
