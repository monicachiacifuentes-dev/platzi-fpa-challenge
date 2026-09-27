# WP20 — A1: Cohort Analysis & Churn Risk

## Answer (numbers first)

### 1. Cohort retention matrix (signup-month cohorts, M-11)

Full long-format mart: `mart_a1_01_cohort_retention` (408 rows: 16 cohorts × up to 16 ages ×
3 segment groups). Wide pivots for readability: `cohort_pivot_{logo,dollar}_{Total,B2C,B2B}.csv`.
Heatmaps: `cohort_heatmap_total.png` (Total, logo + $), `cohort_heatmap_b2c_b2b.png` (B2C vs B2B logo).

Headline read (Total, logo retention across the 15/13/10/4 cohorts old enough to reach that
age): M1 ranges 91–98%, M3 ranges 80–87%, M6 ranges 66–78%, M12 (only the 4 oldest cohorts)
ranges 50–54%. B2C decays faster than B2B — e.g. at M6, B2C logo retention ranges 64–75%
vs. B2B 71–93% depending on cohort. $ retention (includes B2B expansion) is consistently a
few points above logo retention for B2B, and can briefly exceed 100% when expansion outpaces
churn (peak observed: the 2023-08 B2B cohort at M1, 102.8%) before settling into decay as
more of the cohort eventually churns.

### 2. Highest churn-risk cohorts

Benchmark = size-weighted average retention across all cohorts that have reached the same
age (month_k), by segment_group. Flag = cohort ≥10pp below that age's benchmark **and** ≥20
starting customers (avoids flagging noise in tiny cohorts). Only **3 cohort/age/segment
combinations** clear this bar (`cohort_risk_flags_significant.csv`):

| Cohort | Segment | Age | Metric | Value | Benchmark | Gap |
|---|---|---:|---|---:|---:|---:|
| 2023-11 | B2B | M3 | Logo | 78.8% | 90.0% | **−11.2pp** |
| 2023-02 | Total (blended) | M3 | $ | 74.1% | 86.9% | **−12.8pp** |
| 2023-02 | Total (blended) | M6 | $ | 65.3% | 77.3% | **−12.0pp** |

**Why:**
- **B2B Nov-2023 (33 customers)**: first-period engagement at signup was in line with the
  B2B baseline (annual sub-cohort avg active_days 16.7 vs. company B2B-annual baseline 16.8;
  monthly sub-cohort 15.1 vs. baseline 16.8 — a mild but not dramatic gap) and plan mix
  (55% annual / 45% monthly) is close to the overall B2B mix (60%/40%). This cohort's flag is
  mostly a **small-sample effect** (33 logos; losing 4 extra renewals moves the rate by
  >10pp) rather than a clear composition or engagement story — monitor, don't over-react.
- **Total 2023-02 ($ retention)**: this is **concentration risk, not engagement risk**. The
  cohort has only 102 customers, of which just **2 are Enterprise** ($990 and $825 MRR).
  One of those two Enterprise accounts (`U01201`, $990 MRR) churned by month 6, which alone
  erased ~12% of the cohort's starting MRR (`cohort_2023_02_concentration.csv`). A blended
  ("Total") cohort $ metric is fragile whenever it happens to contain very few, very large
  B2B logos — losing one swings the whole cohort's dollar retention by double digits even
  though nothing else in the cohort behaved unusually.
- **No B2C cohort clears the bar.** The largest apparent B2C gaps (e.g. Dec-2023, Jul-2023,
  ~3–4pp below benchmark) are within ~1–1.5 standard errors of sampling noise for a cohort of
  100–160 customers churning at the ~10%/period B2C base rate — not a real signal, just
  normal cohort-to-cohort variance.

### 3. Leading indicators + logistic regression (doubles as bonus WP32)

Churn rate by bucket, whole population with a known outcome (n=7,742: 6,988 renewed + 754
churned), `mart_a1_04_churn_rate_by_bucket.csv`. The engagement fields dominate everything
else by an order of magnitude:

