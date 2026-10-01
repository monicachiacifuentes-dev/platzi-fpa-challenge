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
    # Title across the top; legend in its own column on the right, so the two never overlap
    margin=dict(l=10, r=10, t=60, b=10),
    title=dict(x=0, xanchor="left", y=0.97, yanchor="top", font=dict(size=16)),
    hovermode="x unified",
    legend=dict(orientation="v", xanchor="left", x=1.02, yanchor="top", y=1, bgcolor="rgba(0,0,0,0)"),
)


def style_axes(fig, yfmt=None, showlegend=True):
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=GRID)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, tickformat=yfmt)
    fig.update_layout(**BASE_LAYOUT, showlegend=showlegend)
    return fig


def month_axis(fig):
    """Month-end data points: centre each bar/point on its calendar month, so Apr-30 reads as Apr, not May."""
    fig.update_traces(xperiod="M1", xperiodalignment="middle", xhoverformat="%b %Y")
    fig.update_xaxes(dtick="M2", tickformat="%b %Y", ticklabelmode="period")
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


SEGMENT_ORDER = ["B2C", "SMB", "Enterprise"]


def order_segments(selected) -> list[str]:
    """Segments in the fixed B2C / SMB / Enterprise order, regardless of the
    order the widget returns them in."""
    return [s for s in SEGMENT_ORDER if s in selected]


def resolve_group(selected: list[str]) -> tuple[str | None, str]:
    """Resolve a multi-segment selection to (precomputed_group_label, display_label).

    Several marts carry precomputed rollup rows that are exact -- "Total" (all
    three segments), "B2B" (SMB + Enterprise), and each base segment on its
    own. When the selection matches one of those exactly, the first element is
    that label and callers should read the rollup row directly. Any other
    combination (e.g. {B2C, SMB}) has no precomputed row: the first element is
    None and callers must aggregate from the base segment rows instead (sum
    additive columns, recompute ratios from summed numerators/denominators).
    """
    s = set(selected)
    if s == {"B2C", "SMB", "Enterprise"}:
        return "Total", "All segments"
    if s == {"SMB", "Enterprise"}:
        return "B2B", "B2B"
    if len(s) == 1:
        only = next(iter(s))
        return only, only
    return None, " + ".join(order_segments(selected))


def seg_slug(selected: list[str]) -> str:
    """Filename-safe slug for the current selection, e.g. 'all', 'b2b', 'b2c_smb'."""
    if set(selected) == {"B2C", "SMB", "Enterprise"}:
        return "all"
    return "_".join(seg.lower() for seg in order_segments(selected))


def fmt_money(x: float, decimals: int = 0) -> str:
    return f"${x:,.{decimals}f}"


def fmt_pct(x: float, decimals: int = 1) -> str:
    return f"{x * 100:,.{decimals}f}%"


# --------------------------------------------------------------------------- segment aggregation helpers
# Every helper below takes the raw selection (`selected`) plus the precomputed
# group label from resolve_group (`group`, None when the selection has no
# rollup row) and returns data scoped to that selection: the rollup row
# when `group` is given (exact), otherwise base B2C/SMB/Enterprise rows summed
# on their additive columns with ratios recomputed from the summed
# numerators/denominators -- never averaged, never mixed with a rollup row.

BRIDGE_COLS = ["opening_mrr", "new_mrr", "expansion_mrr", "contraction_mrr", "churn_mrr", "closing_mrr", "active_customers"]


def bridge_scoped(bridge: pd.DataFrame, selected: list[str], group: str | None) -> pd.DataFrame:
    if group is not None:
        return bridge[bridge.segment == group].sort_values("month_end").copy()
    sub = bridge[bridge.segment.isin(selected)].copy()
    sub[BRIDGE_COLS] = sub[BRIDGE_COLS].fillna(0.0)
    return sub.groupby("month_end", as_index=False)[BRIDGE_COLS].sum().sort_values("month_end")


def subs_scoped(q3: pd.DataFrame, selected: list[str], group: str | None, plan_type: str = "Total") -> float:
    # mart_q3_active_subs_apr24 has Total and each base segment, but no B2B rollup
    # row -- fall through to the sum whenever the precomputed row isn't there.
    if group is not None:
        match = q3[(q3.segment == group) & (q3.plan_type == plan_type)]
        if not match.empty:
            return float(match.active_subs.iloc[0])
    sub = q3[q3.segment.isin(selected) & (q3.plan_type == plan_type)]
    return float(sub.active_subs.sum())


