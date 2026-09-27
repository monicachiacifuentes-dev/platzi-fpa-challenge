# WP50 — Final QA (2026-09-27)

## Answer
All automated checks pass across every deliverable: **130 checks, 0 failures**.

| Layer | Check | Result |
|---|---|---|
| SQL pipeline (`sql/run_pipeline.py`) | Row counts, keys, referential integrity, MRR bridge identity, NDR identities, Q1/Q3 totals, analysis marts, scenario ordering/backtest | **31/31 PASS** |
| Financial model (`work/WP40_model/verify_model.py`) | Formula engine recomputes the workbook; Q1/Q3, bridge identity (80 rows), CAC/LTV/GM/ARPA vs. db, scenario reconciliation (D-20) | **46/46 PASS**, master cell TRUE |
| Streamlit (`app/test_app.py`) | Loads, every filter/toggle, KPI values, per-segment reconciliation | **9/9 PASS** |
| Executive summary (`work/WP50_qa/check_summary_numbers.py`) | 44 figures quoted in the summary, recomputed from the db and found verbatim in the text | **44/44 PASS** |
| BigQuery | Apr-24 MRR recomputed in BigQuery from the raw tables = 204,709.09 / 1,941 | PASS |
| PDF | Page count ≤ 2 | 2 pages |

## Corrections made during QA
- The summary said revenue grew "28×" Jan-23→Apr-24. The exact figure is 28.6×, so it now reads **29×**.
- Strategy 2's 6-month impact said "−$0.9k". The exact figure is −$849.64, so it now reads **−$0.8k**.
- Both fixes are in the HTML, and the PDF was regenerated.

## Plan §4 QA checklist
- [x] Row counts match `Docs/Datasets.md`
- [x] Apr-24 MRR is the same in the summary, model, dashboard, scenario M0 and BigQuery
- [x] MRR bridge identity holds every month × segment
- [x] NDR identity; GRR ≤ 100%; NDR ≥ GRR
- [x] Active subs sum to 1,941
- [x] Assumptions in the workbook are logged in Plan §2 (A-01..A-23, D-05..D-20)
- [x] Summary ≤ 2 pages; every quoted number is traceable to the db
- [x] Model: inputs in blue, formulas visible (WP40 conventions; verified by recomputation)

## Open items (not QA failures)
- The "[Candidate name]" placeholder in the summary is for the user to replace.
- Looker Studio dashboard: built by the user from `outputs/Looker_Studio_Guide.md`.
- BigQuery Sandbox tables expire 60 days after loading.

## Files
`work/WP50_qa/{pipeline.log, model_build.log, model_verify.log, summary_numbers.log, check_summary_numbers.py}`
