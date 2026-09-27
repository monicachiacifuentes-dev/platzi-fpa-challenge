#!/usr/bin/env python
"""
WP20 -- cohort pivots, cohort-risk digging, engagement-truncation check, and the
May-2024 at-risk summary/CSV with plain-language main driver labels.

Reads from work/WP20_cohorts_churn/dev.duckdb (built by dev_build.py + churn_model.py).
Writes CSVs and PNGs into work/WP20_cohorts_churn/.

Usage:
    export PYTHONIOENCODING=utf-8
    ./.venv/Scripts/python.exe work/WP20_cohorts_churn/cohort_analysis.py
"""
from pathlib import Path

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

WORK_DIR = Path(__file__).resolve().parent
DEV_DB = WORK_DIR / "dev.duckdb"

BLUES = plt.get_cmap("Blues")


def cohort_pivots(con):
    df = con.sql("SELECT * FROM mart_a1_01_cohort_retention").df()
    df["cohort_month"] = pd.to_datetime(df["cohort_month"]).dt.strftime("%Y-%m")

    for seg in ["Total", "B2C", "B2B"]:
        sub = df[df.segment_group == seg]
        logo_piv = sub.pivot(index="cohort_month", columns="month_k", values="logo_retention")
        dollar_piv = sub.pivot(index="cohort_month", columns="month_k", values="dollar_retention")
        logo_piv.to_csv(WORK_DIR / f"cohort_pivot_logo_{seg}.csv")
        dollar_piv.to_csv(WORK_DIR / f"cohort_pivot_dollar_{seg}.csv")
        print(f"wrote cohort_pivot_logo_{seg}.csv / cohort_pivot_dollar_{seg}.csv "
              f"({logo_piv.shape[0]} cohorts x {logo_piv.shape[1]} ages)")

    return df


def heatmap(ax, piv, title, vmin, vmax, fmt="{:.0%}"):
    im = ax.imshow(piv.values, aspect="auto", cmap=BLUES, vmin=vmin, vmax=vmax)
    ax.set_xticks(range(piv.shape[1]))
    ax.set_xticklabels(piv.columns, fontsize=7)
    ax.set_yticks(range(piv.shape[0]))
    ax.set_yticklabels(piv.index, fontsize=7)
    ax.set_xlabel("Months since signup (k)", fontsize=8)
    ax.set_title(title, fontsize=10)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            if not np.isnan(v):
                color = "white" if v > (vmin + vmax) / 2 * 1.15 else "#1b1b1b"
                ax.text(j, i, fmt.format(v), ha="center", va="center", fontsize=5.5, color=color)
    return im


