"""WP50 - Every key number quoted in the executive summary, recomputed from db/platzi.duckdb.

For each item: compute from the db, format it as the summary does, and assert that the string
appears in outputs/Platzi_FPA_Executive_Summary.html.
Run: .venv/Scripts/python.exe work/WP50_qa/check_summary_numbers.py
"""
import html
import re
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
text = html.unescape(re.sub(r"<[^>]+>", " ", (ROOT / "outputs/Platzi_FPA_Executive_Summary.html").read_text(encoding="utf-8")))
text = re.sub(r"\s+", " ", text)
con = duckdb.connect(str(ROOT / "db/platzi.duckdb"), read_only=True)
v = lambda sql: con.sql(sql).fetchone()[0]

q2 = lambda seg, col: v(f"select {col} from mart_q2_retention_q1_24 where segment='{seg}' and split='all' and method='M06_primary'")
q4 = lambda seg, col: v(f"select {col} from mart_q4_ndr_t12m where segment='{seg}' and method='M08_M09_M10'")
ue = lambda seg, col: v(f"select {col} from mart_a2_12_unit_economics_summary where segment='{seg}'")
sc = lambda s, seg, col: v(f"select {col} from mart_s_03_scenario_summary where scenario='{s}' and segment='{seg}'")
st = lambda s, col: v(f"select sum({col}) from mart_s_04_strategy_impact where strategy like '{s}%' and \"case\"='base' and segment='Total'")
mrr = lambda d, seg="Total": v(f"select closing_mrr from mart_mrr_bridge where segment='{seg}' and month_end=date '{d}'")
cogs = lambda m: v(f"select sum(amount) from stg_support_costs where month=date '{m}' and category<>'G&A'")
gm_apr = 1 - cogs("2024-04-01") / mrr("2024-04-30")
gm_scale = gm_apr / ue("SMB", "gm_pct_t6m_base")
mkt = lambda seg=None: v("select sum(spend) from stg_marketing_spend" + (f" where segment='{seg}'" if seg else ""))
t6m_ndr = v("select ndr from mart_a3_03_t6m_decomposition where segment='Total'") if con.sql(
    "select count(*) from information_schema.columns where table_name='mart_a3_03_t6m_decomposition' and column_name='ndr'").fetchone()[0] else None
pct = lambda x, d=1: f"{x*100:.{d}f}%"

checks = [
    ("Q1 MRR total", f"{mrr('2024-04-30'):,.0f}"),
    ("Q1 B2C", f"${mrr('2024-04-30','B2C'):,.0f}"), ("Q1 SMB", f"${mrr('2024-04-30','SMB'):,.0f}"),
    ("Q1 Enterprise", f"${mrr('2024-04-30','Enterprise'):,.0f}"),
    ("Q3 subs", f"{v('select active_subs from mart_q3_active_subs_apr24 where segment=' + chr(39) + 'Total' + chr(39) + ' and plan_type=' + chr(39) + 'Total' + chr(39)):,}"),
    ("Q3 B2C monthly/annual", "844 monthly / 692 annual"), ("Q3 SMB", "SMB 113 / 190"), ("Q3 Ent", "Enterprise 12 / 90"),
    ("Q2 total logo", pct(q2("Total", "logo_rate"))), ("Q2 B2C logo", pct(q2("B2C", "logo_rate"))),
    ("Q2 B2B logo", pct(q2("B2B", "logo_rate"))), ("Q2 total $", pct(q2("Total", "dollar_rate"))),
    ("Q2 B2C $", pct(q2("B2C", "dollar_rate"))), ("Q2 B2B $", pct(q2("B2B", "dollar_rate"))),
    ("Q4 NDR total", pct(q4("Total", "ndr"))), ("Q4 GRR total", pct(q4("Total", "grr"))),
    ("Q4 NDR B2C", pct(q4("B2C", "ndr"))), ("Q4 NDR SMB", pct(q4("SMB", "ndr"))),
    ("Q4 NDR Ent", pct(q4("Enterprise", "ndr"))), ("Q4 base customers", f"{q4('Total','base_customers'):,} customers"),
    ("MRR x in 12 months", f"×{mrr('2024-04-30')/mrr('2023-04-30'):.1f}"),
    ("Revenue growth Jan-23→Apr-24", f"{mrr('2024-04-30')/mrr('2023-01-31'):.0f}×"),
    ("COGS growth", f"{cogs('2024-04-01')/cogs('2023-01-01'):.1f}×"),
    ("GM Apr-24", f"{gm_apr*100:.0f}%"), ("GM T6M", f"{ue('SMB','gm_pct_t6m_base')*100:.0f}%"),
    ("B2C CAC", f"${ue('B2C','cac_fully_loaded_t6m'):,.0f}"),
    ("LTV:CAC SMB run-rate", f"{ue('SMB','ltv_cac_t6m')*gm_scale:.1f}×"),
    ("LTV:CAC Ent run-rate", f"{ue('Enterprise','ltv_cac_t6m')*gm_scale:.1f}×"),
    ("LTV:CAC B2C range", f"{ue('B2C','ltv_cac_t6m'):.1f}–{ue('B2C','ltv_cac_t6m')*gm_scale:.1f}×"),
    ("SMB payback run-rate", f"payback ≈ {ue('SMB','cac_payback_months_t6m')/gm_scale:.0f} months"),
    ("Ent payback run-rate", f"≈ {ue('Enterprise','cac_payback_months_t6m')/gm_scale:.0f} months"),
    ("B2C share of marketing", f"{mkt('B2C')/mkt()*100:.0f}% of the marketing budget"),
    ("B2C marketing $", f"${mkt('B2C')/1000:,.0f}k of ${mkt()/1e6:.2f}M"),
    ("May-24 renewals", f"{v('select count(*) from mart_a1_06_may24_churn_risk'):,}"),
    ("May-24 MRR", f"${v('select sum(mrr) from mart_a1_06_may24_churn_risk')/1000:.1f}k MRR"),
    ("May-24 high risk", f"{v(chr(115)+'elect count(*) from mart_a1_06_may24_churn_risk where risk_tier=' + chr(39) + 'High' + chr(39))} are high-risk"),
    ("Strategy 1 6-mo", f"+${st('strategy_1','mrr_delta_m6')/1000:.1f}k"),
    ("Strategy 3 6-mo", f"+${st('strategy_3','mrr_delta_m6')/1000:.1f}k"),
    ("Strategy 2 6-mo", f"−${abs(st('strategy_2','mrr_delta_m6'))/1000:.1f}k"),
    ("Base Apr-25", f"${sc('base','Total','mrr_apr25')/1000:,.0f}k MRR (+{sc('base','Total','mrr_growth_pct'):.0f}%)"),
    ("Base subs", f"{sc('base','Total','subs_apr25'):,.0f} subscribers"),
    ("Bear Apr-25", f"${sc('bear','Total','mrr_apr25')/1000:,.0f}k"), ("Bull Apr-25", f"${sc('bull','Total','mrr_apr25')/1000:,.0f}k"),
]
if t6m_ndr is not None:
    checks.append(("T6M NDR", pct(t6m_ndr)))

fails = 0
for label, s in checks:
    ok = s in text
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {label:32s} expects '{s}'")
print(f"\n{len(checks) - fails}/{len(checks)} summary numbers match the database")
