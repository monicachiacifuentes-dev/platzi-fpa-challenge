#!/usr/bin/env python
"""
WP20 (doubles as bonus WP32) -- logistic regression churn model.

Reads mart_a1_03_churn_indicators_base (periods with a KNOWN outcome: status IN
('renewed','churned')) from the WP20 dev DuckDB, builds a small, explainable feature
set, fits a time-based train/test split logistic regression, reports AUC / precision /
recall / coefficients (odds ratios), and re-generates
sql/marts/mart_a1_06_may24_churn_risk.sql with the trained intercept/coefficients and
scaler mean/std baked in as literal constants (so the mart stays a portable, pure-SELECT
SQL file -- no pickled model needed to reproduce scores).

Also scores the May-2024 at-risk population (mart_a1_05) in Python as an independent
cross-check of the SQL-generated scores in mart_a1_06 (see dev_build.py + test_a1_06).

Usage:
    export PYTHONIOENCODING=utf-8
    ./.venv/Scripts/python.exe work/WP20_cohorts_churn/churn_model.py
"""
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, confusion_matrix,
    roc_curve, f1_score,
)

ROOT = Path(__file__).resolve().parent.parent.parent
WORK_DIR = Path(__file__).resolve().parent
DEV_DB = WORK_DIR / "dev.duckdb"
SQL_MART_TEMPLATE_OUT = ROOT / "sql" / "marts" / "mart_a1_06_may24_churn_risk.sql"

NUMERIC_COLS = ["active_days", "courses_seen", "materials_seen", "period_number"]
GATEWAY_BASELINE = "Stripe"
GATEWAY_DUMMIES = ["PayPal", "MercadoPago", "Payoneer", "Wire Transfer"]  # baseline = Stripe
RC_BASELINE = "flat"
RC_DUMMIES = ["contraction", "expansion", "no_prior_renewal"]  # baseline = flat

HIGH_CUTOFF = 0.50
MEDIUM_CUTOFF = 0.25


def build_features(df: pd.DataFrame, scaler_mean=None, scaler_std=None):
    """Builds the model design matrix. If scaler_mean/std are None, fits them (train)."""
    X = pd.DataFrame(index=df.index)
    if scaler_mean is None:
        scaler_mean = df[NUMERIC_COLS].mean()
        scaler_std = df[NUMERIC_COLS].std(ddof=0)
    for c in NUMERIC_COLS:
        X[f"{c}_z"] = (df[c] - scaler_mean[c]) / scaler_std[c]
    X["plan_annual"] = (df["plan_type"] == "annual").astype(int)
    X["is_b2b"] = (df["customer_type"] == "B2B").astype(int)
    for rc in RC_DUMMIES:
        X[f"rc_{rc}"] = (df["renewal_change_bucket"] == rc).astype(int)
    for gw in GATEWAY_DUMMIES:
        col = f"gw_{gw.lower().replace(' ', '_')}"
        X[col] = (df["main_gateway"] == gw).astype(int)
    return X, scaler_mean, scaler_std