| Dimension | Highest-churn bucket | Rate | Lowest-churn bucket | Rate |
|---|---|---:|---|---:|
| active_days | 0–5 | **50.8%** | 16–28 | 0.0% |
| courses_seen | 0–2 | **48.5%** | 6+ | 0.0% |
| materials_seen | 0–9 | **72.2%** | 20+ | 0.0% |
| plan_type | monthly | 9.9% | annual | 3.9% |
| segment | B2C | 10.1% | SMB | 6.9% |
| tenure (periods) | 2 | 11.3% | 1 | 8.0% |
| renewal change (contraction/etc.) | flat | 10.4% | expansion | 5.2% |
| main_gateway | Stripe | 10.6% | PayPal | 8.7% |
| favorite_category | Cloud Computing | 11.9% | English | 7.6% |

Engagement buckets show near-total separation (0% churn once active_days > 15, courses_seen
> 5, or materials_seen > 19); plan/segment/tenure/gateway/category differences are all within
~3–5pp of each other — noise-level next to engagement.

**Model**: logistic regression, standardized numeric features (`active_days`, `courses_seen`,
`materials_seen`, `period_number`), dummy-encoded `plan_type` (baseline monthly),
`customer_type` collapsed to B2C/B2B (baseline B2C), the previous-renewal `mrr_delta`
sign (baseline "flat"), and `main_gateway` (baseline Stripe) — 13 features. Time-based split:
train = periods ending before 2024-01-01 (n=4,318, 9.77% churn), test = ending
2024-01-01…2024-04-30 (n=3,424, 9.70% churn).

| Model | AUC (test) | Precision @0.50 | Recall @0.50 | F1 @0.50 |
|---|---:|---:|---:|---:|
| **class_weight='balanced' (chosen)** | **0.9997** | 86.2% | **100.0%** | 92.6% |
| unweighted (sensitivity) | 0.9997 | 94.5% | 98.8% | 96.6% |

Confusion matrix (balanced, threshold 0.50): TN 3,039 / FP 53 / FN 0 / TP 332 — every churner
in the test set is caught, at the cost of 53 false alarms (out of 3,424 test periods).
**Justification for `balanced`**: the business use-case is a retention early-warning list
(WP20 §4 / WP23), where missing an at-risk customer costs more than one unnecessary outreach
call, and the base rate is skewed (~9.7% churned) — balanced weights trade some precision for
zero missed churners. AUC is essentially identical either way (engagement alone almost
perfectly separates the classes), so this choice mainly moves the precision/recall trade-off,
not overall discrimination.

**Coefficients / odds ratios** (balanced model, standardized features — one full standard
deviation of the raw metric): `churn_model_coefficients.csv`.

| Feature | Coefficient | Odds ratio | Plain language |
|---|---:|---:|---|
| materials_seen (z) | −7.44 | 0.00059 | +1 SD materials seen → ~99.94% lower odds of churn |
| courses_seen (z) | −4.65 | 0.0096 | +1 SD courses seen → ~99% lower odds |
| active_days (z) | −2.02 | 0.133 | +1 SD active days → ~87% lower odds |
| is_b2b | +1.34 | 3.83 | B2B (net of engagement) → ~3.8× higher odds — small-n effect, see caveat |
| gw_payoneer | −0.58 | 0.56 | Payoneer payers → ~44% lower odds vs. Stripe |
| rc_no_prior_renewal | −0.32 | 0.73 | First-ever period → ~27% lower odds than a flat renewal |
| gw_paypal | +0.27 | 1.31 | PayPal payers → ~31% higher odds vs. Stripe |
| period_number (z) | +0.21 | 1.24 | +1 SD tenure → ~24% higher odds (weak) |
| plan_annual | 0.00 | 1.00 | No independent effect once engagement is controlled for |

**Bottom line: engagement (materials/courses/active days) explains almost all of the
predictable churn variance.** Plan type, gateway, category and tenure add only marginal,
mostly non-actionable signal once engagement is in the model.

### 4. May-2024 at-risk list (D-08 population)

Population: `mart_a1_05_may24_population` — subscriptions `status='active'`, `end_date` in
2024-05 → **1,024 subscriptions, $87,828.88 MRR** (matches the independent count exactly).
Scored in `mart_a1_06_may24_churn_risk` (SQL, hardcoded trained coefficients) and
`may24_churn_risk_list.csv` (+ plain-language main driver). Tiers: **High ≥50%, Medium
25–50%, Low <25%** (Proposed D-16, see below).

