# Plan & Work Index — Platzi FP&A Challenge

> **This is the master plan.** Any agent (Claude, ChatGPT, Gemini, Copilot, etc.) starts here.
> Read order: `AGENTS.md` → this file → `Docs/FP_A_Take_Home_Test_Platzi.md` → `Docs/Datasets.md` → `Docs/Deliverables_Framework.md`.
> Raw data: `Docs/Originals/*.csv`. **Never edit the originals.**

---

## 0. Status board

| Phase | Work packages | Status |
|---|---|---|
| P0 Setup | WP00, WP01 | ✅ |
| P1 Ad-hoc questions | WP10–WP13 | ✅ |
| P2 Analyses | WP20–WP23 | ✅ WP20–WP23 done & consolidated (31/31 tests pass) |
| P3 Bonus | WP30–WP34 | ✅ WP30 local · WP31 scenarios · WP32 churn model · WP33 Streamlit (deployed) · WP34 BigQuery: 49 tables loaded + Q1–Q4 native BigQuery SQL reconciled 242/242 (WP34b). Looker Studio dropped (time) |
| P4 Packaging | WP40–WP42 | ✅ WP40 model `outputs/Platzi_FPA_Model.xlsx` (46/46 verified) · WP41 charts ✅ · WP42 summary ✅ (name placeholder) · WP33 Streamlit ✅ (9/9 tests) |
| P5 QA & AI comparison | WP50–WP51 | ✅ WP50 QA 130/130 (`work/WP50_qa/results.md`) · 🟨 WP51 kit ready in `comparison/` (the user runs the prompts; the lead reviews the scorecard) |

Legend: ⬜ todo · 🟨 in progress · ✅ done · 🔁 needs rework. Update this table when a WP changes status.

---

## 1. Metric definitions (single source of truth)

**All agents must use these definitions.** If an agent disagrees, it writes the alternative in its `results.md` as a sensitivity, not as the answer.

| ID | Metric | Definition |
|---|---|---|
| M-01 | As-of date | 2024-04-30 (last day of data). "April 2024" = snapshot at 2024-04-30. |
| M-02 | Active subscription on date D | `start_date ≤ D < end_date`. Verified: at 2024-04-30 this equals `status='active'` (1,941 subs). |
| M-03 | MRR | Sum of `subscriptions.mrr` of active subscriptions on D. Annual plans are already monthly-normalized (399/12 = 33.25). Payments are **not** used for MRR. |
| M-04 | Segment | `users.segment` via `user_id`. B2B = SMB + Enterprise. |
| M-05 | Customer | One `user_id` = one customer (B2B seats are already priced into mrr). |
| M-06 | Retention rate (Q1 2024), primary | Renewal-event basis: subscriptions with `end_date` in 2024-01-01…2024-03-31 → `renewed / (renewed + churned)`. Logo and $ versions. |
| M-07 | Retention rate, cross-check | Customer-snapshot basis: customers active on 2023-12-31 who are still active on 2024-03-31 / customers active on 2023-12-31. |
| M-08 | NDR T12M | Customers active on 2023-04-30. NDR = their MRR on 2024-04-30 (0 if gone) ÷ their MRR on 2023-04-30. New customers after 2023-04-30 are excluded. |
| M-09 | GRR | Same base as M-08, but each customer's end MRR is capped at their start MRR. |
| M-10 | Expansion / Contraction | Per customer in the M-08 base: Δ = end MRR − start MRR. Δ>0 → expansion; Δ<0 with end>0 → contraction; end=0 → churn. Identity: Start + Exp − Contr − Churn = End. Cross-check: sum of `mrr` deltas at renewal events in T12M. |
| M-11 | Signup cohort | `users.signup_date` month. Retention in month k = % of cohort users with an active sub at month-end of signup month + k (logo); $ version uses MRR. |
| M-12 | Gross margin | Revenue = MRR (monthly). COGS = CS Salaries + Infrastructure + Content Production. G&A = opex (goes into fully loaded CAC per the brief). GM by segment: COGS allocated by share of MRR (A-03). |
| M-13 | Fully loaded CAC | (Marketing spend of segment incl. Sales Team + allocated G&A) ÷ new customers of segment, over the 16 months (plus a T6M view). |
| M-14 | LTV | ARPA × GM% × expected lifetime, where lifetime = Σ of observed retention curve (extrapolated with the last observed monthly churn rate). Cross-check: ARPA × GM% ÷ monthly churn. |
| M-15 | CAC payback (months) | CAC ÷ (ARPA × GM%). |