def retention_scoped(q2: pd.DataFrame, selected: list[str], group: str | None,
                      split: str = "all", method: str = "M06_primary") -> dict:
    if group is not None:
        row = q2.loc[(q2.segment == group) & (q2.split == split) & (q2.method == method)].iloc[0]
        return dict(logo_rate=row.logo_rate, dollar_rate=row.dollar_rate)
    sub = q2[q2.segment.isin(selected) & (q2.split == split) & (q2.method == method)]
    n_renewed, n_ended = sub.n_renewed.sum(), sub.n_ended.sum()
    dollar_num, dollar_den = sub.dollar_numerator.sum(), sub.dollar_denominator.sum()
    return dict(logo_rate=n_renewed / n_ended, dollar_rate=dollar_num / dollar_den)


def ndr_scoped(q4: pd.DataFrame, selected: list[str], group: str | None, method: str = "M08_M09_M10") -> dict:
    """NDR = end / start; GRR = (start - contraction - churn) / start (expansion excluded)."""
    if group is not None:
        row = q4.loc[(q4.segment == group) & (q4.method == method)].iloc[0]
        return dict(ndr=row.ndr, grr=row.grr)
    sub = q4[q4.segment.isin(selected) & (q4.method == method)]
    start, contraction, churn, end = sub.start_mrr.sum(), sub.contraction_mrr.sum(), sub.churn_mrr.sum(), sub.end_mrr.sum()
    return dict(ndr=end / start, grr=(start - contraction - churn) / start)


def ndr_t6m_scoped(a303: pd.DataFrame, selected: list[str], group: str | None) -> float:
    if group is not None:
        return float(a303.loc[a303.segment == group, "ndr"].iloc[0])
    sub = a303[a303.segment.isin(selected)]
    return float(sub.end_mrr.sum() / sub.start_mrr.sum())


def gm_scoped(gm: pd.DataFrame, selected: list[str], group: str | None, month: pd.Timestamp) -> float:
    """GM% = gross profit / revenue; both additive across segments (COGS is
    allocated by MRR share, D-07, so summing gross_profit_base reconstructs
    the company total exactly)."""
    if group is not None:
        return float(gm.loc[(gm.month == month) & (gm.segment == group), "gm_pct_base"].iloc[0])
    sub = gm[(gm.month == month) & (gm.segment.isin(selected))]
    return float(sub.gross_profit_base.sum() / sub.revenue.sum())


STEP_ORDER = {"Start MRR": 1, "Churn": 2, "Contraction": 3, "Expansion": 4, "End MRR": 5}


def waterfall_scoped(wf: pd.DataFrame, selected: list[str], group: str | None) -> pd.DataFrame:
    if group is not None:
        return wf[wf.segment == group].sort_values("step_order").copy()
    sub = wf[wf.segment.isin(selected)]
    out = sub.groupby("step", as_index=False)["amount"].sum()
    out["step_order"] = out["step"].map(STEP_ORDER)
    return out.sort_values("step_order")


def cohort_group_for(selected: list[str]) -> tuple[str, bool]:
    """mart_a1_01_cohort_retention only splits cohorts into Total / B2C / B2B
    (A-30 -- no SMB/Enterprise split was ever computed at that granularity).
    Maps the selection to the closest of those three; the bool flags an exact
    match vs. a fallback."""
    s = set(selected)
    if s == {"B2C", "SMB", "Enterprise"}:
        return "Total", True
    if s == {"B2C"}:
        return "B2C", True
    if s == {"SMB", "Enterprise"}:
        return "B2B", True
    if s in ({"SMB"}, {"Enterprise"}):
        return "B2B", False
    return "Total", False  # custom combos that include B2C, e.g. {B2C, SMB}: no valid subset exists


def sens_scoped(sens: pd.DataFrame, selected: list[str], group: str | None) -> pd.DataFrame:
    """Sensitivity results are ratios (CAC, GM%, LTV:CAC, payback) and are not
    additive across segments, so there is no B2B or custom-combo rollup here:
    the precomputed Total row when all three segments are selected, otherwise
    one row per selected base segment."""
    if group == "Total":
        return sens[sens.segment == "Total"].copy()
    return sens[sens.segment.isin(selected)].copy()


