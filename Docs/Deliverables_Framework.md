# Deliverables & Bonus — Framework

> What we must submit, what "done" looks like for each piece, and how it maps to the evaluation criteria. Brief: `Docs/FP_A_Take_Home_Test_Platzi.md`. Work plan: `Docs/Plan_and_Index.md`.

## 1. How we are graded → where each point is earned

| Criterion (weight) | Where we earn it | Proof in the deliverable |
|---|---|---|
| Analytical Rigor (30%) | Q1–Q4, A1–A3 | Metric definitions written down, every number reproducible, reconciliation checks (e.g., MRR bridge ties out) |
| Business Acumen (25%) | A2, A4, exec summary | Each finding ends with "so what / decision"; SaaS benchmarks (LTV:CAC ≥ 3, payback < 12 mo, NDR > 100%) |
| Communication (20%) | Exec summary, charts | 1–2 pages, plain language, headline-first, one chart per message |
| Technical Skill (15%) | Model, SQL, notebook | Clean folder, formulas visible, scripts rerun end to end |
| Creativity (10%) | Bonus B1–B5 | At least 3 bonuses done well > 5 done poorly |

## 2. Required deliverables

### D1 — Financial model
> **Updated 2026-09-26 (D-01):** the model is split into layers. The data and calculation layer is SQL in DuckDB/BigQuery (`sql/`, tables `fct_*`, `mart_*`). A small **Google Sheet** holds the Assumptions, Unit Economics and Scenarios tabs with visible formulas, fed by mart exports. The tab list below is the logical spec: data/fact/MRR/Q-tabs become SQL marts, while Assumptions, A2, A4 and Scenarios live in the Sheet.

**Original file spec:** `outputs/Platzi_FPA_Model.xlsx`

| Tab | Content | Done when |
|---|---|---|
| `README` | Purpose, tab map, color legend (blue = input, black = formula, green = link), data date | Anyone can navigate it in 1 minute |
| `Assumptions` | Every assumption with an ID (A-01…), value, rationale, sensitivity flag | Every formula that uses an assumption points to this tab |
| `Data_*` | Raw CSVs pasted as-is (users, subscriptions, payments, engagement, marketing, support, gateways) | Untouched copies; row counts match `Docs/Datasets.md` |
| `Fact_Subscriptions` | Denormalized table: sub + user segment + engagement + tenure + prior MRR + delta MRR | Row count = 9,683 |
| `MRR_Monthly` | MRR by month × segment, MRR bridge (new / expansion / contraction / churn) | Apr-24 MRR ties to Q1 answer; bridge sums to zero |
| `Q1_MRR` … `Q4_NDR` | One tab per ad-hoc question: answer box on top, method, assumptions, calculation | Number + method + assumption visible on one screen |
| `A1_Cohorts` | Signup-cohort retention matrix (logo and $), heatmap formatting, churn-risk list for May-24 renewals | Matrix is triangular; May-24 list ranked by risk score |
| `A2_UnitEconomics` | Fully loaded CAC, gross margin, LTV, LTV:CAC, payback by segment, with sensitivity table | Base case + alternative denominators shown |
| `A3_NDR_Decomp` | GRR, expansion, contraction, churn by segment | Start + exp − contr − churn = end |
| `A4_Strategies` | 2–3 initiatives: driver, assumption, 6-month MRR & NDR impact, effort/impact score | Impacts use the model's own baselines |
| `Scenarios` (bonus) | Base / bull / bear 12-month MRR and subscriber projection | Driver inputs switchable in one cell |

Rules: formulas are visible (no pasted values in calculation tabs), no hard-coded numbers inside formulas, inputs are colored blue.

### D2 — Executive summary (1–2 pages, PDF)
**File:** `outputs/Platzi_FPA_Executive_Summary.pdf`

Structure (pyramid principle, answer first):
1. **Headline** — 1 sentence on the state of the business (e.g., "MRR of $205k growing X% MoM; B2B drives expansion, B2C churn is the main leak").
2. **Key numbers** — KPI strip: MRR, active subs, Q1 retention, NDR, LTV:CAC by segment.
3. **3–4 findings** — each one: insight → evidence (1 number / chart) → implication.
4. **Recommendations** — 2–3 strategies with 6-month MRR/NDR impact, effort vs. impact.
5. **Assumptions & data caveats** — short bullet list, with a pointer to the model.
6. **Next steps** — what we'd analyze with more data.

Written for a non-finance CEO: no jargon without a one-line definition (NDR, CAC, LTV).

### D3 — Visualizations
Embedded in D2 and/or in the dashboard (B4). Minimum set:

| # | Chart | Message |
|---|---|---|
| V1 | MRR trend stacked by segment (Jan-23 → Apr-24) | Growth and mix |
| V2 | MRR bridge / waterfall (T12M) | Where MRR comes from and where it leaks |
| V3 | Cohort retention heatmap | Which cohorts churn fastest |
| V4 | Engagement vs. churn (active_days buckets → churn rate) | Leading indicator |
| V5 | LTV:CAC and payback by segment (bars + 3× benchmark line) | Where to allocate capital |
| V6 | NDR decomposition by segment | Expansion vs. contraction |
| V7 | Scenario fan chart (bonus) | Range of outcomes |

## 3. Bonus deliverables (pick ≥ 3; recommended order)

| ID | Bonus | Recommended approach | Output | Priority |
|---|---|---|---|---|
| B1 | **SQL & Data Modeling** | dbt-style layers: `stg_*` (clean) → `int_subscription_periods` → `fct_subscriptions` (denormalized) + `fct_mrr_monthly`; run in DuckDB | `sql/` folder + README with lineage diagram | ⭐ High (cheap, reuses core work) |
| B2 | **Scenario Modeling** | 12-month driver model: new subs/month × retention × ARPA × expansion; base = observed, bull/bear = ± assumptions | `Scenarios` tab + chart V7 | ⭐ High (CFO loves it, feeds A4) |
| B3 | **Predictive churn model** | Logistic regression on subscription periods (features: active_days, courses_seen, materials_seen, tenure, plan, segment, MRR delta); time-based train/test; report AUC and coefficients; score May-24 renewals | `notebooks/churn_model.ipynb` + scores in A1 | ⭐ High (feeds A1 churn-risk list) |
| B4 | **Dashboard** | Interactive HTML dashboard (MRR trend, cohort heatmap, unit economics, scenarios) or Looker Studio | `outputs/dashboard.html` / link | Medium |
| B5 | **Cloud warehouse** | Load CSVs to BigQuery sandbox (free), run the B1 SQL there, screenshot + queries | `sql/bigquery/` + screenshots | Low (only if time) |

## 4. Submission package

```
Platzi_FPA_<Name>/
├── 01_Executive_Summary.pdf
├── 02_Financial_Model.xlsx
├── 03_Dashboard (link or .html)
├── 04_SQL/            (bonus B1/B5)
├── 05_Notebooks/      (bonus B3, reproducible analysis)
└── README.md          (how to navigate + how to rerun)
```
Share by Google Drive link (brief's preferred option). Final QA checklist lives in `Docs/Plan_and_Index.md` → Phase 5.