---

## 2. Decisions & assumptions log

| ID | Topic | Decision (proposed) | Status |
|---|---|---|---|
| D-01 | Tooling | Python 3.12 x64 in `.venv/` (run `.venv/Scripts/python.exe`; set `PYTHONIOENCODING=utf-8`), pinned in `requirements.txt`. **Stack (approved 2026-09-26):** DuckDB locally (`db/platzi.duckdb`) → same SQL on BigQuery Sandbox → **Looker Studio** dashboard (Claude prepares one BigQuery table per chart and a build guide; the user clicks) + **Streamlit** app (built fully by Claude, optional) + a small **Google Sheet** for assumptions, unit economics and scenarios. This replaces the full Excel model, in line with Platzi's Excel → database migration. | ✅ |
| D-10 | Model usage | Execution WPs (SQL, scripts) run as **Sonnet** subagents; Opus reviews results and writes the executive summary. | ✅ |
| D-11 | B2B accounts | B2B users share 12 company email domains, but every domain mixes SMB and Enterprise users, so domain ≠ account. **1 user_id = 1 customer** (M-05). Caveat in the summary. | ✅ |
| D-02 | MRR source | `subscriptions.mrr` (M-03); payments only for cash and billing checks | ✅ |
| D-03 | Retention definition | M-06 primary, M-07 cross-check | proposed |
| D-04 | NDR definition | M-08 snapshot method | proposed |
| D-05 | G&A allocation to CAC (A-01) | Share of G&A allocated to acquisition = **marketing spend share of total opex** (marketing ÷ (marketing + support costs)), split by segment by **share of marketing spend** (base; sensitivity: share of new customers). Sensitivity: 0% / 25% / 50% of G&A. Result: barely moves CAC (<12%) | ✅ (WP21) |
| D-06 | CAC denominator (A-02) | **Base (market standard): new *paying* customers = users.csv signups by month × segment.** Evidence: B2C users.csv / marketing `new_users_acquired` = 8–12% every month (corr 0.88) → marketing counts signups/registrations, users.csv counts paying subscribers. Report marketing's figure as a **funnel metric** (cost per signup, signup→paid conversion ≈ 10% B2C, ≈ 50% SMB). Enterprise: users.csv > marketing (109 vs 82) → marketing likely counts deals; caveat. | ✅ approved 2026-09-26 |
| D-07 | COGS allocation by segment (A-03) | **Base: all COGS (CS Salaries + Infrastructure + Content) by share of MRR** → GM% is uniform across segments (neutral default without cost-driver data). **Downside sensitivity:** CS & Infrastructure by active customers, Content by MRR (B2C GM −37%, SMB 49%, Ent 70%). Rejected as base because it assumes one B2C learner costs as much to serve as an Enterprise company. | ✅ (lead review) |
| D-08 | "Churn risk May 2024" population | Subscriptions with `end_date` in 2024-05, status active (monthly renewals and annual renewals due) → 1,024 subs / $87,829 MRR | ✅ (WP20) |
| D-09 | Duplicate emails | Join payments to users via `subscription_id → user_id`, not email | ✅ |
| D-12 | Monthly MRR movement categories (WP01/WP30 SQL) | `fct_customer_mrr_monthly.movement` extends M-10's vocabulary to a full monthly grid: `new` (first grid month, or prev_mrr=0→mrr>0), `expansion`, `contraction`, `churn` (as in M-10), plus `retained_flat` (no $ change while active) and `inactive` (no coverage, before signup / after churn). Implementation detail, does not change M-08..M-10 math. | ✅ (implementation) |
| D-13 | "Main gateway" per subscription (fct_subscriptions) | The payment gateway used on the largest number of payments for that `subscription_id`; ties broken by lowest `payment_gateway_id`. | ✅ (implementation) |
| D-14 | `next_status` column (int_subscription_periods / fct_subscriptions) | Pass-through of `subscriptions.status` (renewed/active/churned already encodes the fate at `end_date`); kept as a separate, self-documenting column name alongside `status`. | ✅ (implementation) |