| Tier | n subs | MRR | Expected churned MRR (Σ p·mrr) | Avg p(churn) |
|---|---:|---:|---:|---:|
| **High** | 72 | $3,747.42 | **$3,143.99** | 83.9% |
| **Medium** | 28 | $1,747.19 | $668.37 | 37.9% |
| **Low** | 924 | $82,334.27 | $492.13 | 1.0% |
| **Total** | **1,024** | **$87,828.88** | **$4,304.48 (4.9% of pop. MRR)** | — |

By tier × segment (`may24_risk_summary_tier_segment.csv`):

| Tier | Segment | n | MRR | Expected churned MRR |
|---|---|---:|---:|---:|
| High | B2C | 70 | $3,398.50 | $2,846.72 |
| High | SMB | 2 | $348.92 | $297.27 |
| Medium | B2C | 26 | $1,274.00 | $482.36 |
| Medium | SMB | 2 | $473.19 | $186.01 |
| Low | B2C | 783 | $37,847.25 | $404.40 |
| Low | SMB | 122 | $26,402.29 | $86.57 |
| Low | Enterprise | 19 | $18,084.73 | $1.16 |

Main driver (per subscription, largest single logit contribution — `may24_churn_risk_list.csv`):
**"Few materials/lessons viewed" and "Few courses viewed" account for all 100 of the 100
High+Medium tier flags** (85 materials, 15 courses). No other feature (segment, gateway,
tenure, contraction) is ever the top driver at High/Medium risk. Practically: **the May-24
at-risk list is, in plain terms, "customers who barely used the product last period."**

**Engagement-truncation check** (`engagement_truncation_check.png/csv`): a real concern for
any in-progress period is that its `active_days` should be partial/incomplete. We compared
`active_days` for currently **active** monthly periods, split by days elapsed since
`start_date` as of the snapshot (2024-04-30), against **completed & renewed** monthly periods:

| Bucket | n | Avg active_days |
|---|---:|---:|
| Active, <10 days elapsed | 327 | 13.4 |
| Active, 10–20 days elapsed | 312 | 14.3 |
| Active, 20+ days elapsed | 330 | 13.2 |
| Completed & renewed (full period) | 6,839 | 14.8 |

**Finding: `active_days` is NOT truncated.** A period only 5–9 days old already shows the
same average `active_days` (13.4) as a period 20+ days in (13.2) or a fully completed period
(14.8) — and separately, 494 of 1,941 active periods (25.5%) already show more `active_days`
than calendar days have elapsed since `start_date`, which is only possible if the field
already reflects an assumed **full-period** value rather than activity accumulated so far.
**No truncation adjustment was applied**; this is stated as a caveat/assumption below because
in a live system this field would need to be treated as partial and either excluded or
re-based to a rate (active_days ÷ days elapsed) for in-progress periods.

## Method

- All work built in an isolated `work/WP20_cohorts_churn/dev.duckdb` (copied from the shared
  `db/platzi.duckdb`, never written back); `dev_build.py` rebuilds it and runs the WP20 tests
  end to end.
- **mart_a1_01_cohort_retention**: `fct_customer_mrr_monthly` (user × month-end MRR grid,
  M-02) joined to `stg_users.signup_date` → `cohort_month` = signup month, `month_k` = months
  between month-end and cohort month. Segment groups Total/B2C/B2B via `UNION ALL`.
  `customers_start`/`mrr_start` = the cohort's own month_k=0 row (always 100% by construction
  — every user's first subscription starts on `signup_date`, a verified data fact).
- **mart_a1_02_cohort_risk_flags**: window-function benchmark (Σcustomers_active/Σcustomers_start,
  Σmrr_active/Σmrr_start) across all cohorts sharing an age, for ages 1/3/6 (M1/M3/M6 per the
  brief); flags cohorts ≥10pp below with ≥20 starting customers.
- **mart_a1_03_churn_indicators_base**: `fct_subscriptions` filtered to `status IN
  ('renewed','churned')` (known outcome only — `active` periods are excluded, they have no
  outcome yet), with bucketed columns for the descriptive cuts and a `model_split` column
  (train = `end_date` < 2024-01-01, test = 2024-01-01..2024-04-30, per the brief).
- **mart_a1_04_churn_rate_by_bucket**: `UNION ALL` of 8 `GROUP BY` blocks on mart_a1_03, one
  per requested dimension, long format for a Looker Studio grid.
