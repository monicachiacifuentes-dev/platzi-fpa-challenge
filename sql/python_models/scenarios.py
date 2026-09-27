"""
scenarios.py -- WP31 (Scenario Model, bonus) + WP23 (Retention Strategy Recommendations)

A driver-based, monthly "compartment" projection engine over 6 buckets
(segment x plan_type: {B2C, SMB, Enterprise} x {monthly, annual}), calibrated
from observed data (default: trailing 6 months, "T6M", matching the WP21/WP22
convention). Every input parameter that isn't a raw calibrated rate is a named,
justified constant declared at the top of this file (search "SCENARIO / STRATEGY
ASSUMPTIONS") and is written to mart_s_01_drivers so nothing is a hidden magic
number.

Engine mechanics per month, per bucket (segment, plan_type):
  1. Logo churn on opening customers (monthly-plan: observed monthly renewal-basis
     rate, used as-is. Annual-plan: observed annual renewal-basis rate, converted
     to a MONTHLY-EQUIVALENT rate via 1-(1-annual_rate)^(1/12), because the
     compartment model has no per-customer renewal-anniversary calendar -- see
     Proposed A-19 below). MRR lost is proportional to the bucket's current
     average ARPA (mrr/customers).
  2. Net expansion / contraction applied to RETAINED MRR only, B2B buckets only
     (verified data fact: B2C mrr is fixed at 49/33.25, so B2C expansion/contraction
     rate is always 0).
  3. Monthly -> annual migration (B2C monthly bucket only): a WP23 Strategy-2 /
     Bull-only lever; retained B2C-monthly customers convert to B2C-annual at a
     monthly rate, leaving their old ARPA (49) and joining at the new one (33.25).
  4. New customers added at the bucket's calibrated new-customer ARPA, split by
     the bucket's observed new-customer plan mix.
Identity per bucket, per month (tested in sql/tests/test_s_03_movement_identity.sql):
  opening_mrr + new_mrr + expansion_mrr - contraction_mrr - churn_mrr
    - migration_out_mrr + migration_in_mrr = closing_mrr

Forward NDR/GRR of the fixed Apr-24 base (no new customers) reuses the exact
same simulate() engine with new_customers forced to 0; GRR reuses it a second
time with expansion forced to 0 (M-09: GRR = NDR with no credit for expansion).

Tables written:
  mart_s_01_drivers            -- every calibrated + assumed input, long format
  mart_s_02_projection_monthly -- scenario x month x segment(+plan_type) panel
  mart_s_03_scenario_summary   -- scenario x segment: MRR/subs Apr-25, growth%,
                                   forward NDR/GRR of the Apr-24 base at M6/M12
  mart_s_04_strategy_impact    -- WP23: strategy x case(low/base/high) x segment
  mart_s_05_backtest           -- backtest, calibrated on data <= 2023-10-31,
                                   projected Nov-23..Apr-24, vs. actual
  mart_s_06_backtest_summary   -- MAPE by segment (MRR and customers)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SEGMENTS = ["B2C", "SMB", "Enterprise"]
PLANS = ["monthly", "annual"]
BUCKETS = [(s, p) for s in SEGMENTS for p in PLANS]
B2B_SEGMENTS = ["SMB", "Enterprise"]

B2C_ANNUAL_PRICE = 33.25  # verified fixed price (Docs/Plan_and_Index.md, verified data facts)

AS_OF_MAIN = pd.Timestamp("2024-04-30")
WINDOW_MONTHS = 6          # T6M calibration window, matches WP21/WP22 convention
N_MONTHS_MAIN = 12         # May-24 .. Apr-25

BACKTEST_AS_OF = pd.Timestamp("2023-10-31")
BACKTEST_WINDOW_MONTHS = 6   # calibrate on May-23..Oct-23
BACKTEST_HORIZON = 6         # project Nov-23..Apr-24

# ---------------------------------------------------------------------------
# SCENARIO / STRATEGY ASSUMPTIONS (Proposed A-19..A-24 -- see results.md)
# ---------------------------------------------------------------------------
# Bear stress (A-19): +15% relative churn = the largest positive monthly
# deviation from the T12M mean observed in B2C-monthly logo churn (see
# work/WP31_scenarios/results.md, "Backtest & driver volatility"). Acquisition
# -10% (A-19b) = roughly 1.5x the worst single observed MoM decline in new B2C
# customers (-6.3%), applied as a SUSTAINED haircut for all 12 months (a full
# soft-demand year, not just one bad month). Expansion halved is given directly
# by the brief.
BEAR_CHURN_RELATIVE_INCREASE = 0.15
BEAR_ACQUISITION_RELATIVE_DECLINE = 0.10
BEAR_EXPANSION_MULTIPLIER = 0.5

# WP23 Strategy 1 -- in-period low-engagement alert + save play (A-20).
# save_rate = share of the flagged, would-be-monthly-churners who are saved.
# Range 10/20/30% is the industry-typical outbound-save-rate band stated in the
# brief; applied only to MONTHLY-plan churn (the alert acts within one billing
# period, D-18) for all three segments (B2C automated nudges, B2B CSM outreach).
STRATEGY1_SAVE_RATE = {"low": 0.10, "base": 0.20, "high": 0.30}

# WP23 Strategy 2 -- B2C monthly -> annual migration offer (A-21).
# conversion_rate = share of the RETAINED B2C-monthly base converting to annual
# each month. 2/4/6% chosen as a plausible offer-acceptance range for a modest,
# recurring discount-style nudge (no direct data on offer take-up; sensitivity
# is reported).
STRATEGY2_CONVERSION_RATE = {"low": 0.02, "base": 0.04, "high": 0.06}

# WP23 Strategy 3 -- B2B expansion & contraction-prevention playbook (A-22).
# SMB: QBR / seat-expansion motion -> relative UPLIFT to SMB's observed monthly
# expansion rate. Enterprise: 2nd-renewal save motion -> relative REDUCTION to
# Enterprise's observed monthly contraction rate.
STRATEGY3_SMB_EXPANSION_UPLIFT = {"low": 0.20, "base": 0.40, "high": 0.60}
STRATEGY3_ENT_CONTRACTION_REDUCTION = {"low": 0.30, "base": 0.50, "high": 0.70}

# Bull = Base acquisition trend + all three strategies at their BASE case.
BULL_CHURN_SAVE_RATE = STRATEGY1_SAVE_RATE["base"]
BULL_MIGRATION_RATE = STRATEGY2_CONVERSION_RATE["base"]
BULL_SMB_EXPANSION_UPLIFT = STRATEGY3_SMB_EXPANSION_UPLIFT["base"]
BULL_ENT_CONTRACTION_REDUCTION = STRATEGY3_ENT_CONTRACTION_REDUCTION["base"]


# ---------------------------------------------------------------------------
# Calibration (pure SQL against the warehouse; works for any as_of/window so
# the same code path calibrates the main scenarios AND the backtest)
# ---------------------------------------------------------------------------
def calibrate(con, as_of: pd.Timestamp, window_months: int = WINDOW_MONTHS) -> dict:
    as_of = pd.Timestamp(as_of)
    win_start_month = (as_of.to_period("M") - (window_months - 1)).to_timestamp()
    win_start_prior_end = win_start_month - pd.Timedelta(days=1)

    new_df = con.execute(
        """
        SELECT date_trunc('month', start_date)::DATE AS month, segment, plan_type,
               COUNT(*) AS n, AVG(mrr) AS avg_mrr
        FROM fct_subscriptions
        WHERE period_number = 1 AND start_date >= ? AND start_date <= ?
          AND segment IN ('B2C','SMB','Enterprise')
        GROUP BY 1, 2, 3
        """,
        [win_start_month.date(), as_of.date()],
    ).fetchdf()

    churn_df = con.execute(
        """
        SELECT segment, plan_type,
               SUM(CASE WHEN status = 'churned' THEN 1 ELSE 0 END) AS churned,
               COUNT(*) AS n
        FROM fct_subscriptions
        WHERE status IN ('renewed', 'churned') AND end_date >= ? AND end_date <= ?
          AND segment IN ('B2C','SMB','Enterprise')
        GROUP BY 1, 2
        """,
        [win_start_month.date(), as_of.date()],
    ).fetchdf()

    ec_df = con.execute(
        """
        WITH base AS (
            SELECT user_id, segment, mrr AS start_mrr
            FROM fct_customer_mrr_monthly
            WHERE month_end = ? AND mrr > 0 AND segment IN ('SMB', 'Enterprise')
        ), endm AS (
            SELECT user_id, mrr AS end_mrr FROM fct_customer_mrr_monthly WHERE month_end = ?
        )
        SELECT b.segment,
               SUM(b.start_mrr) AS start_mrr,
               SUM(CASE WHEN COALESCE(e.end_mrr, 0) > b.start_mrr
                        THEN COALESCE(e.end_mrr, 0) - b.start_mrr ELSE 0 END) AS expansion_mrr,
               SUM(CASE WHEN COALESCE(e.end_mrr, 0) < b.start_mrr AND COALESCE(e.end_mrr, 0) > 0
                        THEN b.start_mrr - COALESCE(e.end_mrr, 0) ELSE 0 END) AS contraction_mrr
        FROM base b LEFT JOIN endm e ON e.user_id = b.user_id
        GROUP BY 1
        """,
        [win_start_prior_end.date(), as_of.date()],
    ).fetchdf()

    stock_df = con.execute(
        """
        SELECT segment, plan_type, COUNT(*) AS customers, SUM(mrr) AS mrr
        FROM fct_subscriptions
        WHERE start_date <= ? AND end_date > ? AND segment IN ('B2C','SMB','Enterprise')
        GROUP BY 1, 2
        """,
        [as_of.date(), as_of.date()],
    ).fetchdf()

    return dict(
        as_of=as_of, window_months=window_months,
        win_start_month=win_start_month, win_start_prior_end=win_start_prior_end,
        new_df=new_df, churn_df=churn_df, ec_df=ec_df, stock_df=stock_df,
    )


def monthly_equiv(rate: float, plan: str) -> float:
    """Annual-plan churn is observed per-YEAR; convert to a monthly-equivalent
    rate (Proposed A-19c). Monthly-plan churn is already a monthly rate."""
    if plan == "annual":
        rate = min(max(rate, 0.0), 0.999999)
        return 1 - (1 - rate) ** (1 / 12)
    return rate


def derive_base_rates(calib: dict) -> dict:
    """Turns calibrate()'s raw query results into per-bucket rates + per-segment
    new-customer trend, ready to feed compute_month_rates()."""
    new_df, churn_df, ec_df, stock_df = calib["new_df"], calib["churn_df"], calib["ec_df"], calib["stock_df"]
    window_months = calib["window_months"]

    rates = {}
    for seg, plan in BUCKETS:
        sub = new_df[(new_df.segment == seg) & (new_df.plan_type == plan)]
        n_new = sub.n.sum()
        arpa_new = (sub.n * sub.avg_mrr).sum() / n_new if n_new > 0 else 0.0

        cdf = churn_df[(churn_df.segment == seg) & (churn_df.plan_type == plan)]
        churn_raw = (cdf.churned.sum() / cdf.n.sum()) if cdf.n.sum() > 0 else 0.0
        churn_rate = monthly_equiv(churn_raw, plan)

        st = stock_df[(stock_df.segment == seg) & (stock_df.plan_type == plan)]
        customers0 = float(st.customers.sum())
        mrr0 = float(st.mrr.sum())

        rates[(seg, plan)] = dict(
            n_new_calib=int(n_new), arpa_new=float(arpa_new),
            churn_rate_raw=float(churn_raw), churn_n=int(cdf.n.sum()) if len(cdf) else 0,
            churn_rate_monthly=float(churn_rate),
            customers0=customers0, mrr0=mrr0,
        )

    # plan mix share within each segment (of new customers, over the window)
    for seg in SEGMENTS:
        tot = sum(rates[(seg, p)]["n_new_calib"] for p in PLANS)
        for p in PLANS:
            rates[(seg, p)]["plan_mix_share"] = (
                rates[(seg, p)]["n_new_calib"] / tot if tot > 0 else (1.0 if p == "monthly" else 0.0)
            )

    # expansion / contraction, B2B only, monthly-equivalent (linear /window_months
    # -- magnitudes are small (<3%/6mo) so linear de-annualization is adequate)
    for seg, plan in BUCKETS:
        if seg in B2B_SEGMENTS:
            e = ec_df[ec_df.segment == seg]
            start_mrr = float(e.start_mrr.sum()) if len(e) else 0.0
            exp_mrr = float(e.expansion_mrr.sum()) if len(e) else 0.0
            con_mrr = float(e.contraction_mrr.sum()) if len(e) else 0.0
            rates[(seg, plan)]["expansion_rate_monthly"] = (exp_mrr / start_mrr / window_months) if start_mrr > 0 else 0.0
            rates[(seg, plan)]["contraction_rate_monthly"] = (con_mrr / start_mrr / window_months) if start_mrr > 0 else 0.0
        else:
            rates[(seg, plan)]["expansion_rate_monthly"] = 0.0
            rates[(seg, plan)]["contraction_rate_monthly"] = 0.0

    # per-segment new-customer total (avg + linear trend slope) over the window
    new_seg = {}
    for seg in SEGMENTS:
        s = new_df[new_df.segment == seg].groupby("month")["n"].sum().sort_index()
        # pad any missing calibration month with 0 so the trend fit uses window_months points
        months = pd.date_range(calib["win_start_month"], periods=window_months, freq="MS")
        y = np.array([float(s.get(m, 0.0)) for m in months])
        x = np.arange(window_months)
        avg = float(y.mean())
        slope = float(np.polyfit(x, y, 1)[0]) if window_months > 1 else 0.0
        new_seg[seg] = dict(avg=avg, slope=slope, series=y.tolist())

    stock0 = {(seg, plan): dict(customers=rates[(seg, plan)]["customers0"], mrr=rates[(seg, plan)]["mrr0"])
              for seg, plan in BUCKETS}

    return dict(rates=rates, new_seg=new_seg, stock0=stock0, window_months=window_months)


# ---------------------------------------------------------------------------
# Scenario / strategy parameter sets
# ---------------------------------------------------------------------------
def default_params() -> dict:
    return dict(
        churn_multiplier={b: 1.0 for b in BUCKETS},
        churn_save_rate={b: 0.0 for b in BUCKETS},
        expansion_multiplier={b: 1.0 for b in BUCKETS},
        contraction_multiplier={b: 1.0 for b in BUCKETS},
        migration_rate={b: 0.0 for b in BUCKETS},
        acquisition_mode="flat",       # 'flat' | 'trend' | 'flat_reduced'
        acquisition_reduction=0.0,
    )


def scenario_params(name: str) -> dict:
    p = default_params()
    if name == "base":
        return p
    if name == "bear":
        p["churn_multiplier"] = {b: 1 + BEAR_CHURN_RELATIVE_INCREASE for b in BUCKETS}
        for seg in B2B_SEGMENTS:
            for plan in PLANS:
                p["expansion_multiplier"][(seg, plan)] = BEAR_EXPANSION_MULTIPLIER
        p["acquisition_mode"] = "flat_reduced"
        p["acquisition_reduction"] = BEAR_ACQUISITION_RELATIVE_DECLINE
        return p
    if name == "bull":
        for seg in SEGMENTS:
            p["churn_save_rate"][(seg, "monthly")] = BULL_CHURN_SAVE_RATE
        p["migration_rate"][("B2C", "monthly")] = BULL_MIGRATION_RATE
        for plan in PLANS:
            p["expansion_multiplier"][("SMB", plan)] = 1 + BULL_SMB_EXPANSION_UPLIFT
            p["contraction_multiplier"][("Enterprise", plan)] = 1 - BULL_ENT_CONTRACTION_REDUCTION
        p["acquisition_mode"] = "trend"
        return p
    raise ValueError(name)


def strategy_params(strategy: str, case: str) -> dict:
    p = default_params()  # isolated on top of BASE acquisition (flat), per the brief
    if strategy == "strategy_1_engagement_alert":
        rate = STRATEGY1_SAVE_RATE[case]
        for seg in SEGMENTS:
            p["churn_save_rate"][(seg, "monthly")] = rate
    elif strategy == "strategy_2_annual_migration":
        rate = STRATEGY2_CONVERSION_RATE[case]
        p["migration_rate"][("B2C", "monthly")] = rate
    elif strategy == "strategy_3_b2b_playbook":
        uplift = STRATEGY3_SMB_EXPANSION_UPLIFT[case]
        reduction = STRATEGY3_ENT_CONTRACTION_REDUCTION[case]
        for plan in PLANS:
            p["expansion_multiplier"][("SMB", plan)] = 1 + uplift
            p["contraction_multiplier"][("Enterprise", plan)] = 1 - reduction
    else:
        raise ValueError(strategy)
    return p


def acquisition_for_month(seg_new: dict, params: dict, m: int, window_months: int) -> float:
    avg, slope = seg_new["avg"], seg_new["slope"]
    mode = params["acquisition_mode"]
    if mode == "flat":
        return avg
    if mode == "flat_reduced":
        return avg * (1 - params["acquisition_reduction"])
    if mode == "trend":
        trend_val = avg + slope * (((window_months - 1) / 2) + m)
        return max(avg, trend_val)  # Bull never falls below the current run-rate
    raise ValueError(mode)


def compute_month_rates(base: dict, params: dict, m: int, no_new: bool = False, zero_expansion: bool = False) -> dict:
    rates_out = {}
    for seg in SEGMENTS:
        new_total = 0.0 if no_new else acquisition_for_month(base["new_seg"][seg], params, m, base["window_months"])
        for plan in PLANS:
            b = (seg, plan)
            br = base["rates"][b]
            churn = br["churn_rate_monthly"] * params["churn_multiplier"][b] * (1 - params["churn_save_rate"][b])
            exp_r = 0.0 if zero_expansion else br["expansion_rate_monthly"] * params["expansion_multiplier"][b]
            con_r = br["contraction_rate_monthly"] * params["contraction_multiplier"][b]
            new_cust = 0.0 if no_new else new_total * br["plan_mix_share"]
            rates_out[b] = dict(
                churn_rate=churn, expansion_rate=exp_r, contraction_rate=con_r,
                new_customers=new_cust, arpa_new=br["arpa_new"],
                migration_rate=params["migration_rate"][b],
            )
    return rates_out


# ---------------------------------------------------------------------------
# Simulation engine
# ---------------------------------------------------------------------------
def simulate(stock0: dict, base: dict, params: dict, n_months: int,
             no_new: bool = False, zero_expansion: bool = False) -> tuple[pd.DataFrame, dict]:
    state = {k: dict(v) for k, v in stock0.items()}
    rows = []
    for m in range(1, n_months + 1):
        rates = compute_month_rates(base, params, m, no_new=no_new, zero_expansion=zero_expansion)
        month_rows = {}
        migration_out = {}
        for bucket, s in state.items():
            r = rates[bucket]
            cust0, mrr0 = s["customers"], s["mrr"]
            arpa0 = mrr0 / cust0 if cust0 > 1e-9 else 0.0

            churn_cust = cust0 * r["churn_rate"]
            churn_mrr = churn_cust * arpa0
            ret_cust = cust0 - churn_cust
            ret_mrr = mrr0 - churn_mrr

            exp_mrr = ret_mrr * r["expansion_rate"]
            con_mrr = ret_mrr * r["contraction_rate"]
            ret_mrr = ret_mrr + exp_mrr - con_mrr

            mig_rate = r["migration_rate"]
            mig_cust = ret_cust * mig_rate if mig_rate > 0 else 0.0
            mig_mrr_out = mig_cust * arpa0
            ret_cust -= mig_cust
            ret_mrr -= mig_mrr_out

            new_cust = r["new_customers"]
            new_mrr = new_cust * r["arpa_new"]

            close_cust = ret_cust + new_cust
            close_mrr = ret_mrr + new_mrr

            month_rows[bucket] = dict(
                opening_customers=cust0, opening_mrr=mrr0,
                new_customers=new_cust, new_mrr=new_mrr,
                expansion_mrr=exp_mrr, contraction_mrr=con_mrr,
                churn_customers=churn_cust, churn_mrr=churn_mrr,
                migration_out_customers=mig_cust, migration_out_mrr=mig_mrr_out,
                migration_in_customers=0.0, migration_in_mrr=0.0,
                closing_customers=close_cust, closing_mrr=close_mrr,
            )
            migration_out[bucket] = (mig_cust, mig_mrr_out)

        mig_cust, _ = migration_out.get(("B2C", "monthly"), (0.0, 0.0))
        if mig_cust > 1e-9:
            dest = ("B2C", "annual")
            mig_mrr_in = mig_cust * B2C_ANNUAL_PRICE
            month_rows[dest]["migration_in_customers"] += mig_cust
            month_rows[dest]["migration_in_mrr"] += mig_mrr_in
            month_rows[dest]["closing_customers"] += mig_cust
            month_rows[dest]["closing_mrr"] += mig_mrr_in

        new_state = {}
        for bucket, row in month_rows.items():
            new_state[bucket] = dict(customers=row["closing_customers"], mrr=row["closing_mrr"])
            rows.append(dict(month_index=m, segment=bucket[0], plan_type=bucket[1], **row))
        state = new_state

    return pd.DataFrame(rows), state


def add_rollups(panel: pd.DataFrame) -> pd.DataFrame:
    """panel: one row per (month_index, segment, plan_type). Adds plan_type='ALL'
    per segment, plus segment='B2B' and segment='Total' (both plan_type='ALL')."""
    num_cols = [c for c in panel.columns if c not in ("month_index", "segment", "plan_type")]
    out = [panel.copy()]

    per_seg = panel.groupby(["month_index", "segment"], as_index=False)[num_cols].sum()
    per_seg["plan_type"] = "ALL"
    out.append(per_seg)

    b2b = panel[panel.segment.isin(B2B_SEGMENTS)].groupby(["month_index"], as_index=False)[num_cols].sum()
    b2b["segment"] = "B2B"
    b2b["plan_type"] = "ALL"
    out.append(b2b)

    total = panel.groupby(["month_index"], as_index=False)[num_cols].sum()
    total["segment"] = "Total"
    total["plan_type"] = "ALL"
    out.append(total)

    return pd.concat(out, ignore_index=True, sort=False)


def cohort_ndr_grr(stock0: dict, base: dict, params: dict, n_months: int) -> pd.DataFrame:
    """Fixed Apr-24 base, no new customers. NDR run = normal rates; GRR run =
    same rates but expansion forced to 0 (M-09 logic), both via simulate()."""
    ndr_panel, _ = simulate(stock0, base, params, n_months, no_new=True, zero_expansion=False)
    grr_panel, _ = simulate(stock0, base, params, n_months, no_new=True, zero_expansion=True)
    ndr_r = add_rollups(ndr_panel)
    grr_r = add_rollups(grr_panel)

    opening0 = {}
    for seg in SEGMENTS + ["B2B", "Total"]:
        opening0[seg] = ndr_r[(ndr_r.month_index == 1) & (ndr_r.segment == seg) & (ndr_r.plan_type == "ALL")]["opening_mrr"].sum()

    rows = []
    for k in (6, 12):
        if k > n_months:
            continue
        for seg in SEGMENTS + ["B2B", "Total"]:
            close_ndr = ndr_r[(ndr_r.month_index == k) & (ndr_r.segment == seg) & (ndr_r.plan_type == "ALL")]["closing_mrr"].sum()
            close_grr = grr_r[(grr_r.month_index == k) & (grr_r.segment == seg) & (grr_r.plan_type == "ALL")]["closing_mrr"].sum()
            start = opening0[seg]
            rows.append(dict(
                month_k=k, segment=seg,
                start_mrr=start, ndr_mrr=close_ndr, grr_mrr=close_grr,
                ndr=(close_ndr / start) if start > 0 else np.nan,
                grr=(close_grr / start) if start > 0 else np.nan,
            ))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Drivers table
# ---------------------------------------------------------------------------
def build_drivers_table(base: dict) -> pd.DataFrame:
    rows = []
    src_rates = f"fct_subscriptions renewal-basis + fct_customer_mrr_monthly $ decomposition, T{WINDOW_MONTHS}M window ending {AS_OF_MAIN.date()}"
    for (seg, plan), r in base["rates"].items():
        rows.append(dict(scenario="base", segment=seg, plan_type=plan, case="base",
                          driver="churn_rate_monthly", value=r["churn_rate_monthly"], unit="fraction/month",
                          source=f"{src_rates}; raw rate {r['churn_rate_raw']:.4f} on n={r['churn_n']}"
                                 + (" (annualized->monthly via 1-(1-r)^(1/12), A-19c)" if plan == "annual" else "")))
        rows.append(dict(scenario="base", segment=seg, plan_type=plan, case="base",
                          driver="arpa_new_customer", value=r["arpa_new"], unit="$/month",
                          source=f"avg mrr of period_number=1 subs, T{WINDOW_MONTHS}M window, n={r['n_new_calib']}"))
        rows.append(dict(scenario="base", segment=seg, plan_type=plan, case="base",
                          driver="plan_mix_share", value=r["plan_mix_share"], unit="fraction of segment new custs",
                          source=f"share of new customers on this plan, T{WINDOW_MONTHS}M window"))
        rows.append(dict(scenario="base", segment=seg, plan_type=plan, case="base",
                          driver="expansion_rate_monthly", value=r["expansion_rate_monthly"], unit="fraction/month of retained MRR",
                          source="mart_a3_03-style $ decomposition /6 (B2B only; B2C=0 by construction, verified fact)"))
        rows.append(dict(scenario="base", segment=seg, plan_type=plan, case="base",
                          driver="contraction_rate_monthly", value=r["contraction_rate_monthly"], unit="fraction/month of retained MRR",
                          source="mart_a3_03-style $ decomposition /6 (B2B only; B2C=0 by construction, verified fact)"))
    for seg in SEGMENTS:
        ns = base["new_seg"][seg]
        rows.append(dict(scenario="base", segment=seg, plan_type="ALL", case="base",
                          driver="new_customers_per_month_avg", value=ns["avg"], unit="customers/month",
                          source=f"T{WINDOW_MONTHS}M average new paying customers (mart_a2_01-style), series={['%.0f' % v for v in ns['series']]}"))
        rows.append(dict(scenario="base", segment=seg, plan_type="ALL", case="base",
                          driver="new_customers_trend_slope", value=ns["slope"], unit="customers/month per month",
                          source=f"OLS linear trend over the T{WINDOW_MONTHS}M window; used flat in Base, extrapolated in Bull (floored at Base run-rate)"))

    rows.append(dict(scenario="bear", segment="ALL", plan_type="ALL", case="base",
                      driver="churn_relative_increase", value=BEAR_CHURN_RELATIVE_INCREASE, unit="relative %",
                      source="Proposed A-19: largest positive MoM deviation from the T12M mean in B2C-monthly logo churn (see results.md)"))
    rows.append(dict(scenario="bear", segment="ALL", plan_type="ALL", case="base",
                      driver="acquisition_relative_decline", value=BEAR_ACQUISITION_RELATIVE_DECLINE, unit="relative %",
                      source="Proposed A-19b: ~1.5x the worst observed single-month new-customer decline (-6.3%), sustained for 12mo"))
    for seg in B2B_SEGMENTS:
        rows.append(dict(scenario="bear", segment=seg, plan_type="ALL", case="base",
                          driver="expansion_multiplier", value=BEAR_EXPANSION_MULTIPLIER, unit="multiplier",
                          source="brief: bear = expansion halved"))

    rows.append(dict(scenario="bull", segment="ALL", plan_type="monthly", case="base",
                      driver="churn_save_rate", value=BULL_CHURN_SAVE_RATE, unit="fraction saved",
                      source="= WP23 Strategy-1 base case"))
    rows.append(dict(scenario="bull", segment="B2C", plan_type="monthly", case="base",
                      driver="migration_rate_monthly", value=BULL_MIGRATION_RATE, unit="fraction/month",
                      source="= WP23 Strategy-2 base case"))
    rows.append(dict(scenario="bull", segment="SMB", plan_type="ALL", case="base",
                      driver="expansion_uplift", value=BULL_SMB_EXPANSION_UPLIFT, unit="relative %",
                      source="= WP23 Strategy-3 base case"))
    rows.append(dict(scenario="bull", segment="Enterprise", plan_type="ALL", case="base",
                      driver="contraction_reduction", value=BULL_ENT_CONTRACTION_REDUCTION, unit="relative %",
                      source="= WP23 Strategy-3 base case"))
    rows.append(dict(scenario="bull", segment="ALL", plan_type="ALL", case="base",
                      driver="acquisition_mode", value=1.0, unit="flag (trend=1)",
                      source="Bull continues the observed T6M linear acquisition trend, floored at the Base run-rate"))

    for case, v in STRATEGY1_SAVE_RATE.items():
        rows.append(dict(scenario="strategy_1_engagement_alert", segment="ALL", plan_type="monthly", case=case,
                          driver="save_rate", value=v, unit="fraction of flagged would-be churners saved",
                          source="Industry-typical outbound-save-rate range (brief-stated 10-30%); applied to monthly-plan churn only (D-18 in-period signal)"))
    for case, v in STRATEGY2_CONVERSION_RATE.items():
        rows.append(dict(scenario="strategy_2_annual_migration", segment="B2C", plan_type="monthly", case=case,
                          driver="conversion_rate_monthly", value=v, unit="fraction/month of retained monthly base",
                          source="Assumed offer take-up range (no direct data); ARPA drops 49->33.25 on conversion, churn drops to the annual monthly-equivalent rate"))
    for case, v in STRATEGY3_SMB_EXPANSION_UPLIFT.items():
        rows.append(dict(scenario="strategy_3_b2b_playbook", segment="SMB", plan_type="ALL", case=case,
                          driver="expansion_uplift", value=v, unit="relative % of observed SMB expansion rate",
                          source="QBR / seat-expansion motion; range reflects the observed 129-event SMB expansion base (WP22)"))
    for case, v in STRATEGY3_ENT_CONTRACTION_REDUCTION.items():
        rows.append(dict(scenario="strategy_3_b2b_playbook", segment="Enterprise", plan_type="ALL", case=case,
                          driver="contraction_reduction", value=v, unit="relative % of observed Enterprise contraction rate",
                          source="2nd-renewal save motion targeting WP22's identified Enterprise contraction window"))

    rows.append(dict(scenario="all", segment="ALL", plan_type="ALL", case="base",
                      driver="calibration_window_months", value=WINDOW_MONTHS, unit="months",
                      source=f"T6M convention (WP21/WP22); window ends {AS_OF_MAIN.date()}"))

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Backtest
# ---------------------------------------------------------------------------
def run_backtest(con) -> tuple[pd.DataFrame, pd.DataFrame]:
    calib_bt = calibrate(con, BACKTEST_AS_OF, BACKTEST_WINDOW_MONTHS)
    base_bt = derive_base_rates(calib_bt)
    panel, _ = simulate(base_bt["stock0"], base_bt, scenario_params("base"), BACKTEST_HORIZON)
    proj = add_rollups(panel)

    rows = []
    for m in range(1, BACKTEST_HORIZON + 1):
        month_end = (BACKTEST_AS_OF + pd.DateOffset(months=m) + pd.offsets.MonthEnd(0))
        actual = con.execute(
            """
            SELECT segment, COUNT(*) AS customers, SUM(mrr) AS mrr
            FROM fct_subscriptions
            WHERE start_date <= ? AND end_date > ? AND segment IN ('B2C','SMB','Enterprise')
            GROUP BY 1
            """,
            [month_end.date(), month_end.date()],
        ).fetchdf()
        actual_roll = {
            "B2C": actual[actual.segment == "B2C"], "SMB": actual[actual.segment == "SMB"],
            "Enterprise": actual[actual.segment == "Enterprise"],
        }
        for seg in SEGMENTS + ["B2B", "Total"]:
            if seg == "B2B":
                a = actual[actual.segment.isin(B2B_SEGMENTS)]
            elif seg == "Total":
                a = actual
            else:
                a = actual_roll[seg]
            actual_mrr = float(a.mrr.sum())
            actual_cust = float(a.customers.sum())
            prow = proj[(proj.month_index == m) & (proj.segment == seg) & (proj.plan_type == "ALL")]
            proj_mrr = float(prow.closing_mrr.sum())
            proj_cust = float(prow.closing_customers.sum())
            rows.append(dict(
                month_index=m, month_end=month_end.date(), segment=seg,
                actual_mrr=actual_mrr, projected_mrr=proj_mrr,
                ape_mrr_pct=abs(proj_mrr - actual_mrr) / actual_mrr * 100 if actual_mrr else np.nan,
                actual_customers=actual_cust, projected_customers=proj_cust,
                ape_customers_pct=abs(proj_cust - actual_cust) / actual_cust * 100 if actual_cust else np.nan,
            ))
    backtest_detail = pd.DataFrame(rows)
    backtest_summary = (
        backtest_detail.groupby("segment", as_index=False)
        .agg(mape_mrr_pct=("ape_mrr_pct", "mean"), mape_customers_pct=("ape_customers_pct", "mean"),
             n_months=("month_index", "count"))
    )
    return backtest_detail, backtest_summary


# ---------------------------------------------------------------------------
# Main build()
# ---------------------------------------------------------------------------
def build(con) -> None:
    calib_main = calibrate(con, AS_OF_MAIN, WINDOW_MONTHS)
    base = derive_base_rates(calib_main)

    mrr_apr24 = {seg: sum(base["stock0"][(seg, p)]["mrr"] for p in PLANS) for seg in SEGMENTS}
    mrr_apr24["B2B"] = sum(mrr_apr24[s] for s in B2B_SEGMENTS)
    mrr_apr24["Total"] = sum(mrr_apr24[s] for s in SEGMENTS)

    scenario_panels = {}
    scenario_cohorts = {}
    for name in ("base", "bull", "bear"):
        params = scenario_params(name)
        panel, _ = simulate(base["stock0"], base, params, N_MONTHS_MAIN)
        scenario_panels[name] = add_rollups(panel)
        scenario_panels[name].insert(0, "scenario", name)
        scenario_cohorts[name] = cohort_ndr_grr(base["stock0"], base, params, N_MONTHS_MAIN)
        scenario_cohorts[name].insert(0, "scenario", name)

    projection_monthly = pd.concat(scenario_panels.values(), ignore_index=True)
    projection_monthly["month_end"] = projection_monthly["month_index"].apply(
        lambda m: (AS_OF_MAIN + pd.DateOffset(months=m) + pd.offsets.MonthEnd(0)).date()
    )
    cols = ["scenario", "month_index", "month_end", "segment", "plan_type",
            "opening_customers", "opening_mrr", "new_customers", "new_mrr",
            "expansion_mrr", "contraction_mrr", "churn_customers", "churn_mrr",
            "migration_out_customers", "migration_out_mrr", "migration_in_customers", "migration_in_mrr",
            "closing_customers", "closing_mrr"]
    projection_monthly = projection_monthly[cols]

    cohort_all = pd.concat(scenario_cohorts.values(), ignore_index=True)

    summary_rows = []
    for name in ("base", "bull", "bear"):
        pr = scenario_panels[name]
        m12 = pr[(pr.month_index == 12) & (pr.plan_type == "ALL")]
        coh = cohort_all[cohort_all.scenario == name]
        for seg in SEGMENTS + ["B2B", "Total"]:
            row = m12[m12.segment == seg].iloc[0]
            mrr_apr25 = float(row.closing_mrr)
            subs_apr25 = float(row.closing_customers)
            growth_pct = (mrr_apr25 / mrr_apr24[seg] - 1) * 100 if mrr_apr24[seg] else np.nan
            c6 = coh[(coh.month_k == 6) & (coh.segment == seg)]
            c12 = coh[(coh.month_k == 12) & (coh.segment == seg)]
            summary_rows.append(dict(
                scenario=name, segment=seg,
                mrr_apr24_actual=mrr_apr24[seg], mrr_apr25=mrr_apr25, mrr_growth_pct=growth_pct,
                subs_apr24_actual=sum(base["stock0"][(seg, p)]["customers"] for p in PLANS) if seg in SEGMENTS
                                   else (sum(base["stock0"][(s, p)]["customers"] for s in B2B_SEGMENTS for p in PLANS) if seg == "B2B"
                                         else sum(v["customers"] for v in base["stock0"].values())),
                subs_apr25=subs_apr25,
                forward_ndr_m6=float(c6.ndr.iloc[0]) if len(c6) else np.nan,
                forward_grr_m6=float(c6.grr.iloc[0]) if len(c6) else np.nan,
                forward_ndr_m12=float(c12.ndr.iloc[0]) if len(c12) else np.nan,
                forward_grr_m12=float(c12.grr.iloc[0]) if len(c12) else np.nan,
            ))
    scenario_summary = pd.DataFrame(summary_rows)

    drivers = build_drivers_table(base)

    # ---- WP23 strategies, sized with the same engine, isolated vs. Base ----
    base_params = scenario_params("base")
    base_panel_roll = scenario_panels["base"]
    base_cohort = cohort_all[cohort_all.scenario == "base"]

    def total_mrr(panel_roll, month_idx, seg):
        row = panel_roll[(panel_roll.month_index == month_idx) & (panel_roll.segment == seg) & (panel_roll.plan_type == "ALL")]
        return float(row.closing_mrr.sum())

    strategy_meta = {
        "strategy_1_engagement_alert": dict(
            segments=["B2C", "SMB", "Enterprise", "Total"], effort="Low",
            time_to_impact_months=1,
            kpi="Save rate on flagged subs; # flagged/month; realized churn rate vs. predicted",
            risk="D-18 caveat: same-period engagement signal, expect production AUC ~0.70-0.85, not the in-sample 0.9997; false-positive outreach cost"),
        "strategy_2_annual_migration": dict(
            segments=["B2C", "Total"], effort="Medium",
            time_to_impact_months=6,
            kpi="Monthly->annual conversion rate; cash collected upfront; blended B2C ARPA",
            risk="Short-term MRR dilution (49->33.25); cannibalizes monthly MRR before the churn benefit compounds; refund/cancellation risk on annual prepay"),
        "strategy_3_b2b_playbook": dict(
            segments=["SMB", "Enterprise", "B2B", "Total"], effort="Medium",
            time_to_impact_months=3,
            kpi="Seats/account (SMB); Enterprise 2nd-renewal retention rate; expansion $ and contraction $ per WP22 waterfall",
            risk="Small-n Enterprise base (WP20/22 caveat) means realized results can differ a lot from the point estimate; requires CSM/AM capacity"),
    }

    strategy_rows = []
    for strategy, meta in strategy_meta.items():
        for case in ("low", "base", "high"):
            params = strategy_params(strategy, case)
            panel, _ = simulate(base["stock0"], base, params, N_MONTHS_MAIN)
            panel_roll = add_rollups(panel)
            coh = cohort_ndr_grr(base["stock0"], base, params, N_MONTHS_MAIN)
            for seg in meta["segments"]:
                mrr6_s, mrr6_b = total_mrr(panel_roll, 6, seg), total_mrr(base_panel_roll, 6, seg)
                mrr12_s, mrr12_b = total_mrr(panel_roll, 12, seg), total_mrr(base_panel_roll, 12, seg)
                ndr6_s = coh[(coh.month_k == 6) & (coh.segment == seg)].ndr
                ndr6_b = base_cohort[(base_cohort.month_k == 6) & (base_cohort.segment == seg)].ndr
                ndr12_s = coh[(coh.month_k == 12) & (coh.segment == seg)].ndr
                ndr12_b = base_cohort[(base_cohort.month_k == 12) & (base_cohort.segment == seg)].ndr
                strategy_rows.append(dict(
                    strategy=strategy, case=case, segment=seg,
                    mrr_delta_m6=mrr6_s - mrr6_b,
                    mrr_delta_pct_m6=(mrr6_s / mrr6_b - 1) * 100 if mrr6_b else np.nan,
                    mrr_delta_m12=mrr12_s - mrr12_b,
                    mrr_delta_pct_m12=(mrr12_s / mrr12_b - 1) * 100 if mrr12_b else np.nan,
                    ndr_delta_pp_m6=(float(ndr6_s.iloc[0]) - float(ndr6_b.iloc[0])) * 100 if len(ndr6_s) and len(ndr6_b) else np.nan,
                    ndr_delta_pp_m12=(float(ndr12_s.iloc[0]) - float(ndr12_b.iloc[0])) * 100 if len(ndr12_s) and len(ndr12_b) else np.nan,
                    effort=meta["effort"], time_to_impact_months=meta["time_to_impact_months"],
                    kpi=meta["kpi"], risk=meta["risk"],
                ))
    strategy_impact = pd.DataFrame(strategy_rows)

    backtest_detail, backtest_summary = run_backtest(con)

    # ---- write tables ----
    con.execute("CREATE OR REPLACE TABLE mart_s_01_drivers AS SELECT * FROM drivers")
    con.execute("CREATE OR REPLACE TABLE mart_s_02_projection_monthly AS SELECT * FROM projection_monthly")
    con.execute("CREATE OR REPLACE TABLE mart_s_03_scenario_summary AS SELECT * FROM scenario_summary")
    con.execute("CREATE OR REPLACE TABLE mart_s_04_strategy_impact AS SELECT * FROM strategy_impact")
    con.execute("CREATE OR REPLACE TABLE mart_s_05_backtest AS SELECT * FROM backtest_detail")
    con.execute("CREATE OR REPLACE TABLE mart_s_06_backtest_summary AS SELECT * FROM backtest_summary")
