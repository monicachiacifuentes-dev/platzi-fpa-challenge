"""WP41 - Executive-summary charts, built straight from db/platzi.duckdb.

Run: .venv/Scripts/python.exe work/WP41_charts/make_charts.py
Writes PNG (for the PDF) and SVG to outputs/charts/, plus chart_data.json with every
plotted number (the table view / source for the summary text).
"""
import json
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "charts"
OUT.mkdir(parents=True, exist_ok=True)
con = duckdb.connect(str(ROOT / "db" / "platzi.duckdb"), read_only=True)
q = lambda sql: con.sql(sql).df()

# Reference palette (dataviz skill, light mode). Segment identity is fixed across every chart.
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SEG = {"B2C": "#2a78d6", "SMB": "#eb6834", "Enterprise": "#1baf7a"}
BLUE_LIGHT, BLUE, BLUE_DARK = "#86b6ef", "#2a78d6", "#104281"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 9,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": AXIS, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})
kfmt = FuncFormatter(lambda v, _: f"${v/1000:,.0f}k")
data = {}


def style(ax, title, subtitle=None):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.set_title(title, loc="left", fontsize=10.5, fontweight="bold", color=INK, pad=18 if subtitle else 8)
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=8.5, color=INK2)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.png", dpi=200)
    fig.savefig(OUT / f"{name}.svg")
    plt.close(fig)


# ---------------------------------------------------------------- C1 MRR by segment (actuals)
mrr = q("""select strftime(month_end,'%Y-%m') m, segment, closing_mrr from mart_mrr_bridge
           where segment in ('B2C','SMB','Enterprise') order by 1""")
piv = mrr.pivot(index="m", columns="segment", values="closing_mrr")[["B2C", "SMB", "Enterprise"]].fillna(0)
data["c1_mrr_by_segment"] = piv.round(2).reset_index().to_dict(orient="records")
fig, ax = plt.subplots(figsize=(4.6, 2.9))
x = range(len(piv))
bottom = [0.0] * len(piv)
for seg in piv.columns:
    ax.bar(x, piv[seg], bottom=bottom, width=0.72, color=SEG[seg], label=seg, edgecolor=SURFACE, linewidth=1)
    bottom = [b + v for b, v in zip(bottom, piv[seg])]
labels = [m[2:4] + "-" + m[5:] if m.endswith(("01", "04", "07", "10")) else "" for m in piv.index]
ax.set_xticks(list(x), [f"{['','Jan','','','Apr','','','Jul','','','Oct','',''][int(m[5:])]} {m[2:4]}" if l else "" for m, l in zip(piv.index, labels)])
ax.yaxis.set_major_formatter(kfmt)
ax.annotate(f"${bottom[-1]/1000:,.1f}k", (len(piv) - 1, bottom[-1]), xytext=(0, 3),
            textcoords="offset points", ha="center", fontsize=8.5, color=INK, fontweight="bold")
ax.legend(loc="upper left", frameon=False, fontsize=8, ncol=3)
style(ax, "MRR by segment, Jan-23 to Apr-24", "B2B (SMB + Enterprise) is 69% of MRR from 21% of subscribers")
ax.set_ylim(0, bottom[-1] * 1.18)
save(fig, "c1_mrr_by_segment")

# ---------------------------------------------------------------- C2 scenarios (actual + 12-mo projection)
act = q("""select month_end, closing_mrr from mart_mrr_bridge where segment='Total' order by 1""")
proj = q("""select scenario, month_end, closing_mrr from mart_s_02_projection_monthly
            where segment='Total' and plan_type='ALL' order by 1,2""")
data["c2_scenarios"] = {
    "actual": [[str(d.date()), round(v, 2)] for d, v in zip(act.month_end, act.closing_mrr)],
    "projection": {s: [[str(d.date()), round(v, 2)] for d, v in zip(g.month_end, g.closing_mrr)]
                   for s, g in proj.groupby("scenario")},
}
fig, ax = plt.subplots(figsize=(4.6, 2.9))
ax.plot(act.month_end, act.closing_mrr, color=INK, linewidth=2, label="Actual")
last_d, last_v = act.month_end.iloc[-1], act.closing_mrr.iloc[-1]
for scen, col in (("bear", BLUE_LIGHT), ("base", BLUE), ("bull", BLUE_DARK)):
    g = proj[proj.scenario == scen]
    xs = [last_d] + list(g.month_end)
    ys = [last_v] + list(g.closing_mrr)
    ax.plot(xs, ys, color=col, linewidth=2, label=scen.capitalize())
    ax.annotate(f"{scen.capitalize()} ${ys[-1]/1000:,.0f}k", (xs[-1], ys[-1]), xytext=(4, 0),
                textcoords="offset points", va="center", fontsize=8, color=INK2)
