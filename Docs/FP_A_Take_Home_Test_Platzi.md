# FP&A — Take Home Test (Platzi)

> Source: `Docs/Originals/FP_A_Take_Home_Test_Platzi__3___1___1_.pdf` (converted to Markdown, full content)

This assessment evaluates analytical thinking, financial modeling, and strategic business acumen for the FP&A position at Platzi.

## Challenge

You are the new FP&A hire at Platzi, a high-growth EdTech company offering **monthly and annual subscriptions** for online courses, workshops, and professional content. Two business lines:

- **B2C** — Individual learners subscribing directly through the platform.
- **B2B (SMB & Enterprise)** — Companies purchasing seat-based licenses for their teams.

The CEO and CFO need a clear financial picture of the business. Analyze the datasets, answer stakeholder questions, and deliver actionable insights that inform growth strategy and capital allocation decisions.

## Scenario & Data

Seven simulated datasets replicating a real-world SaaS environment with B2C and B2B revenue streams. **All data covers Jan 2023 – Apr 2024 (16 months).**

| Dataset | Description | Rows | Columns |
|---|---|---|---|
| users.csv | User demographics and segment | 2,695 | user_id, first_name, email, age, segment, signup_date |
| subscriptions.csv | Subscription lifecycle | 9,683 | subscription_id, user_id, plan_type, start_date, end_date, mrr, status |
| payments.csv | Payment history | 17,209 | email, subscription_id, amount, payment_date, payment_gateway_id |
| payment_gateways.csv | Payment gateway details | 5 | payment_gateway_id, payment_gateway_name |
| engagement.csv ⚠️ *not provided* | User engagement data | 9,683 | user_id, subscription_id, active_days, courses_seen, materials_seen, favorite_category |
| marketing_spend.csv ⚠️ *not provided* | Monthly acquisition costs by channel | 144 | month, channel, spend, new_users_acquired, segment |
| support_costs.csv | Monthly operational costs | 64 | month, category, amount |

### Data Notes — Possible Values

| Field | Possible values |
|---|---|
| segment | B2C \| SMB \| Enterprise |
| plan_type | monthly \| annual |
| status | active \| churned \| renewed |
| channel | Paid Search \| Paid Social \| Organic \| Content \| Sales Team |
| cost category | CS Salaries \| Infrastructure \| Content Production \| G&A |
| payment gateway | Stripe \| PayPal \| MercadoPago \| Payoneer \| Wire Transfer |

### Key Relationships

- users → subscriptions via `user_id` (one user can have multiple sequential subscriptions).
- users → payments via `email`; subscriptions → payments via `subscription_id`.
- engagement has one row per subscription period, linked via `user_id` and `subscription_id`.
- marketing_spend is aggregated at month/channel/segment level (not joinable 1:1 to users).
- `status = renewed` ⇒ user was retained; a new row appears for the next period. **`mrr` may change between renewals (expansion or contraction).**

## Stakeholder Questions (Required)

### Ad-hoc Questions
Answer each with a clear number, brief methodology, and assumptions.

1. **MRR as of April 2024**, broken down by segment (B2C, SMB, Enterprise).
2. **Q1 2024 retention rate**; how it differs between B2C and B2B (SMB + Enterprise).
3. **Active subscribers in April 2024**, by segment and plan type (monthly vs. annual).
4. **Net Dollar Retention (NDR)** for the trailing 12 months ending April 2024 — company level and by segment.

### Analysis
Show work, state assumptions, give clear recommendations. Structured thinking > perfect answers.

1. **Cohort Analysis & Churn Risk** — Build a monthly signup-cohort retention matrix. Identify cohorts with highest churn risk. Flag users renewing in **May 2024** most likely to churn, and explain which leading indicators (engagement, tenure, plan type, etc.) predict churn.
2. **Unit Economics Deep-Dive** — Fully Loaded CAC by segment: all marketing spend, sales team costs, and an allocation of G&A from support_costs.csv. Compute LTV using observed retention curves and gross margins. Report **LTV:CAC** and **CAC Payback Period (months)** per segment.
3. **NDR Decomposition** — Break NDR into Gross Retention, Expansion (MRR increases at renewal), and Contraction (MRR decreases at renewal). Which segment drives most expansion? Where is contraction concentrated?
4. **Retention Strategy Recommendations** — Propose 2–3 data-driven strategies. For each, estimate potential impact on MRR and NDR over the next 6 months. Prioritize by effort vs. impact.

## Deliverables
Clarity, structure, and ability to communicate to non-finance stakeholders.

1. **Financial model** (spreadsheet or notebook) — all calculations, formulas visible, assumptions clearly labeled.
2. **Written executive summary** (1–2 pages max) — findings and recommendations as if presenting to CEO and CFO.
3. **Supporting visualizations/charts** (embedded in summary or separate dashboard).

Accepted formats: Google Sheets / Excel, Jupyter Notebooks, PDF reports, interactive dashboards (Looker Studio, Streamlit, Hex, etc.).

## Bonus Points (Optional)
- **SQL & Data Modeling** — SQL or dbt-style model creating a denormalized fact table for FP&A.
- **Scenario Modeling** — Base / bull / bear projecting MRR and subscriber count for next 12 months with different retention & acquisition assumptions.
- **Predictive Model** — ML model (logistic regression, survival analysis, etc.) scoring churn probability per subscriber.
- **Dashboard** — Interactive executive dashboard: MRR trends, cohort retention heatmap, unit economics by segment.
- **Cloud Warehouse** — Upload data to BigQuery (or similar) and run analysis there.

## Evaluation Criteria

| Criteria | Weight | What they look for |
|---|---|---|
| Analytical Rigor | 30% | Correct calculations, sound methodology, clearly stated assumptions |
| Business Acumen & Curiosity | 25% | Insights tied to real business decisions; understanding of SaaS economics |
| Communication | 20% | Clarity of presentation; storytelling with data for a non-finance audience |
| Technical Skill | 15% | Proficiency with tools (Excel, Python, SQL, etc.); clean, reproducible work |
| Creativity & Initiative | 10% | Going beyond the minimum; novel approaches; bonus section work |

## Logistics
- **Time limit:** 2 calendar days from receipt.
- **Ambiguity:** If unclear, state your assumption and proceed. *"If necessary, create or simulate new data base."*
- **Submission:** Google Drive link or email files to recruiter contact.