def main():
    con = duckdb.connect(str(DEV_DB))
    base = con.sql("SELECT * FROM mart_a1_03_churn_indicators_base").df()
    may24 = con.sql("SELECT * FROM mart_a1_05_may24_population").df()
    con.close()

    train = base[base.model_split == "train"].copy()
    test = base[base.model_split == "test"].copy()
    print(f"train n={len(train)} churn_rate={train.churned.mean():.4f}")
    print(f"test  n={len(test)} churn_rate={test.churned.mean():.4f}")

    X_train, mean_, std_ = build_features(train)
    X_test, _, _ = build_features(test, mean_, std_)
    y_train, y_test = train["churned"].values, test["churned"].values

    feature_names = list(X_train.columns)

    # Primary model: class_weight='balanced'. Justification (business use case = an early-
    # warning / retention outreach list): missing an at-risk customer (false negative) is
    # costlier than a wasted outreach call (false positive), and the base rate is skewed
    # (~9.8% churned in train), so balanced weights push the boundary to catch more churners
    # at the cost of precision. Reported alongside the unweighted model as a sensitivity.
    model_bal = LogisticRegression(class_weight="balanced", max_iter=1000)
    model_bal.fit(X_train, y_train)
    model_plain = LogisticRegression(max_iter=1000)
    model_plain.fit(X_train, y_train)

    results = {}
    for name, model in [("balanced", model_bal), ("unweighted", model_plain)]:
        p_test = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, p_test)
        pred50 = (p_test >= 0.5).astype(int)
        prec = precision_score(y_test, pred50, zero_division=0)
        rec = recall_score(y_test, pred50, zero_division=0)
        f1 = f1_score(y_test, pred50, zero_division=0)
        cm = confusion_matrix(y_test, pred50)
        results[name] = dict(auc=auc, precision_at_50=prec, recall_at_50=rec, f1_at_50=f1,
                              confusion_matrix=cm.tolist())
        print(f"\n[{name}] AUC={auc:.4f} precision@0.5={prec:.4f} recall@0.5={rec:.4f} f1@0.5={f1:.4f}")
        print(f"  confusion matrix [[TN,FP],[FN,TP]] = {cm.tolist()}")

    # Chosen model = balanced (see justification above). Coefficients / odds ratios.
    chosen = model_bal
    coef_table = pd.DataFrame({
        "feature": feature_names,
        "coefficient": chosen.coef_[0],
        "odds_ratio": np.exp(chosen.coef_[0]),
    }).sort_values("coefficient", key=lambda s: s.abs(), ascending=False)
    coef_table.loc[len(coef_table)] = ["intercept", chosen.intercept_[0], np.exp(chosen.intercept_[0])]
    coef_table.to_csv(WORK_DIR / "churn_model_coefficients.csv", index=False)
    print("\nCoefficients (balanced model):")
    print(coef_table.to_string(index=False))

    # ROC points for a plot
    fpr, tpr, thr = roc_curve(y_test, model_bal.predict_proba(X_test)[:, 1])
    pd.DataFrame({"fpr": fpr, "tpr": tpr, "threshold": thr}).to_csv(
        WORK_DIR / "churn_model_roc_points.csv", index=False)

    # Precision/recall at the tier cutoffs actually used downstream (0.25 / 0.50)
    p_test_bal = model_bal.predict_proba(X_test)[:, 1]
    tier_rows = []
    for cutoff in [0.25, 0.50]:
        pred = (p_test_bal >= cutoff).astype(int)
        tier_rows.append(dict(
            threshold=cutoff,
            precision=precision_score(y_test, pred, zero_division=0),
            recall=recall_score(y_test, pred, zero_division=0),
            n_flagged=int(pred.sum()),
            n_test=len(pred),
        ))
    pd.DataFrame(tier_rows).to_csv(WORK_DIR / "churn_model_threshold_metrics.csv", index=False)
    print("\nThreshold metrics:")
    print(pd.DataFrame(tier_rows).to_string(index=False))

    # Save eval summary
    with open(WORK_DIR / "churn_model_eval.json", "w") as f:
        json.dump({
            "train_n": len(train), "test_n": len(test),
            "train_churn_rate": float(train.churned.mean()),
            "test_churn_rate": float(test.churned.mean()),
            "results": results,
            "scaler_mean": mean_.to_dict(),
            "scaler_std": std_.to_dict(),
            "chosen_model": "balanced",
        }, f, indent=2)

    # ---- Score May-2024 population in Python (independent cross-check of the SQL mart) ----
    X_may, _, _ = build_features(may24, mean_, std_)
    p_may = model_bal.predict_proba(X_may)[:, 1]
    may24_scored = may24[["subscription_id", "user_id", "segment", "customer_type",
                           "plan_type", "mrr"]].copy()
    may24_scored["prob_churn_python"] = p_may
    may24_scored.to_csv(WORK_DIR / "may24_scores_python_crosscheck.csv", index=False)
    print(f"\nMay-2024 population scored (Python cross-check): n={len(may24_scored)}, "
          f"mean prob={p_may.mean():.4f}, expected churned MRR (sum p*mrr)="
          f"{(p_may * may24.mrr.values).sum():,.2f}")

    # ---- Generate the portable SQL mart with hardcoded coefficients ----
    generate_sql_mart(chosen, feature_names, mean_, std_)


