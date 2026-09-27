# AI comparison scorecard (WP51)

"Ours" = the verified pipeline values (`db/platzi.duckdb`, QA 130/130). Fill one column per tool × round.
Flag: ✅ within 1 pp / 2% · ⚠️ different, explained by a definition · ❌ different, unexplained (investigate).

## Numbers
| Metric | **Ours** | ChatGPT blind | ChatGPT aligned | Gemini blind | Gemini aligned | Other | Δ explained by |
|---|---|---|---|---|---|---|---|
| MRR Apr-24 total | **$204,709.09** | | | | | | |
| MRR B2C / SMB / Ent | **64,365.00 / 53,869.37 / 86,474.72** | | | | | | |
| Active subs total | **1,941** | | | | | | |
| Subs B2C m/a · SMB m/a · Ent m/a | **844/692 · 113/190 · 12/90** | | | | | | |
| Q1-24 retention logo: total / B2C / B2B | **90.1% / 89.6% / 93.8%** | | | | | | |
| Q1-24 retention $: total / B2C / B2B | **92.2% / 89.5% / 95.2%** | | | | | | |
| NDR T12M: total / B2C / SMB / Ent | **63.7% / 43.1% / 89.8% / 71.8%** | | | | | | |
| GRR T12M total | **59.9%** | | | | | | |
| NDR base: customers, start MRR | **417, $34,771.54** | | | | | | |
| Expansion / contraction / churn $ (T12M) | **1,329.43 / 168.42 / 13,782.57** | | | | | | |
| GM% (Nov-23..Apr-24 avg) | **29.3%** (Apr-24: 40.9%) | | | | | | |
| CAC B2C / SMB / Ent | **$392 / $759 / $4,249** | | | | | | |
| ARPA B2C / SMB / Ent | **$42.21 / $177.94 / $847.75** | | | | | | |
| LTV B2C / SMB / Ent | **$197 / $2,215 / $9,178** | | | | | | |
| LTV:CAC B2C / SMB / Ent | **0.50× / 2.92× / 2.16×** | | | | | | |
| Payback (months) B2C / SMB / Ent | **31.7 / 14.6 / 17.1** | | | | | | |
| Most expansion revenue | **SMB (4× Enterprise)** | | | | | | |
| Top churn indicator | **In-period engagement (active days / courses seen)** | | | | | | |
| Data issues spotted | **Marketing "new users" = sign-ups (~10× paying B2C); payments = list prices; 3 duplicate emails; Enterprise users > marketing's count** | | | | | | |

## Qualitative (1–5)
| Criterion | ChatGPT | Gemini | Other | Notes |
|---|---|---|---|---|
| Insight quality | | | | |
| Recommendations | | | | |
| Clarity | | | | |
| Handled the ambiguity (did it spot the sign-ups vs. payers issue, D-06?) | | | | |
| Errors found in *our* work | | | | |

## Critique round (prompt 3): scores given to our summary
| Criterion | ChatGPT | Gemini | Other |
|---|---|---|---|
| Analytical rigor (30%) | | | |
| Business acumen (25%) | | | |
| Communication (20%) | | | |
| Technical skill (15%) | | | |
| Creativity (10%) | | | |
| Top weakness cited | | | |
