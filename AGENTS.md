# AGENTS.md — Platzi FP&A Take-Home Challenge

Entry point for any AI agent (Claude Code, Codex, ChatGPT, Gemini, Cursor, …) working in this folder.

## Context
A candidate for a Financial Planner / FP&A role at Platzi (EdTech, B2C + B2B subscriptions) is solving a take-home test. Deliverables: Excel financial model, 1–2 page executive summary, charts, plus bonus work (SQL, scenarios, churn model, dashboard).

## Read in this order (Markdown copies save tokens; don't re-parse the PDF)
1. `Docs/Plan_and_Index.md` — **master plan**: metric definitions (M-xx), decisions (D-xx), work packages (WPxx), status board, AI comparison protocol
2. `Docs/FP_A_Take_Home_Test_Platzi.md` — full challenge brief
3. `Docs/Datasets.md` — data dictionary, profiles, known data issues
4. `Docs/Deliverables_Framework.md` — deliverable specs, grading map, bonus plan

## Rules
- Raw data lives in `Docs/Originals/` and is **read-only**. Compute from the CSVs, not from the Markdown summaries.
- Use the metric definitions in `Docs/Plan_and_Index.md` §1. Put alternatives in as sensitivities, never silently.
- Each work package writes to `work/WPxx_<name>/results.md` using the template in the plan §4, then updates the status board (§0).
- Every new assumption goes in the decisions log (§2) with an ID.
- Numbers first, then method, then assumptions. The audience is a non-finance CEO/CFO.
- Output language: English (the brief is in English).