PROJ_COLS = ["opening_customers", "opening_mrr", "new_customers", "new_mrr", "expansion_mrr", "contraction_mrr",
             "churn_customers", "churn_mrr", "migration_out_customers", "migration_out_mrr",
             "migration_in_customers", "migration_in_mrr", "closing_customers", "closing_mrr"]


def proj_scoped(proj: pd.DataFrame, selected: list[str], group: str | None) -> pd.DataFrame:
    base = proj[proj.plan_type == "ALL"]
    if group is not None:
        return base[base.segment == group].sort_values(["scenario", "month_end"]).copy()
    sub = base[base.segment.isin(selected)]
    out = sub.groupby(["scenario", "month_index", "month_end"], as_index=False)[PROJ_COLS].sum()
    return out.sort_values(["scenario", "month_end"])


def scenario_summary_scoped(summary: pd.DataFrame, selected: list[str], group: str | None, label: str) -> pd.DataFrame:
    """MRR/subs are summed (additive); forward NDR/GRR are recomputed as
    sum(rate x mrr_apr24_actual) / sum(mrr_apr24_actual) -- mrr_apr24_actual is
    each segment's NDR/GRR denominator (start MRR), so this is exactly
    Sigma numerator / Sigma denominator, never an average of rates."""
    if group is not None:
        return summary[summary.segment == group].copy()
    sub = summary[summary.segment.isin(selected)]
    rate_cols = ["forward_ndr_m6", "forward_grr_m6", "forward_ndr_m12", "forward_grr_m12"]
    rows = []
    for scen, g in sub.groupby("scenario"):
        mrr24, mrr25 = g.mrr_apr24_actual.sum(), g.mrr_apr25.sum()
        row = dict(scenario=scen, segment=label,
                   mrr_apr24_actual=mrr24, mrr_apr25=mrr25,
                   mrr_growth_pct=(mrr25 / mrr24 - 1) * 100,
                   subs_apr24_actual=g.subs_apr24_actual.sum(), subs_apr25=g.subs_apr25.sum())
        for c in rate_cols:
            row[c] = (g[c] * g.mrr_apr24_actual).sum() / mrr24
        rows.append(row)
    return pd.DataFrame(rows)


def strategy_impact_scoped(strat: pd.DataFrame, selected: list[str], group: str | None) -> tuple[pd.DataFrame, bool]:
    """MRR deltas are additive but %/pp deltas are not, so a custom combination
    (no precomputed row) is shown as one row per selected segment rather than
    a blended average -- the caller adds a caption explaining this. Returns
    (view, is_exact)."""
    if group is not None:
        return strat[strat.segment == group].copy(), True
    return strat[strat.segment.isin(selected)].copy(), False


def panel_scoped(panel: pd.DataFrame, selected: list[str], group: str | None) -> pd.DataFrame:
    """Interactive-scenario panel (from scn.simulate/add_rollups) scoped to the
    selection. Every column is an additive $ / count flow, so summing the base
    segment rows is exact -- add_rollups builds its own 'B2B'/'Total' rows the
    same way."""
    base = panel[panel.plan_type == "ALL"]
    if group is not None:
        return base[base.segment == group].sort_values("month_index").copy()
    sub = base[base.segment.isin(selected)]
    num_cols = [c for c in sub.columns if c not in ("month_index", "segment", "plan_type", "month_end")]
    return sub.groupby(["month_index", "month_end"], as_index=False)[num_cols].sum().sort_values("month_index")


# =============================================================================
# Sidebar
# =============================================================================
st.sidebar.title("Filters")
selected_segments = st.sidebar.multiselect(
    "Segments", SEGMENT_ORDER, default=SEGMENT_ORDER,
    help="Scopes every chart and table on the page. Pick one or more segments.",
)
if not selected_segments:
    st.sidebar.caption("No segment selected -- showing all segments.")
    selected_segments = list(SEGMENT_ORDER)
