"""
WP33 -- Platzi FP&A executive dashboard (Streamlit, bonus B4).

Data source: outputs/marts/*.csv (exported by sql/run_pipeline.py). This app is
READ-ONLY against those CSVs -- it never touches db/platzi.duckdb and never
writes anywhere except the in-memory session. All figures must reconcile to
outputs/Platzi_FPA_Executive_Summary.html; see work/WP33_dashboard/results.md
for the reconciliation table.

Run locally:
    .venv/Scripts/streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parents[1]
MARTS = ROOT / "outputs" / "marts"
SCENARIOS_DIR = ROOT / "sql" / "python_models"

# --------------------------------------------------------------------------- palette
# Fixed everywhere in the app -- must match work/WP41_charts/make_charts.py.
SEG_COLOR = {"B2C": "#2a78d6", "SMB": "#eb6834", "Enterprise": "#1baf7a"}
BLUE_LIGHT, BLUE, BLUE_DARK = "#86b6ef", "#2a78d6", "#104281"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
MOVE_COLOR = {"New": "#2a78d6", "Expansion": "#1baf7a", "Contraction": "#eb6834", "Churn": "#8c2f24"}
TIER_COLOR = {"High": "#8c2f24", "Medium": "#eb6834", "Low": "#898781"}

st.set_page_config(page_title="Platzi FP&A Dashboard", page_icon="\U0001F4C8", layout="wide")

BASE_LAYOUT = dict(
    plot_bgcolor=SURFACE, paper_bgcolor=SURFACE,
    font=dict(family="Segoe UI, -apple-system, sans-serif", color=INK, size=13),
    margin=dict(l=10, r=10, t=50, b=10),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
)


def style_axes(fig, yfmt=None, showlegend=True):
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=GRID)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, tickformat=yfmt)
    fig.update_layout(**BASE_LAYOUT, showlegend=showlegend)
    return fig


# --------------------------------------------------------------------------- data loading
@st.cache_data
def load_mart(name: str) -> pd.DataFrame:
    return pd.read_csv(MARTS / f"{name}.csv")


@st.cache_data
def load_mart_dates(name: str, date_cols: tuple[str, ...]) -> pd.DataFrame:
    df = pd.read_csv(MARTS / f"{name}.csv")
    for c in date_cols:
        df[c] = pd.to_datetime(df[c])
    return df


SEGMENTS = ["All", "B2C", "SMB", "Enterprise"]


def seg_key(choice: str) -> str:
    return "Total" if choice == "All" else choice


def fmt_money(x: float, decimals: int = 0) -> str:
    return f"${x:,.{decimals}f}"


def fmt_pct(x: float, decimals: int = 1) -> str:
    return f"{x * 100:,.{decimals}f}%"


# =============================================================================
# Sidebar
# =============================================================================
st.sidebar.title("Filters")
segment_choice = st.sidebar.radio("Segment", SEGMENTS, index=0, help="Scopes every chart and table on the page.")
SEG = seg_key(segment_choice)
st.sidebar.caption(
    "Data: `outputs/marts/*.csv` (DuckDB pipeline, WP30). "
    "Numbers reconcile to `outputs/Platzi_FPA_Executive_Summary.html`."
)
st.sidebar.markdown("---")
st.sidebar.caption(
    "Built for the Platzi FP&A take-home challenge (WP33, bonus B4). "
    "See `work/WP33_dashboard/results.md` for method and limitations."
)

# =============================================================================
# Header
# =============================================================================
st.title("Platzi FP&A Executive Dashboard")
st.caption(
    "Data window: **Jan 2023 - Apr 2024** (16 months) &nbsp;|&nbsp; "
    f"Segment: **{segment_choice}** &nbsp;|&nbsp; "
    "All datasets are **simulated** for this take-home exercise -- treat every number as illustrative, not real Platzi data."
)

tab_overview, tab_retention, tab_unit_econ, tab_churn_risk, tab_scenarios = st.tabs(
    ["Overview", "Retention", "Unit economics", "Churn risk (May-24)", "Scenarios & strategies"]
)

# =============================================================================
# TAB 1 -- Overview
# =============================================================================
with tab_overview:
    bridge = load_mart_dates("mart_mrr_bridge", ("month_end",))
    q3 = load_mart("mart_q3_active_subs_apr24")
    q2 = load_mart("mart_q2_retention_q1_24")
    q4 = load_mart("mart_q4_ndr_t12m")
    a303 = load_mart("mart_a3_03_t6m_decomposition")
    gm = load_mart_dates("mart_a2_08_gm_monthly", ("month",))

    apr24 = pd.Timestamp("2024-04-30")
    mrr_apr24 = bridge.loc[(bridge.month_end == apr24) & (bridge.segment == SEG), "closing_mrr"].iloc[0]
    subs_apr24 = q3.loc[(q3.segment == SEG) & (q3.plan_type == "Total"), "active_subs"].iloc[0]
    ret_row = q2.loc[(q2.segment == SEG) & (q2.split == "all") & (q2.method == "M06_primary")].iloc[0]
    ndr_row = q4.loc[(q4.segment == SEG) & (q4.method == "M08_M09_M10")].iloc[0]
    ndr_t6m = a303.loc[a303.segment == SEG, "ndr"].iloc[0]
    gm_row = gm.loc[(gm.month == apr24) & (gm.segment == SEG)].iloc[0]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(f"MRR, Apr-24 ({segment_choice})", fmt_money(mrr_apr24))
    c2.metric("Active subscriptions", f"{int(subs_apr24):,}")
    c3.metric(
        "Q1-24 retention (logo)", fmt_pct(ret_row.logo_rate),
        help=f"$ basis: {fmt_pct(ret_row.dollar_rate)}. Renewal-event basis (M-06): renewed / (renewed + churned).",
    )
    c4.metric(
        "NDR, trailing 12 mo", fmt_pct(ndr_row.ndr),
        help=f"Trailing 6 mo: {fmt_pct(ndr_t6m)}. M-08: MRR now / MRR 12 months ago, fixed customer base.",
    )
    c5.metric(
        "Gross margin, Apr-24", fmt_pct(gm_row.gm_pct_base),
        help="COGS allocated by MRR share (D-07/A-03) -> uniform % across segments by design.",
    )
    st.caption(
        "How to read: KPI tiles are scoped to the sidebar segment filter. "
        "GM% is uniform across segments because COGS is allocated by share of MRR (D-07), not by segment cost drivers."
    )

    st.markdown("### MRR by segment")
    b_seg = bridge[bridge.segment.isin(["B2C", "SMB", "Enterprise"])].copy()
    if SEG != "Total":
        b_seg = b_seg[b_seg.segment == SEG]
    piv = b_seg.pivot(index="month_end", columns="segment", values="closing_mrr").fillna(0)
    piv = piv[[c for c in ["B2C", "SMB", "Enterprise"] if c in piv.columns]]
    fig = go.Figure()
    for seg in piv.columns:
        fig.add_bar(x=piv.index, y=piv[seg], name=seg, marker_color=SEG_COLOR[seg])
    fig.update_layout(barmode="stack", title="MRR by segment, monthly (stacked)")
    style_axes(fig, yfmt="$,.0f", showlegend=len(piv.columns) > 1)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "How to read: each bar is total MRR at month-end; colors are fixed segment identities "
        "(B2C blue, SMB orange, Enterprise green) used consistently across every tab."
    )
    with st.expander("Data table"):
        st.dataframe(piv.reset_index().assign(month_end=lambda d: d.month_end.dt.strftime("%Y-%m")), use_container_width=True)

    st.markdown("### MRR bridge (new / expansion / contraction / churn)")
    br = bridge[bridge.segment == SEG].sort_values("month_end").copy()
    fig2 = go.Figure()
    fig2.add_bar(x=br.month_end, y=br.new_mrr.fillna(0), name="New", marker_color=MOVE_COLOR["New"])
    fig2.add_bar(x=br.month_end, y=br.expansion_mrr.fillna(0), name="Expansion", marker_color=MOVE_COLOR["Expansion"])
    fig2.add_bar(x=br.month_end, y=-br.contraction_mrr.fillna(0), name="Contraction", marker_color=MOVE_COLOR["Contraction"])
    fig2.add_bar(x=br.month_end, y=-br.churn_mrr.fillna(0), name="Churn", marker_color=MOVE_COLOR["Churn"])
    fig2.add_trace(go.Scatter(x=br.month_end, y=br.closing_mrr, mode="lines", name="Closing MRR",
                               line=dict(color=INK, width=2)))
    fig2.update_layout(barmode="relative", title=f"MRR bridge by month -- {segment_choice}")
    style_axes(fig2, yfmt="$,.0f")
    st.plotly_chart(fig2, use_container_width=True)
    st.caption(
        "How to read: stacked bars are the monthly $ movement (new + expansion above zero, "
        "contraction + churn below); the black line is closing MRR. Opening + New + Expansion "
        "- Contraction - Churn = Closing MRR every month (tested in `sql/tests/`)."
    )
    with st.expander("Data table"):
        st.dataframe(
            br[["month_end", "opening_mrr", "new_mrr", "expansion_mrr", "contraction_mrr", "churn_mrr", "closing_mrr"]]
            .assign(month_end=lambda d: d.month_end.dt.strftime("%Y-%m")),
            use_container_width=True,
        )

# =============================================================================
# TAB 2 -- Retention
# =============================================================================
with tab_retention:
    st.markdown("### Cohort retention heatmap")
    cohort_group = {"Total": "Total", "B2C": "B2C", "SMB": "B2B", "Enterprise": "B2B"}[SEG]
    if SEG in ("SMB", "Enterprise"):
        st.info(
            f"Cohort retention is only tracked at B2C vs. B2B granularity in the data model "
            f"(mart_a1_01_cohort_retention has no SMB/Enterprise split) -- showing the **B2B** cohort matrix.",
            icon="ℹ️",
        )
    dollar_toggle = st.toggle("Show $ (dollar) retention instead of logo retention", value=False, key="cohort_toggle")
    a101 = load_mart("mart_a1_01_cohort_retention")
    cg = a101[a101.segment_group == cohort_group].copy()
    metric_col = "dollar_retention" if dollar_toggle else "logo_retention"
    heat = cg.pivot(index="cohort_month", columns="month_k", values=metric_col)
    heat = heat.sort_index()
    fig = go.Figure(
        data=go.Heatmap(
            z=heat.values * 100,
            x=[f"M{k}" for k in heat.columns],
            y=heat.index,
            colorscale=[[0, "#eef4fc"], [0.5, BLUE], [1, BLUE_DARK]],
            zmin=0, zmax=100,
            colorbar=dict(title="%", ticksuffix="%"),
            hovertemplate="Cohort %{y}<br>Month %{x}<br>Retention %{z:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(title=f"{'Dollar' if dollar_toggle else 'Logo'} retention by signup cohort -- {cohort_group}",
                       yaxis=dict(autorange="reversed"))
    style_axes(fig, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "How to read: each row is a signup-month cohort; each column is months since signup. "
        "Darker = more of the cohort's logos (or $) retained. Blank cells = cohort hasn't reached that age yet."
    )
    with st.expander("Data table"):
        st.dataframe((heat * 100).round(1), use_container_width=True)

    st.markdown("### NDR waterfall")
    window_toggle = st.toggle("Show T6M instead of T12M", value=False, key="ndr_window_toggle")
    wf_name = "mart_a3_04_t6m_waterfall_long" if window_toggle else "mart_a3_02_t12m_waterfall_long"
    wf = load_mart(wf_name)
    wf_seg = wf[wf.segment == SEG].sort_values("step_order")
    measures = ["absolute"] + ["relative"] * (len(wf_seg) - 2) + ["total"]
    fig = go.Figure(
        go.Waterfall(
            x=wf_seg.step, y=wf_seg.amount, measure=measures,
            increasing=dict(marker_color=SEG_COLOR.get("Enterprise", "#1baf7a")),
            decreasing=dict(marker_color=MOVE_COLOR["Churn"]),
            totals=dict(marker_color=INK),
            connector=dict(line=dict(color=GRID)),
            texttemplate="%{y:$,.0f}", textposition="outside",
        )
    )
    window_label = "T6M" if window_toggle else "T12M"
    fig.update_layout(title=f"NDR waterfall, {window_label} -- {segment_choice}")
    style_axes(fig, yfmt="$,.0f", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    ndr_val = wf_seg.loc[wf_seg.step == "End MRR", "amount"].iloc[0] / wf_seg.loc[wf_seg.step == "Start MRR", "amount"].iloc[0]
    st.caption(
        f"How to read: waterfall from Start MRR to End MRR for the fixed cohort of customers active at the "
        f"start of the window. NDR = End / Start = {fmt_pct(ndr_val)}. Green = expansion, red = churn/contraction, "
        f"gray = totals."
    )
    with st.expander("Data table"):
        st.dataframe(wf_seg[["step", "amount"]], use_container_width=True)

    st.markdown("### Churn rate by in-period engagement")
    base = load_mart("mart_a1_03_churn_indicators_base")
    bdf = base if SEG == "Total" else base[base.segment == SEG]
    order = ["0-5", "6-10", "11-15", "16-20", "21-25", "26-28"]
    g = bdf.groupby("active_days_bucket").agg(n=("churned", "size"), churn_rate=("churned", "mean")).reindex(order).dropna()
    fig = go.Figure(go.Bar(x=g.index, y=g.churn_rate * 100, marker_color=BLUE,
                            text=[f"{v:.0f}%" for v in g.churn_rate * 100], textposition="outside"))
    fig.update_layout(title=f"Churn rate by active days in the billing period -- {segment_choice}")
    fig.update_xaxes(title="Active days in the period")
    style_axes(fig, showlegend=False)
    fig.update_yaxes(tickformat=".0f", ticksuffix="%", range=[0, 110])
    st.plotly_chart(fig, use_container_width=True)
    st.warning(
        "Simulated-data caveat (D-18): same-period engagement almost perfectly separates churn here "
        "(an artifact of how the dataset was generated). Treat this as an **in-period early-warning "
        "signal**, not a production-grade model -- expect real-world AUC around 0.70-0.85, far below "
        "what this chart implies. Previous-period engagement carries no signal.",
        icon="⚠️",
    )
    with st.expander("Data table"):
        st.dataframe(g.reset_index().assign(churn_rate=lambda d: (d.churn_rate * 100).round(1)), use_container_width=True)

# =============================================================================
# TAB 3 -- Unit economics
# =============================================================================
with tab_unit_econ:
    ue = load_mart("mart_a2_12_unit_economics_summary")
    ue = ue[ue.segment.isin(["B2C", "SMB", "Enterprise"])].set_index("segment")
    gm_apr24 = load_mart_dates("mart_a2_08_gm_monthly", ("month",))
    gm_now = gm_apr24.loc[(gm_apr24.month == pd.Timestamp("2024-04-30")) & (gm_apr24.segment == "Total"), "gm_pct_base"].iloc[0]
    ue_view = ue if SEG == "Total" else ue.loc[[SEG]]

    st.markdown("### LTV : CAC by segment")
    gm_basis = st.radio(
        "Gross margin basis", ["Trailing 6 months (29.3%, base/conservative)", "Apr-24 run-rate (40.9%, D-17 sensitivity)"],
        horizontal=True, key="gm_basis",
    )
    use_runrate = gm_basis.startswith("Apr-24")
    gm_t6m = ue.gm_pct_t6m_base.iloc[0]
    ratio = ue_view.ltv_base / ue_view.cac_fully_loaded_t6m
    if use_runrate:
        ratio = ratio * (gm_now / gm_t6m)
    fig = go.Figure()
    for seg in ue_view.index:
        fig.add_bar(x=[seg], y=[ratio.loc[seg]], name=seg, marker_color=SEG_COLOR[seg], showlegend=False,
                    text=f"{ratio.loc[seg]:.1f}x", textposition="outside")
    fig.add_hline(y=3, line_dash="dash", line_color=INK2, annotation_text="3x benchmark", annotation_position="top left")
    fig.update_layout(title=f"LTV : CAC ({'Apr-24 run-rate' if use_runrate else 'trailing 6mo'} gross margin)")
    style_axes(fig, showlegend=False)
    fig.update_yaxes(ticksuffix="x")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "How to read: LTV uses the T6M-average gross margin as the conservative base case (D-17); "
        "toggling to the Apr-24 run-rate margin shows the more optimistic reading as margins keep improving. "
        "Fully loaded CAC includes marketing + sales + an allocated share of G&A (D-05)."
    )
    with st.expander("Data table"):
        st.dataframe(pd.DataFrame({"segment": ue_view.index, "ltv_cac": ratio.round(2).values}), use_container_width=True)

    st.markdown("### CAC and payback")
    pay_cols = ["cac_fully_loaded_t6m", "cac_fully_loaded_t16m", "cac_payback_months_t6m", "cac_payback_months_t16m",
                "ltv_cac_t6m", "ltv_cac_t16m", "benchmark_ltv_cac_pass_ge3", "benchmark_payback_pass"]
    st.dataframe(ue_view[pay_cols].round(2), use_container_width=True)
    st.caption("How to read: T6M = fully loaded CAC / payback calibrated on the last 6 months; T16M = the whole 16-month window. Benchmarks: LTV:CAC >= 3x, payback < 12 months.")

    st.markdown("### Acquisition funnel")
    funnel = load_mart_dates("mart_a2_03_funnel_segment_monthly", ("month",))
    last6 = funnel[funnel.month >= pd.Timestamp("2023-11-01")]
    agg = last6.groupby("segment").agg(
        spend=("marketing_spend", "sum"),
        signups=("new_users_acquired_marketing", "sum"),
        paying=("new_paying_customers", "sum"),
    )
    agg["cost_per_signup"] = agg.spend / agg.signups
    agg["cost_per_paying"] = agg.spend / agg.paying
    agg["conversion"] = agg.paying / agg.signups
    seg_for_funnel = [SEG] if SEG != "Total" else ["B2C", "SMB", "Enterprise"]
    fig = go.Figure()
    for seg in seg_for_funnel:
        row = agg.loc[seg]
        fig.add_trace(go.Funnel(
            name=seg, y=["Sign-ups", "Paying customers"], x=[row.signups, row.paying],
            marker=dict(color=SEG_COLOR[seg]), textinfo="value+percent initial",
        ))
    fig.update_layout(title="Sign-ups -> paying customers, trailing 6 months")
    style_axes(fig, showlegend=len(seg_for_funnel) > 1)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "How to read: marketing counts sign-ups, not paying customers (D-06). Cost per sign-up looks cheap; "
        "cost per **paying** customer (= fully loaded CAC's numerator) is the number that matters for LTV:CAC."
    )
    with st.expander("Data table"):
        st.dataframe(agg.round(2), use_container_width=True)

    st.markdown("### Sensitivity table")
    sens = load_mart("mart_a2_13_sensitivity")
    sens_view = sens if SEG == "Total" else sens[sens.segment == SEG]
    st.dataframe(sens_view.round(3), use_container_width=True)
    st.caption("How to read: each row flexes one lever (CAC period, GM basis, lifetime cap) holding the rest at base case, from `mart_a2_13_sensitivity`.")

# =============================================================================
# TAB 4 -- Churn risk (May-24)
# =============================================================================
with tab_churn_risk:
    risk = load_mart_dates("mart_a1_06_may24_churn_risk", ("start_date", "end_date"))
    risk_view = risk if SEG == "Total" else risk[risk.segment == SEG]

    st.markdown("### Tier summary")
    summary = risk_view.groupby(["risk_tier", "segment"]).agg(
        n=("subscription_id", "count"), mrr=("mrr", "sum"), expected_churned_mrr=("mrr_at_risk", "sum")
    ).reset_index()
    tier_order = ["High", "Medium", "Low"]
    summary["risk_tier"] = pd.Categorical(summary.risk_tier, categories=tier_order, ordered=True)
    summary = summary.sort_values(["risk_tier", "segment"])
    fig = go.Figure()
    for seg in (["B2C", "SMB", "Enterprise"] if SEG == "Total" else [SEG]):
        d = summary[summary.segment == seg]
        d = d.set_index("risk_tier").reindex(tier_order).fillna(0)
        fig.add_bar(x=tier_order, y=d.expected_churned_mrr, name=seg, marker_color=SEG_COLOR[seg])
    fig.update_layout(title="Expected churned MRR by risk tier" + (" x segment" if SEG == "Total" else f" -- {SEG}"),
                       barmode="stack" if SEG == "Total" else "group")
    style_axes(fig, yfmt="$,.0f", showlegend=SEG == "Total")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"Population: {len(risk_view):,} subscriptions renewing in May-24 ($"
        f"{risk_view.mrr.sum():,.0f} MRR at stake). Risk tiers per D-16: High >= 50% churn probability, "
        f"Medium 25-49%, Low < 25%. 'Expected churned MRR' = sum(MRR x churn probability)."
    )
    with st.expander("Data table"):
        st.dataframe(
            summary[["risk_tier", "segment", "n", "mrr", "expected_churned_mrr"]].round(1),
            use_container_width=True,
        )

    st.markdown("### At-risk subscriptions")
    contrib_cols = [c for c in risk_view.columns if c.startswith("contrib_")]
    driver_label = {
        "contrib_active_days": "Low active days",
        "contrib_courses_seen": "Few courses viewed",
        "contrib_materials_seen": "Few materials viewed",
        "contrib_tenure": "Tenure / renewal stage",
        "contrib_plan_annual": "Annual plan",
        "contrib_is_b2b": "B2B account",
        "contrib_rc_contraction": "MRR contraction at last renewal",
        "contrib_rc_expansion": "MRR expansion at last renewal",
        "contrib_rc_no_prior_renewal": "First renewal (no history)",
        "contrib_gw_paypal": "Payment gateway: PayPal",
        "contrib_gw_mercadopago": "Payment gateway: MercadoPago",
        "contrib_gw_payoneer": "Payment gateway: Payoneer",
        "contrib_gw_wire_transfer": "Payment gateway: wire transfer",
    }
    risk_view = risk_view.copy()
    risk_view["main_driver"] = risk_view[contrib_cols].idxmax(axis=1).map(driver_label)

    tier_filter = st.multiselect("Filter by risk tier", tier_order, default=["High", "Medium"])
    table = risk_view[risk_view.risk_tier.isin(tier_filter)][
        ["subscription_id", "segment", "plan_type", "risk_tier", "prob_churn", "mrr", "main_driver", "end_date"]
    ].sort_values("prob_churn", ascending=False)
    table = table.rename(columns={"prob_churn": "probability", "end_date": "renewal_date"})
    st.dataframe(
        table.style.format({"probability": "{:.1%}", "mrr": "${:,.2f}"}),
        use_container_width=True, height=420,
    )
    st.caption(
        "How to read: 'main driver' is the feature with the largest positive contribution to the churn "
        "logit for that subscription (D-18: a same-period-engagement early-warning score, not a production model)."
    )
    st.download_button(
        "Download filtered list (CSV)",
        data=table.to_csv(index=False).encode("utf-8"),
        file_name=f"may24_at_risk_{segment_choice.lower()}.csv",
        mime="text/csv",
    )

# =============================================================================
# TAB 5 -- Scenarios & strategies
# =============================================================================
with tab_scenarios:
    st.markdown("### MRR outlook: base / bull / bear")
    bridge = load_mart_dates("mart_mrr_bridge", ("month_end",))
    proj = load_mart_dates("mart_s_02_projection_monthly", ("month_end",))
    summary = load_mart("mart_s_03_scenario_summary")

    act = bridge[bridge.segment == SEG].sort_values("month_end")
    proj_seg = proj[(proj.segment == SEG) & (proj.plan_type == "ALL")].sort_values(["scenario", "month_end"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=act.month_end, y=act.closing_mrr, name="Actual", line=dict(color=INK, width=3)))
    last_d, last_v = act.month_end.iloc[-1], act.closing_mrr.iloc[-1]
    for scen, col in (("bear", BLUE_LIGHT), ("base", BLUE), ("bull", BLUE_DARK)):
        g = proj_seg[proj_seg.scenario == scen]
        xs = pd.concat([pd.Series([last_d]), g.month_end])
        ys = pd.concat([pd.Series([last_v]), g.closing_mrr])
        fig.add_trace(go.Scatter(x=xs, y=ys, name=scen.capitalize(), line=dict(color=col, width=2.5)))
    fig.add_vline(x=last_d, line_dash="dot", line_color=GRID)
    fig.update_layout(title=f"MRR: actual + 12-month projection -- {segment_choice}")
    style_axes(fig, yfmt="$,.0f")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "How to read: black = actuals through Apr-24. Base = flat acquisition at the last-6-month average "
        "with T6M churn/expansion rates (D-19); Bull = acquisition trend + the three strategies below at "
        "their base case; Bear = churn stress + lower acquisition + halved expansion."
    )
    with st.expander("Data table -- scenario summary"):
        st.dataframe(summary[summary.segment == SEG].round(1) if SEG != "Total" else summary.round(1),
                     use_container_width=True)

    st.markdown("### Strategy impact")
    strat = load_mart("mart_s_04_strategy_impact")
    case = st.select_slider("Case", options=["low", "base", "high"], value="base")
    strat_view = strat[strat.case == case]
    strat_view = strat_view if SEG == "Total" else strat_view[strat_view.segment == SEG]
    st.dataframe(
        strat_view[["strategy", "segment", "mrr_delta_m6", "mrr_delta_pct_m6", "mrr_delta_m12", "mrr_delta_pct_m12",
                    "ndr_delta_pp_m6", "ndr_delta_pp_m12", "effort", "time_to_impact_months"]].round(2),
        use_container_width=True,
    )
    st.caption("How to read: 6- and 12-month MRR delta and NDR delta per strategy, isolated on top of the Base acquisition case. See `work/WP23_strategies/results.md` for the full writeup.")

    st.markdown("### Interactive projection (simplified)")
    st.caption(
        "**Simplified**; reuses the pure simulation step of the official engine "
        "(`sql/python_models/scenarios.py::simulate`) with drivers loaded from "
        "`mart_s_01_drivers.csv` and the Apr-24 customer base from `fct_subscriptions.csv` -- "
        "no database access. The official base/bull/bear scenarios and backtest are the table above; "
        "use these sliders to explore 'what if' without touching the SQL pipeline."
    )

    sys.path.insert(0, str(SCENARIOS_DIR))
    import scenarios as scn  # noqa: E402  (pure numpy/pandas module, no db import at load time)

    @st.cache_data
    def build_engine_base() -> dict:
        drivers = pd.read_csv(MARTS / "mart_s_01_drivers.csv")
        d = drivers[(drivers.scenario == "base") & (drivers.case == "base")]

        rates = {}
        for seg in scn.SEGMENTS:
            for plan in scn.PLANS:
                sub = d[(d.segment == seg) & (d.plan_type == plan)].set_index("driver")["value"]
                rates[(seg, plan)] = dict(
                    churn_rate_monthly=float(sub["churn_rate_monthly"]),
                    arpa_new=float(sub["arpa_new_customer"]),
                    plan_mix_share=float(sub["plan_mix_share"]),
                    expansion_rate_monthly=float(sub["expansion_rate_monthly"]),
                    contraction_rate_monthly=float(sub["contraction_rate_monthly"]),
                )

        new_seg = {}
        for seg in scn.SEGMENTS:
            sub = d[(d.segment == seg) & (d.plan_type == "ALL")].set_index("driver")["value"]
            new_seg[seg] = dict(avg=float(sub["new_customers_per_month_avg"]), slope=float(sub["new_customers_trend_slope"]))

        fct = pd.read_csv(MARTS / "fct_subscriptions.csv", parse_dates=["start_date", "end_date"])
        as_of = pd.Timestamp("2024-04-30")
        live = fct[(fct.start_date <= as_of) & (fct.end_date > as_of) & (fct.segment.isin(scn.SEGMENTS))]
        stock = live.groupby(["segment", "plan_type"]).agg(customers=("subscription_id", "count"), mrr=("mrr", "sum"))
        stock0 = {(seg, plan): dict(customers=float(stock.loc[(seg, plan), "customers"]) if (seg, plan) in stock.index else 0.0,
                                     mrr=float(stock.loc[(seg, plan), "mrr"]) if (seg, plan) in stock.index else 0.0)
                  for seg in scn.SEGMENTS for plan in scn.PLANS}

        return dict(rates=rates, new_seg=new_seg, stock0=stock0, window_months=6)

    engine_base = build_engine_base()

    sc1, sc2, sc3 = st.columns(3)
    churn_mult = sc1.slider("Monthly churn multiplier", 0.5, 2.0, 1.0, 0.05,
                             help="Scales the calibrated T6M churn rate for every segment/plan.")
    accel_mult = sc2.slider("New customers/month multiplier", 0.5, 2.0, 1.0, 0.05,
                             help="Scales the T6M average new-paying-customer run rate.")
    save_rate = sc3.slider("Save rate on flagged churners", 0.0, 0.5, 0.0, 0.05,
                            help="Strategy-1-style: share of monthly-plan churners saved by an in-cycle intervention.")

    params = scn.default_params()
    for b in scn.BUCKETS:
        params["churn_multiplier"][b] = churn_mult
        params["churn_save_rate"][b] = save_rate
    scaled_new_seg = {s: dict(avg=v["avg"] * accel_mult, slope=v["slope"] * accel_mult) for s, v in engine_base["new_seg"].items()}
    scaled_base = dict(engine_base, new_seg=scaled_new_seg)

    panel, _ = scn.simulate(engine_base["stock0"], scaled_base, params, n_months=12)
    panel = scn.add_rollups(panel)
    month_ends = pd.date_range("2024-05-31", periods=12, freq="ME")
    panel["month_end"] = panel.month_index.map(dict(enumerate(month_ends, start=1)))
    line = panel[(panel.segment == SEG) & (panel.plan_type == "ALL")].sort_values("month_index")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=act.month_end, y=act.closing_mrr, name="Actual", line=dict(color=INK, width=3)))
    for scen_name, col in (("bear", BLUE_LIGHT), ("base", BLUE), ("bull", BLUE_DARK)):
        g = proj_seg[proj_seg.scenario == scen_name]
        xs = pd.concat([pd.Series([last_d]), g.month_end])
        ys = pd.concat([pd.Series([last_v]), g.closing_mrr])
        fig.add_trace(go.Scatter(x=xs, y=ys, name=f"Official {scen_name}", line=dict(color=col, width=1.5, dash="dot")))
    xs = pd.concat([pd.Series([last_d]), line.month_end])
    ys = pd.concat([pd.Series([last_v]), line.closing_mrr])
    fig.add_trace(go.Scatter(x=xs, y=ys, name="Your scenario", line=dict(color="#8c2f24", width=3)))
    fig.add_vline(x=last_d, line_dash="dot", line_color=GRID)
    fig.update_layout(title=f"Interactive projection vs. official scenarios -- {segment_choice}")
    style_axes(fig, yfmt="$,.0f")
    st.plotly_chart(fig, use_container_width=True)

    end_mrr = line.closing_mrr.iloc[-1]
    st.metric(f"Your scenario: MRR Apr-25 ({segment_choice})", fmt_money(end_mrr),
              delta=f"{(end_mrr / last_v - 1) * 100:+.1f}% vs. Apr-24")
    with st.expander("Data table -- your scenario, monthly"):
        st.dataframe(line[["month_end", "opening_mrr", "new_mrr", "expansion_mrr", "contraction_mrr", "churn_mrr", "closing_mrr"]]
                     .assign(month_end=lambda d: d.month_end.dt.strftime("%Y-%m")).round(1),
                     use_container_width=True)