| D-15 | NDR robustness (WP22) | Secondary NDR definitions: **T6M snapshot** (base 1,124 customers active 2023-10-31) and **monthly-compounded T12M**. Snapshot T12M stays the headline answer to Q4; the others are shown as robustness checks because the T12M base is small (417; 12 Enterprise). | ✅ |
| D-16 | May-24 risk tiers (WP20) | High ≥ 50% churn probability · Medium 25–49% · Low < 25% | ✅ |
| D-17 | Gross margin period for LTV | Base = **T6M average GM 29.3%** (conservative). GM is rising fast (−919% Jan-23 → +41% Apr-24, operating leverage: revenue ×28 vs. COGS ×1.7). **Run-rate sensitivity = Apr-24 GM 40.9%** → LTV:CAC ≈ B2C 0.70× · SMB 4.1× · Ent 3.0×. Both go in the summary; GM is an input cell in the Google Sheet. | ✅ (lead review) |
| D-18 | Churn model framing (WP20/WP32) | Same-period engagement almost perfectly separates churn (AUC 0.9997 = simulated-data artifact). Previous-period engagement has **no** signal (10.8% vs 10.1%). Present as an **in-period early-warning alert**, with "expect AUC ≈ 0.70–0.85 in production". | ✅ (lead review) |

