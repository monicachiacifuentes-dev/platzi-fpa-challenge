# Looker Studio dashboard — step-by-step guide

Data source: BigQuery project `project-b7f9b2e4-dcdc-4e36-b89`, dataset **`platzi_fpa`** (49 tables, loaded by `sql/bigquery/load_to_bigquery.ps1`).
Time needed: about 60–90 minutes. Colors (the same as the executive summary): **B2C `#2a78d6` · SMB `#eb6834` · Enterprise `#1baf7a`** · scenarios: bear `#86b6ef`, base `#2a78d6`, bull `#104281`.

> ⚠️ BigQuery **Sandbox** deletes tables **60 days** after they're created. Submit within that window, or rerun the load script to refresh them.

---

## 0. Create the report and connect the data (once)
1. Go to **https://lookerstudio.google.com** → sign in with **the project owner's Google account**.
2. **Create → Report** → in "Add data to report" choose **BigQuery** → **Authorize**.
3. **My Projects → project-b7f9b2e4-dcdc-4e36-b89 → platzi_fpa → `mart_mrr_bridge`** → **Add**.
4. To add every other table later: **Resource → Manage added data sources → Add a data source → BigQuery →** the same path → the table name.
5. **Theme:** Theme and layout → *Simple*; the background is white. Rename the report: **"Platzi — FP&A Executive Dashboard"**.
6. Add **pages** (Page → New page): *1 Overview · 2 Retention · 3 Unit Economics · 4 Churn Risk · 5 Outlook & Strategies*.

**Segment colors (do this once per data source that has `segment`):** select a chart → Style → *Color by → Dimension values* → set B2C / SMB / Enterprise to the hex codes above. Looker remembers them report-wide.

---

## Page 1 — Overview
| # | Chart | Data source | Setup |
|---|---|---|---|
| 1 | **Scorecard ×4** | `mart_q1_mrr_apr24` | Metric `mrr` (SUM) with filter `segment = Total` → "MRR Apr-24". Repeat with `mart_q3_active_subs_apr24`: metric `active_subs` (SUM), filter `segment = Total` → "Active subscribers". |
| 2 | **Scorecard** | `mart_q2_retention_q1_24` | Metric `logo_rate` (MAX), filters `segment = Total`, `method = M06_primary`, `split = all` → format Percent → "Q1-24 renewal rate". |
| 3 | **Scorecard** | `mart_q4_ndr_t12m` | Metric `ndr` (MAX), filters `segment = Total` and `method = M08_M09_M10` → Percent → "NDR T12M". |
| 4 | **Stacked column chart** | `mart_mrr_bridge` | Dimension `month_end` (Date: Year-Month) · Breakdown dimension `segment` · Metric `closing_mrr` (SUM) · **Filter: exclude `segment` IN (Total, B2B)** · Style: stacked. Title: "MRR by segment". |
| 5 | **Table** | `mart_mrr_bridge` | Dimension `month_end` · Metrics `new_mrr`, `expansion_mrr`, `contraction_mrr`, `churn_mrr`, `closing_mrr` · Filter `segment = Total`. Title: "MRR bridge". |

Add a **Drop-down list control** (Add a control → Drop-down) at the top, with control field `segment`, so the viewer can filter the page.

## Page 2 — Retention
| # | Chart | Data source | Setup |
|---|---|---|---|
| 1 | **Pivot table with heatmap** (cohort matrix) | `mart_a1_01_cohort_retention` | Row dimension `cohort_month` (Year-Month) · Column dimension `month_k` · Metric `logo_retention` (AVG, Percent) · Filter `segment_group = Total` · Style → **Heatmap**, single blue color. Title: "Cohort retention (share still active k months after signup)". |
| 2 | **Bar chart** (waterfall-style) | `mart_a3_02_t12m_waterfall_long` | Dimension `step` (sorted by `step_order` ascending) · Metric `amount` (SUM) · Filter `segment = Total`. Title: "NDR T12M: start → churn → contraction → expansion → end". |
| 3 | **Column chart** | `mart_a1_04_churn_rate_by_bucket` | Dimension `bucket` (sort by `sort_order`) · Metric `churn_rate` (AVG, Percent) · Filter `dimension = active_days`. Title: "Churn rate by active days in the period". Add a text box: *"Simulated data: sharper than reality."* |

## Page 3 — Unit Economics
| # | Chart | Data source | Setup |
|---|---|---|---|
| 1 | **Column chart** | `mart_a2_12_unit_economics_summary` | Dimension `segment` (exclude Total) · Metric `ltv_cac_t6m` (SUM) · Style → **Reference line**: constant **3**, label "3× benchmark". Title: "LTV : CAC by segment (T6M margin)". |
| 2 | **Table** | same | Dimension `segment` · Metrics `cac_fully_loaded_t6m`, `arpa_t6m_avg`, `gm_pct_t6m_base`, `lifetime_dollar_months`, `ltv_base`, `ltv_cac_t6m`, `cac_payback_months_t6m`. Rename the columns to plain English. |
| 3 | **Table** | `mart_a2_04_funnel_channel_total` | All columns → "Cost per sign-up vs. per paying customer". |
| 4 | **Text box** | — | "At Apr-24 gross margin (41%), LTV:CAC ≈ B2C 0.7× · SMB 4.1× · Enterprise 3.0×." |

## Page 4 — Churn Risk (May-24)
| # | Chart | Data source | Setup |
|---|---|---|---|
| 1 | **Pivot table** | `mart_a1_06_may24_churn_risk` | Rows `risk_tier` · Columns `segment` · Metrics Record Count and `mrr_at_risk` (SUM). |
| 2 | **Table** (paginated) | same | Dimensions `subscription_id`, `user_id`, `segment`, `plan_type`, `risk_tier` · Metrics `prob_churn` (Percent), `mrr` · Sort by `prob_churn` descending. |
| 3 | **Drop-down controls** | same | `risk_tier` and `segment`. |

## Page 5 — Outlook & Strategies
| # | Chart | Data source | Setup |
|---|---|---|---|
| 1 | **Time series** | `mart_s_02_projection_monthly` | Dimension `month_end` · Breakdown `scenario` · Metric `closing_mrr` (SUM) · Filter `segment = Total` AND `plan_type = ALL`. Colors: bear/base/bull as above. Title: "MRR outlook to Apr-25". |
| 2 | **Table** | `mart_s_03_scenario_summary` | Dimensions `scenario`, `segment` · Metrics `mrr_apr25`, `mrr_growth_pct`, `subs_apr25`, `forward_ndr_m12`. |
| 3 | **Table** | `mart_s_04_strategy_impact` | Filter `case = base` · Dimensions `strategy`, `segment`, `effort` · Metrics `mrr_delta_m6`, `mrr_delta_m12`, `ndr_delta_pp_m6`. |

---

## Share
**Share → Manage access → "Anyone with the link can view"** → copy the link and put it in the submission README and the email to the recruiter. The viewers need no BigQuery access (the report uses the owner's credentials by default).

## Troubleshooting
| Problem | Fix |
|---|---|
| A date shows as text | In the data source, set the field type to **Date (YYYY-MM-DD)** |
| A percentage shows as 0.89 | Field → Type → **Numeric → Percent** |
| "Total" appears twice in the stacked chart | Add the filter excluding `segment` Total and B2B |
| Tables disappeared | The Sandbox 60-day expiry: rerun `powershell -ExecutionPolicy Bypass -File sql\bigquery\load_to_bigquery.ps1` |