- **Model** (`churn_model.py`): `sklearn.LogisticRegression`, features standardized
  (`StandardScaler` fit on train only) for the 4 continuous columns; categoricals one-hot
  with an explicit baseline (dropped) category. Two fits (`class_weight='balanced'` and
  unweighted) for comparison; balanced is the reported/chosen model (justification above).
  The script then **auto-generates** `sql/marts/mart_a1_06_may24_churn_risk.sql`: it bakes
  the trained intercept, coefficients, and the train-set scaler mean/std as literal SQL
  constants, so scoring `mart_a1_05_may24_population` is a plain linear combination + a
  manual `1/(1+EXP(-logit))` sigmoid — a pure, portable SELECT with no ML runtime dependency
  (verified to match the Python model's own predictions to ~1e-11, see Checks).
- **mart_a1_05_may24_population**: `fct_subscriptions` filtered to `status='active'` and
  `end_date` in 2024-05 (D-08).
- **cohort_analysis.py**: builds the wide CSV pivots, PNG heatmaps, the cohort-risk "why"
  digging queries, the engagement-truncation check, the ROC plot, and the final May-24 CSV
  (joins mart_a1_06's per-feature `contrib_*` columns to label each row's single largest
  driver in plain language, direction-aware for the 3 continuous engagement features + tenure
  since the same column can be either the top risk-*increasing* or risk-*reducing* factor
  depending on whether that customer sits above or below the training average).

## Assumptions used (IDs)

- M-01, M-02, M-04 (segment/B2B roll-up), M-11 (cohort definition), D-08 (May-2024 at-risk
  population), D-13 (main_gateway), D-14 (next_status, unused directly but underlies `status`).
- **Proposed A-06** (new): the logistic regression collapses `segment` to `customer_type`
  (B2C/B2B) and excludes `favorite_category` (12 levels) as model features, to keep the model
  "simple and explainable" per the brief — both are still shown as descriptive cuts in
  `mart_a1_04`. Rationale: neither showed material discriminative power once engagement was
  accounted for (segment churn rates span only 6.9–10.1%, category 7.6–11.9%, vs. engagement's
  0%–72% range).
- **Proposed A-05** (new): cohort risk-flag rule = ≥10 percentage points below the
  size-weighted age benchmark **and** ≥20 starting customers. Chosen to separate real signal
  from small-cohort noise; sensitivity — with no minimum size, several more <20-customer
  cohorts would also flag (not reported, judged unreliable).
- **Proposed D-16** (new): May-24 risk tiers = High ≥50% churn probability, Medium 25–49%,
  Low <25%. Matches the model's own natural break (precision 86%/recall 100% at 0.50 on the
  test set) and gives WP23 a stable convention to reference.
- A `main_gateway = NULL` row (28 of 1,024 May-24 rows — no payment posted yet on an
  in-progress period) is scored as if it were the baseline (Stripe) gateway, since the
  training population had zero such rows (main_gateway is never NULL for a completed period)
  — the model never learned an "unknown gateway" effect. Immaterial to the tier outcome in
  practice (gateway's largest odds-ratio effect is ±44%, dwarfed by the engagement terms).

## Checks performed (reconciliations, row counts)

- `test_a1_01_cohort_retention`: month_k=0 logo/dollar retention = exactly 1.0 for every
  cohort/segment_group, and customers_start/mrr_start > 0. **PASS**.
- `test_a1_01b_cohort_total_reconciles`: Total = B2C + B2B on customers_active and mrr_active
  for every (cohort_month, month_k). **PASS**.
- `test_a1_03_churn_indicators_base`: row count = 7,742 (6,988 renewed + 754 churned per
  `Docs/Datasets.md`); `churned` flag matches `status` exactly; no row falls outside
  train/test (`model_split <> 'other'`). **PASS**.
- `test_a1_05_may24_population`: row count = 1,024 and MRR = $87,828.88, cross-checked
  independently via a direct DuckDB query before the mart was written. **PASS**.
- `test_a1_06_churn_risk_scores`: row count matches mart_a1_05 1:1; `prob_churn` in [0,1];
  `risk_tier` matches the stated cutoffs exactly; `mrr_at_risk` = `mrr × prob_churn` (±0.01).
  **PASS**.
- Independent cross-check: the SQL-computed `prob_churn` in `mart_a1_06` matches the Python
  model's own `predict_proba` on the same population to a max absolute difference of
  **3.7×10⁻¹¹** (`may24_scores_python_crosscheck.csv` vs. the mart) — confirms the
  hardcoded-coefficient SQL formula exactly reproduces the trained model.
- `dev_build.py` rebuilds `dev.duckdb` from a **fresh copy** of the shared `db/platzi.duckdb`
  and reruns all 5 WP20 tests every time (last run: ALL PASS). `db/platzi.duckdb` itself and
  `outputs/marts/` were never written to (verified: no `a1` files appear there).

## Open issues / sensitivities

- **Small samples**: the B2B Nov-2023 cohort flag rests on 33 customers; Enterprise NDR/cohort
  metrics generally (only ~100–110 Enterprise users total) are sensitive to single-logo moves,
  as illustrated directly by the 2023-02 cohort's $ concentration finding.
- **`is_b2b` coefficient (odds ratio 3.83)** is counter-intuitive at first glance — B2C shows
  *higher* raw churn (10.1% vs. SMB 6.9%/Enterprise 8.3%, see WP11) — but this coefficient is
  the *residual* effect after controlling for engagement; it's estimated from a small B2B
  churn count (65 of 754 churned periods are B2B) and should not be over-interpreted as "being
  B2B causes churn," only as "at matched engagement levels, this dataset's few B2B churns
  looked slightly riskier." Not a primary driver in practice (see May-24 main-driver
  breakdown — only 1 of 1,024 rows is B2B-segment-driven).