def generate_sql_mart(model, feature_names, mean_, std_):
    c = dict(zip(feature_names, model.coef_[0]))
    intercept = model.intercept_[0]

    def f(x):
        return f"{x:.10f}"

    sql = f"""-- mart_a1_06_may24_churn_risk: scores mart_a1_05_may24_population (D-08 population)
-- with the trained logistic regression from work/WP20_cohorts_churn/churn_model.py.
-- AUTO-GENERATED by churn_model.py -- do not hand-edit; re-run the script to refresh the
-- coefficients if the model changes. Kept as a pure, portable SELECT (BigQuery-compatible):
-- the model's intercept/coefficients and the StandardScaler mean/std learned on the TRAIN
-- split (end_date < 2024-01-01) are baked in as literal constants, so scoring is just a
-- linear combination + a manual sigmoid (1/(1+EXP(-logit))) -- no ML runtime needed in SQL.
--
-- Encoding (must match churn_model.py's build_features exactly):
--   *_z            = (raw - train_mean) / train_std                (4 standardized numerics)
--   plan_annual    = 1 if plan_type='annual' else 0                 (baseline: monthly)
--   is_b2b         = 1 if customer_type='B2B' else 0                (baseline: B2C; SMB+Enterprise
--                    collapsed into B2B for the model -- simplification, see results.md)
--   rc_*           = 1 if renewal_change_bucket=<label> else 0      (baseline: 'flat';
--                    dummies: contraction / expansion / no_prior_renewal)
--   gw_*           = 1 if main_gateway=<label> else 0               (baseline: Stripe, and a
--                    NULL main_gateway -- 28 of 1,024 May-24 rows, no payment posted yet on an
--                    in-progress period -- also falls to the Stripe baseline; the model never
--                    saw a "no gateway" class in training, see results.md caveat)
-- Model: class_weight='balanced' logistic regression, trained on periods with a known
-- outcome ending before 2024-01-01, tested on periods ending 2024-01-01..2024-04-30.
-- contrib_* columns are included so the CSV/Python step can label each row's single
-- largest driver in plain language without re-deriving the linear algebra.
WITH feats AS (
    SELECT
        subscription_id, user_id, segment, customer_type, plan_type, start_date, end_date,
        mrr, period_number, main_gateway, renewal_change_bucket,
        (active_days    - {f(mean_['active_days'])})    / {f(std_['active_days'])}    AS active_days_z,
        (courses_seen   - {f(mean_['courses_seen'])})   / {f(std_['courses_seen'])}   AS courses_seen_z,
        (materials_seen - {f(mean_['materials_seen'])}) / {f(std_['materials_seen'])} AS materials_seen_z,
        (period_number  - {f(mean_['period_number'])})  / {f(std_['period_number'])}  AS period_number_z,
        CASE WHEN plan_type = 'annual' THEN 1 ELSE 0 END AS plan_annual,
        CASE WHEN customer_type = 'B2B' THEN 1 ELSE 0 END AS is_b2b,
        CASE WHEN renewal_change_bucket = 'contraction'      THEN 1 ELSE 0 END AS rc_contraction,
        CASE WHEN renewal_change_bucket = 'expansion'        THEN 1 ELSE 0 END AS rc_expansion,
        CASE WHEN renewal_change_bucket = 'no_prior_renewal' THEN 1 ELSE 0 END AS rc_no_prior_renewal,
        CASE WHEN main_gateway = 'PayPal'        THEN 1 ELSE 0 END AS gw_paypal,
        CASE WHEN main_gateway = 'MercadoPago'    THEN 1 ELSE 0 END AS gw_mercadopago,
        CASE WHEN main_gateway = 'Payoneer'       THEN 1 ELSE 0 END AS gw_payoneer,
        CASE WHEN main_gateway = 'Wire Transfer'  THEN 1 ELSE 0 END AS gw_wire_transfer
    FROM mart_a1_05_may24_population
),
contribs AS (
    SELECT
        *,
        {f(c['active_days_z'])}    * active_days_z    AS contrib_active_days,
        {f(c['courses_seen_z'])}   * courses_seen_z   AS contrib_courses_seen,
        {f(c['materials_seen_z'])} * materials_seen_z AS contrib_materials_seen,
        {f(c['period_number_z'])}  * period_number_z  AS contrib_tenure,
        {f(c['plan_annual'])}      * plan_annual      AS contrib_plan_annual,
        {f(c['is_b2b'])}           * is_b2b           AS contrib_is_b2b,
        {f(c['rc_contraction'])}   * rc_contraction   AS contrib_rc_contraction,
        {f(c['rc_expansion'])}     * rc_expansion     AS contrib_rc_expansion,
        {f(c['rc_no_prior_renewal'])} * rc_no_prior_renewal AS contrib_rc_no_prior_renewal,
        {f(c['gw_paypal'])}        * gw_paypal        AS contrib_gw_paypal,
        {f(c['gw_mercadopago'])}   * gw_mercadopago   AS contrib_gw_mercadopago,
        {f(c['gw_payoneer'])}      * gw_payoneer      AS contrib_gw_payoneer,
        {f(c['gw_wire_transfer'])} * gw_wire_transfer AS contrib_gw_wire_transfer
    FROM feats
),
scored AS (
    SELECT
        *,
        {f(intercept)}
        + contrib_active_days + contrib_courses_seen + contrib_materials_seen + contrib_tenure
        + contrib_plan_annual + contrib_is_b2b
        + contrib_rc_contraction + contrib_rc_expansion + contrib_rc_no_prior_renewal
        + contrib_gw_paypal + contrib_gw_mercadopago + contrib_gw_payoneer + contrib_gw_wire_transfer
        AS logit
    FROM contribs
)
SELECT
    subscription_id, user_id, segment, customer_type, plan_type, start_date, end_date,
    mrr, period_number, main_gateway, renewal_change_bucket,
    active_days_z, courses_seen_z, materials_seen_z, period_number_z,
    plan_annual, is_b2b, rc_contraction, rc_expansion, rc_no_prior_renewal,
    gw_paypal, gw_mercadopago, gw_payoneer, gw_wire_transfer,
    contrib_active_days, contrib_courses_seen, contrib_materials_seen, contrib_tenure,
    contrib_plan_annual, contrib_is_b2b, contrib_rc_contraction, contrib_rc_expansion,
    contrib_rc_no_prior_renewal, contrib_gw_paypal, contrib_gw_mercadopago,
    contrib_gw_payoneer, contrib_gw_wire_transfer,
    logit,
    1.0 / (1.0 + EXP(-logit)) AS prob_churn,
    CASE
        WHEN 1.0 / (1.0 + EXP(-logit)) >= {HIGH_CUTOFF}   THEN 'High'
        WHEN 1.0 / (1.0 + EXP(-logit)) >= {MEDIUM_CUTOFF} THEN 'Medium'
        ELSE 'Low'
    END AS risk_tier,
    mrr * (1.0 / (1.0 + EXP(-logit))) AS mrr_at_risk
FROM scored
ORDER BY prob_churn DESC
"""
    SQL_MART_TEMPLATE_OUT.write_text(sql, encoding="utf-8")
    print(f"\nWrote {SQL_MART_TEMPLATE_OUT}")


if __name__ == "__main__":
    main()