| D-19 | Scenario design (WP31) | Engine = monthly compartment model by segment × plan, calibrated on T6M (Nov-23..Apr-24). **Base = flat acquisition at the T6M average + T6M churn/expansion rates** (deliberately prudent: May-24 churned MRR is projected at $7.8k vs. the Apr-24 actual $6.0k and the WP20 model's $4.3k; new MRR $21.2k vs. the Apr-24 actual $22.7k). **Bull** = acquisition trend + the 3 WP23 strategies at their base case. **Bear** = churn stress, flat/lower acquisition, expansion halved (A-19). Backtest MAPE: MRR 10.3% / customers 7.7% (under-shoots, since the business accelerates). | ✅ (lead review) |

| D-20 | Model reconciliation tolerance (WP40) | Sheet vs. Python engine, Apr-25 MRR: **≤ 3% for totals, ≤ 5% for single segments** (SMB Bull −3.7% stacks 3 levers on a small base). Verified 46/46. | ✅ (lead review) |
| D-25..D-27 | Streamlit implementation (WP33) | CSV-only data source; main-driver derivation for the at-risk table; reuse of the pure engine functions for the sliders. See `work/WP33_dashboard/results.md` | ✅ |

**Assumptions register (A-xx)** — details live in each WP's results.md
| ID | Assumption | Source |
|---|---|---|
| A-01 | G&A share to acquisition (see D-05) | WP21 |
| A-02 | CAC denominator = new paying customers (see D-06) | WP21 |
| A-03 | COGS allocation by MRR (see D-07) | WP21 |
| A-04 | MRR tier cutoffs: <100 / 100–300 / 300–600 / 600–1,000 / 1,000+ | WP22 |
| A-05 | Cohort risk flag: ≥ 10 pp below the same-age benchmark and n ≥ 20 | WP20 |
| A-06 | Churn model features: segment collapsed to B2C/B2B; favorite_category dropped | WP20 |
| A-15 | Survival curve reliable only where the exposed cohort n ≥ 20 | WP21 |
| A-16 | Dollar-retention tail falls back to logo churn when unstable | WP21 |
| A-17 | Dollar tail decay floored at logo tail churn | WP21 |
| A-18 | LTV horizon cap 60 months (sensitivity 36 / uncapped) | WP21 |
| A-19 | Bear stress constants; A-19c annual→monthly churn conversion | WP31 |
| A-20 | Strategy 1 (engagement alert) save-rate range | WP23 |
| A-21 | Strategy 2 (monthly→annual) conversion-rate range | WP23 |
| A-22 | Strategy 3 (B2B playbook) expansion uplift & contraction reduction | WP23 |
| A-23 | Survival-curve tail decay exposed as Assumptions inputs in the workbook | WP40 |
| A-30 | Cohort heatmap: SMB/Enterprise fall back to B2B (small n) | WP33 |
| A-31 | Funnel view uses the T6M window | WP33 |

**Open issue for WP40:** "retention-adjusted payback" shows "never" only because it's limited to the observed 11–15 months. Recompute it in the Sheet on the extrapolated 60-month curve.

Record new assumptions here as A-xx and mirror them in the Google Sheet `Assumptions` tab.

**Verified data facts (2026-09-26):**
- Every user has one contiguous chain of subscriptions: each `renewed` row's next row starts exactly on its `end_date`. There are no gaps, no overlaps and no reactivations. The chain ends in `churned` (754 users) or `active` (1,941 users).
- **No plan switches ever occur** (monthly→monthly 6,839, annual→annual 149). Monthly→annual migration is untested in the data.
- The first subscription always starts on `signup_date`.
- B2C mrr is fixed (49 / 33.25). SMB and Enterprise mrr vary → all expansion and contraction is B2B.
- At most one active subscription per user on any date.

---

## 3. Folder structure

```
PRUEBA_PLATZI/
├── AGENTS.md                 ← entry point for any AI agent
├── CLAUDE.md                 ← points to AGENTS.md
├── Docs/                     ← brief, data dictionary, framework, this plan (Markdown)
│   └── Originals/            ← raw PDF + 7 CSVs (read-only)
├── work/WPxx_<name>/         ← one folder per work package: scripts + results.md
├── sql/                      ← dbt-style models (B1)
├── notebooks/                ← analysis notebooks (B3)
├── outputs/                  ← final Excel, PDF, dashboard
└── comparison/               ← outputs from other AI tools + scorecard (WP51)
```

---

## 4. Work package index (for agents)

Each WP is self-contained. An agent gets: the WP row + section 1 (definitions) + the listed inputs. Output always goes to `work/WPxx_<name>/results.md` with this template:

```markdown
# WPxx — <name>
## Answer (numbers first)
## Method
## Assumptions used (IDs)
## Checks performed (reconciliations, row counts)
## Open issues / sensitivities
## Files produced
```

### P0 — Setup
| WP | Name | Inputs | Output | Depends on |
|---|---|---|---|---|
| WP00 | Environment | — | Python + pandas, duckdb, scikit-learn, openpyxl, matplotlib installed; `requirements.txt` | D-01 |
| WP01 | Fact tables | all CSVs | `work/WP01/fct_subscriptions.csv` (sub + segment + engagement + prev_mrr + delta_mrr + tenure + renewal #), `fct_mrr_monthly.csv` (customer × month-end MRR, 16 months) | WP00 |

### P1 — Ad-hoc questions (parallelizable after WP01)
| WP | Question | Definitions | Output |
|---|---|---|---|
| WP10 | Q1 MRR Apr-24 by segment | M-01..04 | table + method (expected total ≈ $204.7k) |
| WP11 | Q2 Q1-24 retention, B2C vs B2B | M-06, M-07 | logo & $ retention, by segment |
| WP12 | Q3 active subs Apr-24 by segment × plan | M-02 | 3×2 matrix (total 1,941) |
| WP13 | Q4 NDR T12M, company & segment | M-08 | NDR %, with GRR |

### P2 — Analyses
| WP | Analysis | Inputs | Output | Depends on |
|---|---|---|---|---|
| WP20 | A1 Cohorts & churn risk | fct tables, engagement | retention matrix (logo + $), riskiest cohorts, indicator analysis (churn rate by active_days / courses buckets, tenure, plan, segment), May-24 at-risk list | WP01 (WP32 improves it) |
| WP21 | A2 Unit economics | marketing, support, fct | CAC, GM, LTV, LTV:CAC, payback by segment + sensitivity (D-05, D-06) | WP01 |
| WP22 | A3 NDR decomposition | fct_mrr_monthly | GRR / expansion / contraction / churn by segment; where contraction concentrates (segment × plan × tenure) | WP13 |
| WP23 | A4 Retention strategies | WP20–22 | 2–3 initiatives, 6-mo MRR & NDR impact, effort × impact matrix | WP20, WP21, WP22 |

Strategy hypotheses to test in WP23 (from the data profile): (1) low-engagement early warning (churned periods average 6.5 active days vs. 14.8), (2) monthly → annual migration in B2C (churn per ended period: annual 6/155 ≈ 4% per year vs. monthly 748/7,587 ≈ 10% per month), (3) B2B expansion/QBR playbook to turn contraction into expansion.

### P3 — Bonus
| WP | Bonus | Output | Depends on |
|---|---|---|---|
| WP30 | B1 SQL / dbt-style model | `sql/staging`, `sql/intermediate`, `sql/marts` run in DuckDB — ✅ **DuckDB (local) part done**: `sql/run_pipeline.py` builds `db/platzi.duckdb` end to end, all `sql/tests/*.sql` PASS, marts exported to `outputs/marts/`. See `sql/README.md` for lineage + the DuckDB-specific functions to edit for the BigQuery port (WP34, still open). | WP00 |
| WP31 | B2 Scenarios base/bull/bear | 12-mo MRR + subs projection | WP10–13, WP21 |
| WP32 | B3 Churn model | logistic regression, AUC, coefficients, May-24 scores | WP01 |
| WP33 | B4 Dashboard | interactive HTML | WP10–WP31 |
| WP34 | B5 BigQuery (optional) | queries + screenshots | WP30 |

### P4 — Packaging
| WP | Name | Output |
|---|---|---|
| WP40 | Excel model | `outputs/Platzi_FPA_Model.xlsx` per `Deliverables_Framework.md` D1 |
| WP41 | Charts V1–V7 | PNG/SVG in `outputs/charts/` |
| WP42 | Executive summary | `outputs/Platzi_FPA_Executive_Summary.pdf` (≤ 2 pages) |

### P5 — QA & comparison
| WP | Name | Output |
|---|---|---|
| WP50 | QA checklist | All checks below ✅ |
| WP51 | AI tool comparison | `comparison/scorecard.md` |

**QA checklist (WP50)**
- [ ] Row counts match `Docs/Datasets.md`
- [ ] Apr-24 MRR = sum of segments = last point of MRR trend = scenario starting point
- [ ] MRR bridge: Start + New + Exp − Contr − Churn = End, every month
- [ ] NDR identity holds (M-10); GRR ≤ 100%; NDR ≥ GRR
- [ ] Active subs by segment × plan sum to 1,941
- [ ] Every assumption in the Excel exists in the log (section 2)
- [ ] Exec summary ≤ 2 pages; every number in it appears in the model
- [ ] Model: no hard-coded numbers in formulas; inputs blue

---

## 5. Execution timeline (2 calendar days)

| Block | Work |
|---|---|
| Day 1 AM | WP00, WP01, WP10–13 (answers to the ad-hoc questions) |
| Day 1 PM | WP20, WP21, WP22, WP30 (SQL comes almost free with WP01) |
| Day 2 AM | WP32, WP23, WP31, WP40 |
| Day 2 PM | WP41, WP42, WP33, WP50, WP51 → submit |

Parallelization: after WP01, the WP10–13 and WP20–22 packages can run in separate agents.

---

## 6. AI tool comparison protocol (WP51)

Goal: use other AI tools (ChatGPT, Gemini, Copilot, Julius, etc.) as **independent auditors**. Where they agree with us, we're more confident. Where they disagree, we find the ambiguity and state it as an assumption.

**Two rounds per tool:**
1. **Blind round:** give the tool only the brief (`Docs/FP_A_Take_Home_Test_Platzi.md`) + the CSVs. Don't share our definitions. This shows how others interpret the ambiguity (the recruiter may think the same way).
2. **Aligned round:** give the tool section 1 (definitions) + the WP prompt. Results should now match ours. If they don't, there's a bug on one side.

**Prompt template (aligned round):**
```
You are an FP&A analyst. Using the attached CSVs and ONLY these metric definitions:
<paste section 1>
Answer <WPxx question>. Return: the number(s), the method in 3 bullets, assumptions,
and one reconciliation check. Output as a Markdown table.
```

**Scorecard: `comparison/scorecard.md`**

| Metric | Ours | ChatGPT (blind) | ChatGPT (aligned) | Gemini (blind) | Gemini (aligned) | Other | Δ explained by |
|---|---|---|---|---|---|---|---|
| MRR Apr-24 total | | | | | | | |
| MRR B2C / SMB / Ent | | | | | | | |
| Q1-24 retention B2C / B2B | | | | | | | |
| Active subs Apr-24 | | | | | | | |
| NDR T12M total / by seg | | | | | | | |
| GRR / Exp / Contr | | | | | | | |
| CAC by segment | | | | | | | |
| LTV:CAC by segment | | | | | | | |
| Payback (months) | | | | | | | |
| Churn model AUC | | | | | | | |

Qualitative comparison (1–5 each): insight quality, recommendations, clarity, handling of ambiguity (did it spot D-06?), and errors found. Note the best ideas from other tools in `comparison/ideas.md` and adopt them if they're sound.

⚠️ Before uploading data to external tools: the data is simulated (no real PII), but check that the recruiter's terms don't forbid sharing it.

---

## 7. HANDOFF (2026-09-27): read this first in a new session
**Done:** P0, P1 (Q1–Q4), P2 (WP20–23), WP30 (local SQL), WP31 scenarios, WP32 churn model, WP41 charts, WP42 executive summary (`outputs/Platzi_FPA_Executive_Summary.pdf`, 2 pages; name set to Monica Chia and PDF re-printed 2026-09-27; to re-print after edits, change the .html then print with headless Edge from PowerShell using `--user-data-dir`).
**Launched but NOT yet reviewed (Sonnet agents, may have finished):**
- WP40 model → `outputs/Platzi_FPA_Model.xlsx`, `work/WP40_model/{build_model.py,verify_model.py,results.md}`
- WP33 Streamlit ✅ **deployed** (Streamlit Cloud, checked 2026-09-27, all 5 tabs render, KPIs match): https://platzi-challenge-3wrgxevauckcvnh6rbdvaf.streamlit.app/ · reviewed 2026-09-27 (lead reran `pytest app/test_app.py`: 9/9 pass). Proposed IDs D-25..D-27, A-30, A-31 are in its results.md. Note: the agent deleted a stray `work/WP31_scenarios_test.duckdb` (unused scratch file).
- WP40 ✅ reviewed 2026-09-27: `verify_model.py` 46/46 pass. Retention-adjusted payback on the 60-mo curve: B2C > 60 · SMB 17 mo · Ent 21 mo.
- WP34 ✅ 2026-09-27: 49/49 tables loaded to BigQuery `project-b7f9b2e4-dcdc-4e36-b89.platzi_fpa` by `sql/bigquery/load_to_bigquery.ps1` (the script prepends the portable gcloud bin to PATH). Verified in BigQuery: Apr-24 MRR 204,709.09 / 1,941 subs from the raw tables. **Sandbox tables expire after 60 days.** Looker Studio click-guide: `outputs/Looker_Studio_Guide.md` (the user builds it).
**GitHub:** public repo https://github.com/monicachiacifuentes-dev/platzi-fpa-challenge (gh CLI installed via winget, not on PATH in old shells: `%LOCALAPPDATA%/Microsoft/WinGet/Packages/GitHub.cli_*/bin/gh.exe`). `.gitignore` excludes *.duckdb, .venv, Docs/Originals, CLAUDE.md. Next: the user deploys Streamlit Cloud (main file `app/streamlit_app.py`, Python 3.12) → add the link to the README + summary.
**Remaining:** the user builds Looker Studio; the user runs the WP51 prompts (`comparison/README.md`) → the lead reviews the scorecard; submission package + README; replace [Candidate name] in the summary (then re-print the PDF). WP50 QA ✅ 130/130 (corrected the summary: 29×, −$0.8k).
**Next steps:**
1. Check that each results.md exists. If not, rerun that WP with Sonnet using the same spec (Deliverables_Framework D1 / B4).
2. Review: `verify_model.py` passes; `app/test_app.py` passes; numbers match the summary (MRR 204,709; subs 1,941; LTV:CAC 0.50/2.92/2.16 at T6M, 0.70/4.07/3.02 at Apr-24 GM).
3. Consolidate the proposed IDs (A-23+/D-20+ from WP40; A-30+/D-25+ from WP33) into §2.
4. WP34: BigQuery Sandbox upload (user runs `! gcloud auth login`) + Looker Studio click-guide (one table per chart).
5. WP50 QA checklist, WP51 AI comparison (§6), submission package (Deliverables_Framework §4).
**Rules:** execution → Sonnet subagents; review/writing → Opus. Rebuild the db: `PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe sql/run_pipeline.py` (31/31 tests pass).
- 2026-09-27 (session a0998f4c): exec summary PDF re-printed with name (Monica Chia) + Streamlit link. **WP34b ✅** Q1–Q4 ported to BigQuery SQL from raw tables (`sql/bigquery/q*.sql`, `run_bigquery.ps1`, `reconcile.py` → `outputs/bigquery_reconciliation.csv`, 242/242 PASS; lead re-queried bq_q1 live). **Looker Studio dropped** from deliverables (not built); BigQuery presented as the cloud warehouse. **WP43 ✅** architecture diagram `Deliverables/06_Architecture.drawio` (built by `work/WP43_architecture/build_drawio.py`; preview via `drawio_url.py`).