- **Engagement fields drive the model almost to the point of tautology**: with 0% churn once
  materials_seen > 19 and 72% churn when materials_seen ≤ 9, the "model" is close to
  rediscovering a threshold rule already visible in `Docs/Datasets.md`'s profile. This is a
  property of the (likely partly synthetic) engagement generation process, not evidence that
  a real product's usage data would separate this cleanly — flag this when presenting AUC
  0.9997 to a non-technical audience: it reflects a strong, simple pattern in this dataset,
  not a claim that churn is this predictable in general.
- **Engagement-not-truncated finding** is itself a data-generation artifact (see §4) and a
  caveat, not a fix: in a live system, an in-progress period's engagement-to-date would need
  to be normalized (e.g., a rate) before being used to score it — here it was used as-is
  because the check showed it already represents a full-period-equivalent value.
- The dollar cohort matrix ($ retention) can exceed 100% for B2B cohorts with strong
  expansion (by construction, correct, but worth flagging when presenting a heatmap so it
  isn't read as an error).
- `plan_annual` coefficient ≈ 0.00 once engagement is controlled for — consistent with WP11's
  finding that annual retention is higher, but here the higher-annual-retention effect is
  fully explained by annual subscribers' slightly higher engagement, not the plan type itself.

## 3–5 business insights for retention strategy (→ WP23)

1. **A simple engagement floor could be an automatic early-warning trigger.** Churn goes from
   ~0% to 50–72% once `materials_seen` drops below 10 or `courses_seen` drops below 3 in a
   period — this is sharp enough to drive a rules-based (not just ML) nudge/outreach trigger,
   cheap to implement ahead of any model rollout.
2. **The May-24 "High" tier (72 subs, $3,747 MRR, $3,144 expected churn) is a small,
   high-precision list** — 86% precision at recall 100% on the historical test set means a
   retention team can act on ~70–100 accounts/month with confidence, not spam the whole base.
   B2C dominates it (70 of 72), so the first playbook to build is B2C low-engagement outreach,
   not a B2B-specific one.
3. **B2B cohorts are dollar-fragile in small batches.** The 2023-02 cohort lesson generalizes:
   any monthly B2B cohort with only 1–3 Enterprise logos will show volatile $ retention purely
   from single-account moves. WP23 should track new B2B cohorts at the *logo* level primarily
   until they reach enough scale (~10+ Enterprise accounts) for a $ retention KPI to be
   statistically meaningful, and treat early Enterprise churn as a "save this account" alert,
   not a KPI miss.
4. **Contraction, expansion, tenure, gateway and plan type are not useful churn levers**
   compared to engagement — they each move churn rate by only 2–5pp. Retention budget is
   better spent on driving product usage (courses/materials) than on payment-method nudges or
   annual-plan upsells framed as anti-churn (annual's apparent protection washes out once
   engagement is controlled for — it's a proxy for engaged customers, not a cause).
5. **Cohort-level "risk" claims need a size and significance bar.** Only 3 of 114
   cohort/age/segment checks (2.6%) cleared a 10pp/n≥20 threshold — most visible cohort
   wiggles in a heatmap are sampling noise at these cohort sizes (100–200 for B2C, 20–40 for
   B2B). WP23 should present the retention matrix with this caveat attached, and avoid
   reacting to every red cell.

## Files produced

**SQL (portable, pure SELECT; `dev_build.py`-buildable):**
- `sql/marts/mart_a1_01_cohort_retention.sql`
- `sql/marts/mart_a1_02_cohort_risk_flags.sql`
- `sql/marts/mart_a1_03_churn_indicators_base.sql`
- `sql/marts/mart_a1_04_churn_rate_by_bucket.sql`
- `sql/marts/mart_a1_05_may24_population.sql`
- `sql/marts/mart_a1_06_may24_churn_risk.sql` (auto-generated by `churn_model.py`)

**Tests:**
- `sql/tests/test_a1_01_cohort_retention.sql`, `test_a1_01b_cohort_total_reconciles.sql`,
  `test_a1_03_churn_indicators_base.sql`, `test_a1_05_may24_population.sql`,
  `test_a1_06_churn_risk_scores.sql` — all PASS.

**Python (this folder):**
- `dev_build.py` — isolated build + test runner (copies db, builds mart_a1_*, runs test_a1_*).
- `churn_model.py` — trains/evaluates the logistic regression, writes coefficients/eval/ROC
  CSVs, generates `mart_a1_06`'s SQL, scores May-24 as a Python cross-check.
- `cohort_analysis.py` — cohort pivots/heatmaps, cohort-risk digging, engagement-truncation
  check, ROC plot, May-24 CSV + tier×segment summary.

**Outputs (this folder):**
- `mart_a1_0{1,2,3,4,5,6}_*.csv` (mart exports), `cohort_pivot_{logo,dollar}_{Total,B2C,B2B}.csv`,
  `cohort_heatmap_total.png`, `cohort_heatmap_b2c_b2b.png`, `cohort_risk_flags_significant.csv`,
  `cohort_risk_composition.csv` / `_baseline.csv`, `cohort_2023_02_concentration.csv`,
  `engagement_truncation_check.csv/.png`, `churn_model_coefficients.csv`,
  `churn_model_eval.json`, `churn_model_threshold_metrics.csv`, `churn_model_roc_points.csv`,
  `churn_model_roc.png`, `may24_scores_python_crosscheck.csv`, `may24_churn_risk_list.csv`,
  `may24_risk_summary_tier.csv`, `may24_risk_summary_tier_segment.csv`, `dev.duckdb` (dev DB,
  not the shared one).

---

## Reviewer note (lead analyst, 2026-09-26) — how to present the churn model

Independent checks against the raw CSVs:

| Check | Result |
|---|---|
| Engagement ranges, churned periods | active_days 1–12, courses_seen 0–3, materials_seen 0–10 |
| Engagement ranges, renewed periods | active_days 5–28, courses_seen 2–18, materials_seen 8–97 |
| Churn rate by same-period active_days | 1–5: 50.8% · 6–8: 16.9% · 9–11: 15.7% · 12+: 1.2% |
| Churn rate by **previous**-period active_days | ≤8: 10.8% · >8: 10.1% (**no signal**) |

Implications:
1. **AUC 0.9997 is an artifact of the simulated data**: churned periods have near-zero course/material consumption by construction. Present it that way ("in production, expect AUC of ~0.70–0.85"). Don't claim near-perfect prediction.
2. Engagement is a **concurrent, in-period signal**, not a multi-period leading indicator: last month's usage does not predict this month's churn. The actionable design is a **mid-period alert** (e.g., by day 10–15 of the billing period: courses_seen ≤ 3 or materials_seen ≤ 10 → intervene before the renewal date), not a long-horizon score.
3. The May-24 at-risk list stays valid (it scores the current in-progress period, which is exactly the in-period signal).
4. IDs renumbered at consolidation to avoid collisions with WP22: model feature set = **A-06**, cohort flag rule = **A-05**, risk tiers = **D-16**. See `Docs/Plan_and_Index.md` §2.