ax.axvline(last_d, color=AXIS, linewidth=0.8)
ax.text(last_d, ax.get_ylim()[1] * 0.02, " forecast →", fontsize=7.5, color=MUTED, va="bottom")
ax.yaxis.set_major_formatter(kfmt)
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y"))
ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator(bymonth=(1, 7)))
ax.legend(loc="upper left", frameon=False, fontsize=8, ncol=4)
ax.set_xlim(act.month_end.iloc[0], proj.month_end.max() + (proj.month_end.max() - last_d) * 0.35)
style(ax, "MRR outlook to Apr-25", "Base case: flat acquisition at the last-6-month average")
ax.set_ylim(0, proj.closing_mrr.max() * 1.15)
save(fig, "c2_scenarios")

# ---------------------------------------------------------------- C3 churn vs in-period engagement
eng = q("""select case when active_days<=3 then '1-3' when active_days<=6 then '4-6'
                       when active_days<=9 then '7-9' when active_days<=12 then '10-12'
                       else '13+' end bucket, min(active_days) o, count(*) n,
                  avg(case when status='churned' then 1.0 else 0 end) churn
           from fct_subscriptions where status in ('renewed','churned') group by 1 order by o""")
data["c3_churn_by_active_days"] = eng[["bucket", "n", "churn"]].round(4).to_dict(orient="records")
fig, ax = plt.subplots(figsize=(4.6, 2.9))
bars = ax.bar(eng.bucket, eng.churn * 100, width=0.6, color=BLUE)
for b, v, n in zip(bars, eng.churn * 100, eng.n):
    ax.annotate(f"{v:.0f}%", (b.get_x() + b.get_width() / 2, v), xytext=(0, 3),
                textcoords="offset points", ha="center", fontsize=8.5, color=INK)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.set_xlabel("Active days in the billing period")
ax.set_ylim(0, 112)
ax.set_yticks([0, 25, 50, 75, 100])
style(ax, "Churn rate by in-period engagement", "Share of billing periods that ended in churn")
save(fig, "c3_churn_by_engagement")

# ---------------------------------------------------------------- C4 LTV:CAC by segment, two margin bases
ue = q("""select segment, ltv_base, cac_fully_loaded_t6m cac, gm_pct_t6m_base gm from mart_a2_12_unit_economics_summary
          where segment in ('B2C','SMB','Enterprise')""").set_index("segment").loc[["B2C", "SMB", "Enterprise"]]
gm_now = q("""with r as (select sum(mrr) rev from fct_customer_mrr_monthly where month_end=date '2024-04-30'),
                   k as (select sum(amount) cogs from stg_support_costs
                         where month=date '2024-04-01' and category<>'G&A')
              select 1-cogs/rev from r, k""").iloc[0, 0]
ue["ratio_t6m"] = ue.ltv_base / ue.cac
ue["ratio_runrate"] = ue.ltv_base * (gm_now / ue.gm) / ue.cac
data["c4_ltv_cac"] = {"gm_t6m": round(float(ue.gm.iloc[0]), 4), "gm_apr24": round(float(gm_now), 4),
                      "rows": ue[["cac", "ltv_base", "ratio_t6m", "ratio_runrate"]].round(3).reset_index().to_dict(orient="records")}
fig, ax = plt.subplots(figsize=(4.6, 2.9))
w = 0.34
xs = range(len(ue))
b1 = ax.bar([i - w / 2 - 0.01 for i in xs], ue.ratio_t6m, width=w, color=BLUE_LIGHT, label=f"Margin last 6 mo ({ue.gm.iloc[0]:.0%})")
b2 = ax.bar([i + w / 2 + 0.01 for i in xs], ue.ratio_runrate, width=w, color=BLUE_DARK, label=f"Margin Apr-24 ({gm_now:.0%})")
for bs in (b1, b2):
    for b in bs:
        ax.annotate(f"{b.get_height():.1f}×", (b.get_x() + b.get_width() / 2, b.get_height()), xytext=(0, 3),
                    textcoords="offset points", ha="center", fontsize=8, color=INK)
ax.axhline(3, color=INK2, linewidth=1)
ax.text(-0.45, 3.06, "3× benchmark", fontsize=7.5, color=INK2, va="bottom", ha="left")
ax.set_xticks(list(xs), ue.index)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}×"))
ax.set_ylim(0, max(ue.ratio_runrate.max(), 3) * 1.3)
ax.legend(loc="upper left", frameon=False, fontsize=8)
style(ax, "LTV : CAC by segment", "Fully loaded CAC; lifetime capped at 60 months")
save(fig, "c4_ltv_cac")

(OUT / "chart_data.json").write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")
print("charts written to", OUT)