def plot_cohort_heatmaps(df):
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    total = df[df.segment_group == "Total"]
    logo_piv = total.pivot(index="cohort_month", columns="month_k", values="logo_retention")
    dollar_piv = total.pivot(index="cohort_month", columns="month_k", values="dollar_retention")
    im1 = heatmap(axes[0], logo_piv, "Logo retention by cohort (Total)", 0, 1)
    im2 = heatmap(axes[1], dollar_piv, "$ retention by cohort (Total, incl. expansion)", 0.4, 1.1)
    fig.colorbar(im1, ax=axes[0], fraction=0.046, pad=0.04)
    fig.colorbar(im2, ax=axes[1], fraction=0.046, pad=0.04)
    fig.suptitle("Cohort retention matrix -- signup month x months since signup", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(WORK_DIR / "cohort_heatmap_total.png", dpi=150)
    plt.close(fig)
    print("wrote cohort_heatmap_total.png")

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    b2c = df[df.segment_group == "B2C"].pivot(index="cohort_month", columns="month_k", values="logo_retention")
    b2b = df[df.segment_group == "B2B"].pivot(index="cohort_month", columns="month_k", values="logo_retention")
    im1 = heatmap(axes[0], b2c, "Logo retention -- B2C", 0, 1)
    im2 = heatmap(axes[1], b2b, "Logo retention -- B2B", 0, 1)
    fig.colorbar(im1, ax=axes[0], fraction=0.046, pad=0.04)
    fig.colorbar(im2, ax=axes[1], fraction=0.046, pad=0.04)
    fig.suptitle("Logo retention by cohort -- B2C vs B2B", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(WORK_DIR / "cohort_heatmap_b2c_b2b.png", dpi=150)
    plt.close(fig)
    print("wrote cohort_heatmap_b2c_b2b.png")


def cohort_risk_digging(con):
    """Explains the flagged/most negative-gap cohorts: composition (plan/segment mix) and
    first-period engagement vs the company baseline, and dollar-concentration in small
    cohorts (a churned high-MRR logo)."""
    flags = con.sql("""
        SELECT * FROM mart_a1_02_cohort_risk_flags
        WHERE at_risk_logo OR at_risk_dollar
        ORDER BY segment_group, month_k
    """).df()
    flags.to_csv(WORK_DIR / "cohort_risk_flags_significant.csv", index=False)
    print(f"wrote cohort_risk_flags_significant.csv ({len(flags)} flagged rows)")

    # Composition (plan mix, first-period engagement) for the standout cohorts, vs baseline.
    q = """
    WITH cohort_users AS (
        SELECT user_id, segment, customer_type, date_trunc('month', signup_date) AS cohort_month
        FROM stg_users
    )
    SELECT
        cu.cohort_month, cu.customer_type, isp.plan_type,
        COUNT(*) n,
        round(AVG(isp.active_days), 2) avg_active_days,
        round(AVG(isp.courses_seen), 2) avg_courses,
        round(AVG(isp.materials_seen), 2) avg_materials
    FROM cohort_users cu
    JOIN int_subscription_periods isp ON isp.user_id = cu.user_id AND isp.period_number = 1
    WHERE cu.cohort_month IN (DATE '2023-11-01', DATE '2023-02-01')
    GROUP BY 1, 2, 3
    ORDER BY 1, 2, 3
    """
    comp = con.sql(q).df()
    baseline = con.sql("""
        SELECT customer_type, plan_type, COUNT(*) n,
               round(AVG(active_days), 2) avg_active_days,
               round(AVG(courses_seen), 2) avg_courses,
               round(AVG(materials_seen), 2) avg_materials
        FROM int_subscription_periods WHERE period_number = 1 GROUP BY 1, 2
    """).df()
    comp.to_csv(WORK_DIR / "cohort_risk_composition.csv", index=False)
    baseline.to_csv(WORK_DIR / "cohort_risk_composition_baseline.csv", index=False)
    print("wrote cohort_risk_composition.csv / cohort_risk_composition_baseline.csv")

    # 2023-02 cohort dollar concentration: biggest single-logo MRR drops through month 6
    q2 = """
    WITH cohort AS (SELECT user_id, segment FROM stg_users WHERE date_trunc('month', signup_date) = DATE '2023-02-01')
    SELECT c.user_id, c.segment, f0.mrr AS mrr_k0, f6.mrr AS mrr_k6, f0.mrr - f6.mrr AS mrr_drop
    FROM cohort c
    JOIN fct_customer_mrr_monthly f0 ON f0.user_id = c.user_id AND f0.month_end = DATE '2023-02-28'
    JOIN fct_customer_mrr_monthly f6 ON f6.user_id = c.user_id AND f6.month_end = DATE '2023-08-31'
    ORDER BY mrr_drop DESC LIMIT 10
    """
    con.sql(q2).df().to_csv(WORK_DIR / "cohort_2023_02_concentration.csv", index=False)
    print("wrote cohort_2023_02_concentration.csv")


def engagement_truncation_check(con):
    """Checks whether in-progress ('active') periods show partial/truncated engagement vs
    completed periods, by comparing active_days across elapsed-time buckets. If active_days
    doesn't grow with elapsed time for 'active' rows, the field isn't truncated -- it already
    reflects an assumed full-period value regardless of status."""
    q = """
    SELECT
        status,
        plan_type,
        CASE
            WHEN status <> 'active' THEN 'completed'
            WHEN DATE_DIFF('day', start_date, DATE '2024-04-30') < 10 THEN 'active: <10d elapsed'
            WHEN DATE_DIFF('day', start_date, DATE '2024-04-30') < 20 THEN 'active: 10-20d elapsed'
            ELSE 'active: 20d+ elapsed'
        END AS bucket,
        COUNT(*) n,
        round(AVG(active_days), 2) avg_active_days,
        round(AVG(courses_seen), 2) avg_courses_seen,
        round(AVG(materials_seen), 2) avg_materials_seen
    FROM int_subscription_periods
    WHERE plan_type = 'monthly'
    GROUP BY 1, 2, 3
    ORDER BY 2, 3
    """
    df = con.sql(q).df()
    df.to_csv(WORK_DIR / "engagement_truncation_check.csv", index=False)
    print("wrote engagement_truncation_check.csv")
    print(df.to_string(index=False))

    # plot: avg active_days by elapsed bucket (monthly plan only, active vs completed).
    # Baseline = RENEWED (successful, full-length) periods only -- not blended with churned,
    # which would drag a "completed" average down and understate the comparison.
    active_rows = df[df.bucket.str.startswith("active")]
    renewed_row = df[(df.status == "renewed") & (df.bucket == "completed")]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    order = ["active: <10d elapsed", "active: 10-20d elapsed", "active: 20d+ elapsed"]
    vals = [active_rows[active_rows.bucket == b].avg_active_days.mean() for b in order]
    bars = ax.bar(order, vals, color=BLUES(0.6), width=0.5)
    renewed_avg = renewed_row.avg_active_days.mean()
    ax.axhline(renewed_avg, color="#c0392b", linestyle="--", linewidth=2,
               label=f"Completed & renewed periods avg ({renewed_avg:.1f} days)")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.2, f"{v:.1f}", ha="center", fontsize=9)
    ax.set_ylabel("Avg active_days")
    ax.set_title("Engagement is NOT truncated for in-progress ('active') periods\n"
                  "(monthly plan; active_days barely differs by elapsed time)")
    ax.legend(frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(WORK_DIR / "engagement_truncation_check.png", dpi=150)
    plt.close(fig)
    print("wrote engagement_truncation_check.png")


def roc_plot():
    roc = pd.read_csv(WORK_DIR / "churn_model_roc_points.csv")
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.plot(roc.fpr, roc.tpr, color=BLUES(0.7), linewidth=2, label="Logistic regression (test)")
    ax.plot([0, 1], [0, 1], color="#999999", linestyle="--", linewidth=1, label="Random")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("Churn model ROC curve (test: end_date 2024-01..2024-04)")
    ax.legend(frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(WORK_DIR / "churn_model_roc.png", dpi=150)
    plt.close(fig)
    print("wrote churn_model_roc.png")


# Static labels for features whose contribution sign never flips within a row (0/1 dummies:
# the label already describes "the dummy is on", and main_driver_direction says whether that
# helps or hurts).
DRIVER_LABELS = {
    "contrib_plan_annual": "Annual plan",
    "contrib_is_b2b": "B2B segment",
    "contrib_rc_contraction": "MRR contraction at last renewal",
    "contrib_rc_expansion": "MRR expansion at last renewal",
    "contrib_rc_no_prior_renewal": "First subscription period (no renewal history)",
    "contrib_gw_paypal": "Pays via PayPal",
    "contrib_gw_mercadopago": "Pays via MercadoPago",
    "contrib_gw_payoneer": "Pays via Payoneer",
    "contrib_gw_wire_transfer": "Pays via Wire Transfer",
}

# Direction-aware labels for the 4 standardized continuous features: the SAME column can
# increase or decrease risk depending on whether the customer sits below/above the training
# mean (and, for tenure, the coefficient's sign is even positive, unlike the other three), so
# a fixed "Few X" label would be wrong on some rows. Selected by the sign of the feature's OWN
# z-score (below/above the training mean), independent of the coefficient sign; the separate
# main_driver_direction column (from the contribution's sign) says whether that raises or
# lowers this customer's risk. Tuple = (label when z < 0 / below average, label when z >= 0).
DIRECTIONAL_DRIVER_LABELS = {
    "contrib_active_days": ("Low platform activity (few days active)", "High platform activity (many days active)"),
    "contrib_courses_seen": ("Few courses viewed", "Many courses viewed"),
    "contrib_materials_seen": ("Few materials/lessons viewed", "Many materials/lessons viewed"),
    "contrib_tenure": ("Short tenure (early lifecycle)", "Long tenure (many renewals)"),
}
# Maps each directional contrib column to the raw z-score column used to pick low vs high.
DIRECTIONAL_Z_COL = {
    "contrib_active_days": "active_days_z",
    "contrib_courses_seen": "courses_seen_z",
    "contrib_materials_seen": "materials_seen_z",
    "contrib_tenure": "period_number_z",
}


def may24_summary(con):
    df = con.sql("SELECT * FROM mart_a1_06_may24_churn_risk").df()
    contrib_cols = [c for c in df.columns if c.startswith("contrib_")]

    abs_contribs = df[contrib_cols].abs()
    top_idx = abs_contribs.values.argmax(axis=1)
    top_col = np.array(contrib_cols)[top_idx]
    top_val = df[contrib_cols].values[np.arange(len(df)), top_idx]

    def label_for(row_col, row_idx):
        if row_col in DIRECTIONAL_DRIVER_LABELS:
            z = df.at[row_idx, DIRECTIONAL_Z_COL[row_col]]
            low_label, high_label = DIRECTIONAL_DRIVER_LABELS[row_col]
            return low_label if z < 0 else high_label
        return DRIVER_LABELS[row_col]

    df["main_driver"] = [label_for(c, i) for c, i in zip(top_col, df.index)]
    df["main_driver_direction"] = np.where(top_val > 0, "increases risk", "reduces risk")

    out_cols = ["subscription_id", "user_id", "segment", "customer_type", "plan_type",
                "end_date", "mrr", "prob_churn", "risk_tier", "mrr_at_risk",
                "main_driver", "main_driver_direction"]
    df[out_cols].sort_values("prob_churn", ascending=False).to_csv(
        WORK_DIR / "may24_churn_risk_list.csv", index=False)
    print(f"wrote may24_churn_risk_list.csv ({len(df)} rows)")

    # Summary: n / mrr / expected-churned-mrr by tier x segment
    summary = df.groupby(["risk_tier", "segment"]).agg(
        n_subscriptions=("subscription_id", "count"),
        mrr_total=("mrr", "sum"),
        expected_churned_mrr=("mrr_at_risk", "sum"),
        avg_prob=("prob_churn", "mean"),
    ).reset_index()
    summary.to_csv(WORK_DIR / "may24_risk_summary_tier_segment.csv", index=False)
    print("wrote may24_risk_summary_tier_segment.csv")
    pd.set_option("display.width", 200)
    print(summary.to_string(index=False))

    overall = df.groupby("risk_tier").agg(
        n=("subscription_id", "count"), mrr_total=("mrr", "sum"),
        expected_churned_mrr=("mrr_at_risk", "sum")).reset_index()
    overall.to_csv(WORK_DIR / "may24_risk_summary_tier.csv", index=False)
    print(overall.to_string(index=False))
    print(f"\nTOTAL May-24 population: n={len(df)}, MRR={df.mrr.sum():,.2f}, "
          f"expected churned MRR (sum p*mrr) = {df.mrr_at_risk.sum():,.2f} "
          f"({df.mrr_at_risk.sum()/df.mrr.sum():.1%} of population MRR)")


def main():
    con = duckdb.connect(str(DEV_DB))
    df = cohort_pivots(con)
    plot_cohort_heatmaps(df)
    cohort_risk_digging(con)
    engagement_truncation_check(con)
    roc_plot()
    may24_summary(con)
    con.close()


if __name__ == "__main__":
    main()