selected_segments = order_segments(selected_segments)
SEG_GROUP, SEG_LABEL = resolve_group(selected_segments)
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
    f"Segment: **{SEG_LABEL}** &nbsp;|&nbsp; "
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
    brow = bridge_scoped(bridge, selected_segments, SEG_GROUP)
    mrr_apr24 = brow.loc[brow.month_end == apr24, "closing_mrr"].iloc[0]
    subs_apr24 = subs_scoped(q3, selected_segments, SEG_GROUP, plan_type="Total")
    ret = retention_scoped(q2, selected_segments, SEG_GROUP, split="all", method="M06_primary")
    ndr = ndr_scoped(q4, selected_segments, SEG_GROUP, method="M08_M09_M10")
    ndr_t6m = ndr_t6m_scoped(a303, selected_segments, SEG_GROUP)
    gm_pct = gm_scoped(gm, selected_segments, SEG_GROUP, apr24)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(f"MRR, Apr-24 ({SEG_LABEL})", fmt_money(mrr_apr24))
    c2.metric("Active subscriptions", f"{int(subs_apr24):,}")
    c3.metric(
        "Q1-24 retention (logo)", fmt_pct(ret["logo_rate"]),
        help=f"$ basis: {fmt_pct(ret['dollar_rate'])}. Renewal-event basis (M-06): renewed / (renewed + churned).",
    )
    c4.metric(
        "NDR, trailing 12 mo", fmt_pct(ndr["ndr"]),
        help=f"Trailing 6 mo: {fmt_pct(ndr_t6m)}. M-08: MRR now / MRR 12 months ago, fixed customer base.",
    )
    c5.metric(
        "Gross margin, Apr-24", fmt_pct(gm_pct),
        help="COGS allocated by MRR share (D-07/A-03) -> uniform % across segments by design.",
    )
    st.caption(
        "How to read: KPI tiles are scoped to the sidebar segment filter. "
        "GM% is uniform across segments because COGS is allocated by share of MRR (D-07), not by segment cost drivers."
    )

    st.markdown("### MRR by segment")
    b_seg = bridge[bridge.segment.isin(selected_segments)].copy()
    piv = b_seg.pivot(index="month_end", columns="segment", values="closing_mrr").fillna(0)
    piv = piv[[c for c in ["B2C", "SMB", "Enterprise"] if c in piv.columns]]
    fig = go.Figure()
    for seg in piv.columns:
        fig.add_bar(x=piv.index, y=piv[seg], name=seg, marker_color=SEG_COLOR[seg])
    fig.update_layout(barmode="stack", title="MRR by segment, monthly (stacked)")
    style_axes(fig, yfmt="$,.0f", showlegend=len(piv.columns) > 1)
    month_axis(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "How to read: each bar is total MRR at month-end; colors are fixed segment identities "
        "(B2C blue, SMB orange, Enterprise green) used consistently across every tab."
    )
    with st.expander("Data table"):
        st.dataframe(piv.reset_index().assign(month_end=lambda d: d.month_end.dt.strftime("%Y-%m")), use_container_width=True)

    st.markdown("### MRR bridge (new / expansion / contraction / churn)")
    br = bridge_scoped(bridge, selected_segments, SEG_GROUP)
    fig2 = go.Figure()
    fig2.add_bar(x=br.month_end, y=br.new_mrr.fillna(0), name="New", marker_color=MOVE_COLOR["New"])
    fig2.add_bar(x=br.month_end, y=br.expansion_mrr.fillna(0), name="Expansion", marker_color=MOVE_COLOR["Expansion"])
    fig2.add_bar(x=br.month_end, y=-br.contraction_mrr.fillna(0), name="Contraction", marker_color=MOVE_COLOR["Contraction"])
    fig2.add_bar(x=br.month_end, y=-br.churn_mrr.fillna(0), name="Churn", marker_color=MOVE_COLOR["Churn"])
    fig2.add_trace(go.Scatter(x=br.month_end, y=br.closing_mrr, mode="lines", name="Closing MRR",
                               line=dict(color=INK, width=2)))
    fig2.update_layout(barmode="relative", title=f"MRR bridge by month -- {SEG_LABEL}")
    style_axes(fig2, yfmt="$,.0f")
    month_axis(fig2)
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
    cohort_group, cohort_exact = cohort_group_for(selected_segments)
    if not cohort_exact:
        st.info(
            f"Cohort retention is only tracked at Total / B2C / B2B granularity in the data model "
            f"(A-30: mart_a1_01_cohort_retention has no SMB/Enterprise split) -- showing the **{cohort_group}** "
            f"cohort matrix for {SEG_LABEL}.",
            icon="ℹ️",
        )
    dollar_toggle = st.toggle("Show $ (dollar) retention instead of logo retention", value=False, key="cohort_toggle")
    a101 = load_mart("mart_a1_01_cohort_retention")
    cg = a101[a101.segment_group == cohort_group].copy()
    metric_col = "dollar_retention" if dollar_toggle else "logo_retention"
    heat = cg.pivot(index="cohort_month", columns="month_k", values=metric_col)
    heat = heat.sort_index()
    # Fixed 30-100% scale (observed range is 36-103%) so shades are comparable across segments and toggles;
    # values above 100% (B2B dollar expansion) take the darkest shade.
    fig = go.Figure(
        data=go.Heatmap(
            z=heat.values * 100,
            x=[f"M{k}" for k in heat.columns],
            y=pd.to_datetime(heat.index).strftime("%b %Y"),
            colorscale=[[0, "#f3f8fe"], [0.35, BLUE_LIGHT], [0.7, BLUE], [1, BLUE_DARK]],
            zmin=30, zmax=100,
            texttemplate="%{z:.0f}", textfont=dict(size=10),
            xgap=1, ygap=1,
            colorbar=dict(title="%", ticksuffix="%", tickvals=[30, 50, 70, 90, 100]),
            hovertemplate="Cohort %{y}<br>Month %{x}<br>Retention %{z:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(title=f"{'Dollar' if dollar_toggle else 'Logo'} retention by signup cohort -- {cohort_group}",
                       yaxis=dict(autorange="reversed", type="category"), height=560)
    style_axes(fig, showlegend=False)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "How to read: each row is a signup-month cohort; each column is months since signup. "
        "Cell labels are % retained; darker = more retained (scale 30-100%). Blank cells = cohort hasn't reached that age yet."
    )
    with st.expander("Data table"):
        st.dataframe((heat * 100).round(1), use_container_width=True)

    st.markdown("### NDR waterfall")
    window_toggle = st.toggle("Show T6M instead of T12M", value=False, key="ndr_window_toggle")
    wf_name = "mart_a3_04_t6m_waterfall_long" if window_toggle else "mart_a3_02_t12m_waterfall_long"
    wf = load_mart(wf_name)
    wf_seg = waterfall_scoped(wf, selected_segments, SEG_GROUP)
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
    fig.update_layout(title=f"NDR waterfall, {window_label} -- {SEG_LABEL}")
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
    bdf = base[base.segment.isin(selected_segments)]
    order = ["0-5", "6-10", "11-15", "16-20", "21-25", "26-28"]
    g = bdf.groupby("active_days_bucket").agg(n=("churned", "size"), churn_rate=("churned", "mean")).reindex(order).dropna()
    fig = go.Figure(go.Bar(x=g.index, y=g.churn_rate * 100, marker_color=BLUE,
                            text=[f"{v:.0f}%" for v in g.churn_rate * 100], textposition="outside"))
    fig.update_layout(title=f"Churn rate by active days in the billing period -- {SEG_LABEL}")
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
    ue = ue[ue.segment.isin(SEGMENT_ORDER)].set_index("segment")
    gm_apr24 = load_mart_dates("mart_a2_08_gm_monthly", ("month",))
    gm_total = gm_apr24[gm_apr24.segment == "Total"].sort_values("month")
    gm_now = gm_total.gm_pct_base.iloc[-1]
    gm_t3m = gm_total.gm_pct_base.tail(3).mean()
    ue_view = ue.loc[selected_segments]

    st.markdown("### LTV : CAC by segment")
    gm_t6m = ue.gm_pct_t6m_base.iloc[0]
    # Only the gross-margin input changes; ARPA, lifetime and CAC stay on their T6M basis.
    gm_options = {
        f"Trailing 6 months ({gm_t6m:.1%}, base/conservative)": ("trailing 6mo", gm_t6m),
        f"Trailing 3 months ({gm_t3m:.1%})": ("trailing 3mo", gm_t3m),
        f"Apr-24 run-rate ({gm_now:.1%}, D-17 sensitivity)": ("Apr-24 run-rate", gm_now),
    }
    gm_basis = st.radio("Gross margin basis", list(gm_options), horizontal=True, key="gm_basis")
    gm_label, gm_used = gm_options[gm_basis]
    ratio = ue_view.ltv_base / ue_view.cac_fully_loaded_t6m * (gm_used / gm_t6m)
    fig = go.Figure()
    for seg in ue_view.index:
        fig.add_bar(x=[seg], y=[ratio.loc[seg]], name=seg, marker_color=SEG_COLOR[seg], showlegend=False,
                    text=f"{ratio.loc[seg]:.1f}x", textposition="outside")
    fig.add_hline(y=3, line_dash="dash", line_color=INK2, annotation_text="3x benchmark", annotation_position="top left")
    fig.update_layout(title=f"LTV : CAC ({gm_label} gross margin)")
    style_axes(fig, showlegend=False)
    fig.update_yaxes(ticksuffix="x")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "How to read: LTV uses the T6M-average gross margin as the conservative base case (D-17); "
        "the trailing-3-month and Apr-24 run-rate margins show progressively more optimistic readings as margins keep "
        "improving. Only the margin changes; ARPA, lifetime and CAC stay on their T6M basis. "
        "Fully loaded CAC includes marketing + sales + an allocated share of G&A (D-05)."
        + (" LTV:CAC is a ratio, not additive -- each bar is one selected segment, never a blended combination."
           if len(selected_segments) > 1 else "")
    )
    with st.expander("Data table"):
        st.dataframe(pd.DataFrame({"segment": ue_view.index, "ltv_cac": ratio.round(2).values}), use_container_width=True)

    st.markdown("### CAC and payback")
    # Same margin as the chart above: payback = CAC / (ARPA x GM); LTV scales linearly with GM.
    gm_profit = ue_view.arpa_t6m_avg * gm_used
    ltv = ue_view.ltv_base * (gm_used / gm_t6m)
    pay = pd.DataFrame({
        "CAC (6 mo)": ue_view.cac_fully_loaded_t6m.map("${:,.0f}".format),
        "CAC (16 mo)": ue_view.cac_fully_loaded_t16m.map("${:,.0f}".format),
        "Payback, months (6-mo CAC)": (ue_view.cac_fully_loaded_t6m / gm_profit).round(1),
        "Payback, months (16-mo CAC)": (ue_view.cac_fully_loaded_t16m / gm_profit).round(1),
        "LTV:CAC (6-mo CAC)": (ltv / ue_view.cac_fully_loaded_t6m).map("{:.2f}x".format),
        "LTV:CAC (16-mo CAC)": (ltv / ue_view.cac_fully_loaded_t16m).map("{:.2f}x".format),
    })
    pay["LTV:CAC ≥ 3x?"] = (ltv / ue_view.cac_fully_loaded_t6m >= 3).map({True: "✅ Yes", False: "❌ No"})
    pay["Payback < 12 mo?"] = (pay["Payback, months (6-mo CAC)"] < 12).map({True: "✅ Yes", False: "❌ No"})
    st.dataframe(pay.rename_axis("Segment"), use_container_width=True)
    st.caption(
        f"How to read: gross margin = {gm_label} ({gm_used:.1%}), same as the chart above. "
        "'6-mo CAC' = fully loaded CAC (marketing + sales + allocated G&A) on Nov-23 to Apr-24, the base case; "
        "'16-mo CAC' = the whole Jan-23 to Apr-24 window, higher because early acquisition was costlier. "
        "Payback = CAC / (monthly ARPA x gross margin), before churn. Benchmarks use the 6-mo CAC: "
        "LTV:CAC >= 3x, payback < 12 months."
    )

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
    seg_for_funnel = selected_segments
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
    sens_view = sens_scoped(sens, selected_segments, SEG_GROUP)
    st.dataframe(sens_view.round(3), use_container_width=True)
    st.caption(
        "How to read: each row flexes one lever (CAC period, GM basis, lifetime cap) holding the rest at base case, "
        "from `mart_a2_13_sensitivity`."
        + (" These are ratios, so a custom combination shows one row per selected segment rather than a blend."
           if SEG_GROUP != "Total" and len(selected_segments) > 1 else "")
    )

