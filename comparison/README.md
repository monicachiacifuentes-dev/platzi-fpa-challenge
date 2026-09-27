# AI tool comparison (WP51): how to run it

Goal: use ChatGPT, Gemini (and optionally Copilot / Claude.ai) as **independent auditors** of our numbers and recommendations.
Agreement → confidence. Disagreement → find out why (a definition choice or a bug) and document it.

## Files to attach (all rounds)
From `Docs/Originals/`: `users.csv`, `subscriptions.csv`, `payments.csv`, `payment_gateways.csv`, `engagement.csv`, `marketing_spend.csv`, `support_costs.csv`, plus the brief `FP_A_Take_Home_Test_Platzi__3___1___1_.pdf`.
(The data is simulated, with no real personal data. Still, check that the recruiter's terms allow sharing it.)

Use a tool mode that **runs code on files** (ChatGPT: GPT with data analysis/code; Gemini: Advanced with file upload). Otherwise it will guess numbers.

## Rounds
| Round | File | What to paste | Why |
|---|---|---|---|
| 1 Blind | `prompt_1_blind.md` | Brief + CSVs only | See how others interpret the ambiguities (the recruiter may think the same way) |
| 2 Aligned | `prompt_2_aligned.md` | + our metric definitions | Results should match ours; a gap = a bug on one side |
| 3 Critique | `prompt_3_critique.md` | + our summary PDF | Get a tough reviewer's feedback on the story and recommendations |

Start a **new chat for each round and each tool**, so earlier answers don't leak into the next round.

## After each run
1. Copy the tool's results table into `scorecard.md`, in the matching column.
2. For any difference > 1 pp or > 2%, note the cause in the "Δ explained by" column (a definition, a data filter, an error).
3. Save the full answers as `answers/<tool>_<round>.md` (for the record).
4. Paste good ideas we don't have into `ideas.md`.

Then tell Claude "comparison done". It will review the scorecard and propose any changes to the deliverables.
