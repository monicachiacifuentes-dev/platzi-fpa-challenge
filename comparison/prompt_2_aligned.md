# Prompt 2 — Aligned round
*(New chat. Attach the 7 CSVs. Paste everything below the line.)*

---

You are an FP&A analyst. Using the attached CSVs (Jan 2023 – Apr 2024), compute the metrics below **by running code**, using **ONLY these definitions**:

- **As-of date:** 2024-04-30. A subscription is **active on date D** if `start_date ≤ D < end_date`.
- **MRR** = the sum of `subscriptions.mrr` of active subscriptions (annual plans are already monthly-normalized). Don't use payments for MRR. **Segment** comes from `users.segment` via `user_id`; B2B = SMB + Enterprise. One `user_id` = one customer.
- **Q1-24 retention (renewal basis):** subscriptions with `end_date` between 2024-01-01 and 2024-03-31 → logo rate = renewed ÷ (renewed + churned). Dollar rate = Σ MRR of the *next* subscription of the renewed ones ÷ Σ MRR of all ended ones.
- **NDR T12M:** the customers active on 2023-04-30. NDR = their MRR on 2024-04-30 (0 if not active) ÷ their MRR on 2023-04-30. **GRR:** the same, but each customer's end MRR is capped at their start MRR. Expansion / contraction / churn = per-customer changes (Δ>0 / Δ<0 with end>0 / end=0).
- **New paying customers** = `users.csv` signups by month × segment. (Marketing's `new_users_acquired` is sign-ups: use it only for cost per sign-up.)
- **Fully loaded CAC (Nov-23..Apr-24):** (segment marketing spend incl. Sales Team + allocated G&A) ÷ new paying customers of the segment. G&A share to acquisition = total marketing ÷ (total marketing + total support costs) × total G&A, split across segments by share of marketing spend.
- **Gross margin:** revenue = monthly MRR; COGS = CS Salaries + Infrastructure + Content Production (allocated by MRR share, so the margin % is the same for every segment). Use the Nov-23..Apr-24 average.
- **ARPA** = MRR ÷ active customers (Nov-23..Apr-24 average). **Lifetime** = sum of the observed survival curve (share of customers still active k months after signup) with the tail extrapolated at the recent monthly churn, capped at 60 months. **LTV** = ARPA × GM% × lifetime. **Payback** = CAC ÷ (ARPA × GM%).

Return **only** this table, plus up to 5 bullets on anything that looks inconsistent:

| Metric | Value |
|---|---|
| MRR Apr-24 total | |
| MRR Apr-24 B2C / SMB / Enterprise | |
| Active subs Apr-24 total | |
| Active subs B2C m/a · SMB m/a · Ent m/a | |
| Q1-24 retention logo: total / B2C / B2B | |
| Q1-24 retention $: total / B2C / B2B | |
| NDR T12M: total / B2C / SMB / Enterprise | |
| GRR T12M total | |
| NDR base: # customers, start MRR | |
| Expansion $ / contraction $ / churn $ (T12M, total) | |
| GM% (Nov-23..Apr-24 avg) | |
| CAC: B2C / SMB / Enterprise | |
| ARPA: B2C / SMB / Enterprise | |
| LTV: B2C / SMB / Enterprise | |
| LTV:CAC: B2C / SMB / Enterprise | |
| Payback (months): B2C / SMB / Enterprise | |