# =============================================================================
# TAB 4 -- Churn risk (May-24)
# =============================================================================
with tab_churn_risk:
    risk = load_mart_dates("mart_a1_06_may24_churn_risk", ("start_date", "end_date"))
    risk_view = risk[risk.segment.isin(selected_segments)]

    st.markdown("### Tier summary")
    summary = risk_view.groupby(["risk_tier", "segment"]).agg(
        n=("subscription_id", "count"), mrr=("mrr", "sum"), expected_churned_mrr=("mrr_at_risk", "sum")
    ).reset_index()
    tier_order = ["High", "Medium", "Low"]
    summary["risk_tier"] = pd.Categorical(summary.risk_tier, categories=tier_order, ordered=True)
    summary = summary.sort_values(["risk_tier", "segment"])
    multi = len(selected_segments) > 1
    fig = go.Figure()
    for seg in selected_segments:
        d = summary[summary.segment == seg]
        d = d.set_index("risk_tier").reindex(tier_order).fillna(0)
        fig.add_bar(x=tier_order, y=d.expected_churned_mrr, name=seg, marker_color=SEG_COLOR[seg])
    fig.update_layout(title="Expected churned MRR by risk tier" + (" x segment" if multi else f" -- {SEG_LABEL}"),
                       barmode="stack" if multi else "group")
    style_axes(fig, yfmt="$,.0f", showlegend=multi)
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
        file_name=f"may24_at_risk_{seg_slug(selected_segments)}.csv",
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

    act = bridge_scoped(bridge, selected_segments, SEG_GROUP)
    proj_seg = proj_scoped(proj, selected_segments, SEG_GROUP)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=act.month_end, y=act.closing_mrr, name="Actual", line=dict(color=INK, width=3)))
    last_d, last_v = act.month_end.iloc[-1], act.closing_mrr.iloc[-1]
    for scen, col in (("bear", BLUE_LIGHT), ("base", BLUE), ("bull", BLUE_DARK)):
        g = proj_seg[proj_seg.scenario == scen]
        xs = pd.concat([pd.Series([last_d]), g.month_end])
        ys = pd.concat([pd.Series([last_v]), g.closing_mrr])
        fig.add_trace(go.Scatter(x=xs, y=ys, name=scen.capitalize(), line=dict(color=col, width=2.5)))
    fig.add_vline(x=last_d, line_dash="dot", line_color=GRID)
    fig.update_layout(title=f"MRR: actual + 12-month projection -- {SEG_LABEL}")
    style_axes(fig, yfmt="$,.0f")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "How to read: black = actuals through Apr-24. Base = flat acquisition at the last-6-month average "
        "with T6M churn/expansion rates (D-19); Bull = acquisition trend + the three strategies below at "
        "their base case; Bear = churn stress + lower acquisition + halved expansion."
    )
    with st.expander("Data table -- scenario summary"):
        st.dataframe(scenario_summary_scoped(summary, selected_segments, SEG_GROUP, SEG_LABEL).round(1),
                     use_container_width=True)

    st.markdown("### Strategy impact")
    strat = load_mart("mart_s_04_strategy_impact")
    case = st.select_slider("Case", options=["low", "base", "high"], value="base")
    strat_view, strat_exact = strategy_impact_scoped(strat[strat.case == case], selected_segments, SEG_GROUP)
    st.dataframe(
        strat_view[["strategy", "segment", "mrr_delta_m6", "mrr_delta_pct_m6", "mrr_delta_m12", "mrr_delta_pct_m12",
                    "ndr_delta_pp_m6", "ndr_delta_pp_m12", "effort", "time_to_impact_months"]].round(2),
        use_container_width=True,
    )
    st.caption(
        "How to read: 6- and 12-month MRR delta and NDR delta per strategy, isolated on top of the Base acquisition "
        "case. See `work/WP23_strategies/results.md` for the full writeup."
        + ("" if strat_exact else " Showing one row per selected segment for this custom combination: MRR deltas "
                                   "are additive but %/pp deltas are not, so they are not blended across segments.")
    )

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
    line = panel_scoped(panel, selected_segments, SEG_GROUP)

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
    fig.update_layout(title=f"Interactive projection vs. official scenarios -- {SEG_LABEL}")
    style_axes(fig, yfmt="$,.0f")
    st.plotly_chart(fig, use_container_width=True)

    end_mrr = line.closing_mrr.iloc[-1]
    st.metric(f"Your scenario: MRR Apr-25 ({SEG_LABEL})", fmt_money(end_mrr),
              delta=f"{(end_mrr / last_v - 1) * 100:+.1f}% vs. Apr-24")
    with st.expander("Data table -- your scenario, monthly"):
        st.dataframe(line[["month_end", "opening_mrr", "new_mrr", "expansion_mrr", "contraction_mrr", "churn_mrr", "closing_mrr"]]
                     .assign(month_end=lambda d: d.month_end.dt.strftime("%Y-%m")).round(1),
                     use_container_width=True)
