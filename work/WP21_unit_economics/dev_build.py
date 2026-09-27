#!/usr/bin/env python
"""
WP21 (A2 Unit Economics) -- dev_build.py

Isolated build script:
  1. Copies db/platzi.duckdb -> work/WP21_unit_economics/dev.duckdb (never touches
     the shared db/platzi.duckdb, never runs sql/run_pipeline.py).
  2. Builds the mart_a2_01..13 SQL marts (pure SELECT files in sql/marts/) into
     dev.duckdb, in dependency order, the same way sql/run_pipeline.py wraps
     other marts (CREATE OR REPLACE TABLE <name> AS <select>).
  3. Runs sql/tests/test_a2_*.sql (each must return 0 rows to PASS).
  4. Exports every mart_a2_* table to work/WP21_unit_economics/marts_csv/*.csv
     and writes work/WP21_unit_economics/sheet_inputs.csv.

Pipeline integration note (lead-analyst review, item 3): ALL WP21 logic --
including the lifetime/LTV/CAC-payback synthesis that used to live in pandas
here -- is now expressed as pure SQL in sql/marts/mart_a2_11_lifetime.sql,
mart_a2_12_unit_economics_summary.sql and mart_a2_13_sensitivity.sql. Because
these files are NOT in sql/run_pipeline.py's hardcoded MARTS list, that
script's own glob line --
    MARTS += sorted(p.stem for p in (SQL_DIR / "marts").glob("*.sql") if p.stem not in MARTS)
-- already picks up every mart_a2_*.sql file automatically, in alphabetical
(= dependency, thanks to the NN prefix) order. No change to run_pipeline.py is
needed for these marts to appear in db/platzi.duckdb once this branch is
merged; this dev_build.py simply mirrors that same behaviour in isolation.

Usage:
    export PYTHONIOENCODING=utf-8
    ./.venv/Scripts/python.exe work/WP21_unit_economics/dev_build.py
"""
import shutil
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
SQL_DIR = ROOT / "sql"
DB_SRC = ROOT / "db" / "platzi.duckdb"
WORK_DIR = ROOT / "work" / "WP21_unit_economics"
DB_DEV = WORK_DIR / "dev.duckdb"
CSV_DIR = WORK_DIR / "marts_csv"

A2_MARTS = [
    "mart_a2_01_new_paying_customers",
    "mart_a2_02_marketing_spend_segment_monthly",
    "mart_a2_03_funnel_segment_monthly",
    "mart_a2_04_funnel_channel_total",
    "mart_a2_05_gna_allocation",
    "mart_a2_06_cac_fully_loaded",
    "mart_a2_07_cac_monthly",
    "mart_a2_08_gm_monthly",
    "mart_a2_09_arpa",
    "mart_a2_10_survival_curve",
    "mart_a2_11_lifetime",
    "mart_a2_12_unit_economics_summary",
    "mart_a2_13_sensitivity",
]

MIN_EXPOSURE = 20  # Proposed A-15: minimum cohort exposure n at k to trust a survival-curve point
LTV_CAP_BASE_MONTHS = 60   # Proposed A-18
LTV_CAP_SENS_MONTHS = 36   # Proposed A-18


def build_marts(con: duckdb.DuckDBPyConnection) -> None:
    print("== Building mart_a2_* (WP21) ==")
    for name in A2_MARTS:
        path = SQL_DIR / "marts" / f"{name}.sql"
        sql = path.read_text(encoding="utf-8")
        con.execute(f"CREATE OR REPLACE TABLE {name} AS\n{sql}")
        n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"  {name:<45} {n:>6} rows")


def run_tests(con: duckdb.DuckDBPyConnection) -> bool:
    print("== Running sql/tests/test_a2_*.sql ==")
    all_pass = True
    for path in sorted((SQL_DIR / "tests").glob("test_a2_*.sql")):
        sql = path.read_text(encoding="utf-8")
        df = con.execute(sql).fetchdf()
        status = "PASS" if len(df) == 0 else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  [{status}] {path.stem}")
        if status == "FAIL":
            print(df.to_string(index=False))
    return all_pass


def write_sheet_inputs(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Tidy (id, name, value, unit, source, note) list of every input/assumption
    that feeds the WP40 Google Sheet unit-economics model. Reads only from the
    already-built mart_a2_* SQL tables (no python-side computation)."""
    rows = []
    n = [0]

    def add(name, value, unit, source, note=""):
        n[0] += 1
        rows.append(dict(id=f"A2-{n[0]:03d}", name=name, value=value, unit=unit, source=source, note=note))

    # -- Method assumption IDs (see results.md / Plan_and_Index.md decisions log) --
    add("D-06: CAC denominator", "new paying customers (users.csv signups)", "definition", "D-06 (approved)",
        "marketing new_users_acquired reported only as a funnel metric, not the CAC denominator")
    add("D-05: G&A allocation formula", "marketing / (marketing + support costs) x total G&A", "formula", "D-05 (proposed)",
        "support costs = CS Salaries + Infrastructure + Content Production (excl. G&A itself)")
    add("D-05: G&A segment split (base)", "by segment share of marketing spend", "definition", "D-05 (proposed)", "sensitivity: by share of new customers")
    add("GM allocation (base, revised)", "all COGS (CS Salaries + Infrastructure + Content Production) by MRR share", "definition", "results.md WP21 (lead-analyst review)",
        "neutral default with no cost-driver data; forces uniform GM% across segments by construction")
    add("GM allocation (downside sensitivity)", "CS Salaries & Infrastructure by active-customer share; Content by MRR share", "definition", "results.md WP21",
        "was the base case in the prior draft (-37% B2C GM%); demoted to sensitivity per review")
    add("Proposed A-15: survival curve reliability threshold", MIN_EXPOSURE, "min cohort exposure n per k", "mart_a2_11_lifetime.sql", "k-points with exposed_n below this are dropped as unreliable/too-censored")
    add("Proposed A-16: dollar curve tail fallback", "use logo tail churn", "rule", "mart_a2_11_lifetime.sql", "applied when no window shows net dollar decay (net expansion in the tail)")
    add("Proposed A-17: dollar curve tail floor", "dollar decay >= logo tail churn", "rule", "mart_a2_11_lifetime.sql", "prevents implausible multi-decade LTV when dollar-tail decay is near zero on a small sample (SMB)")
    add("Proposed A-18: LTV horizon cap", f"{LTV_CAP_BASE_MONTHS} months (base)", "months", "mart_a2_11_lifetime.sql", f"sensitivity {LTV_CAP_SENS_MONTHS} months; uncapped reference also reported")
    add("Tail churn estimation window", "cascading last3 -> last6 -> full_range average of period-over-period ratios", "method", "mart_a2_11_lifetime.sql")
    add("ARPA / GM% base window", "T6M average (Nov-23..Apr-24)", "period", "mart_a2_08/09", "T16M and Apr-24 snapshot also reported")
    add("Enterprise payback benchmark", 18, "months", "SaaS benchmark (brief)", "vs 12 months for B2C/SMB; LTV:CAC benchmark = 3.0x for all segments")

    # -- Funnel (D-06) --
    funnel = con.execute(
        "SELECT segment, SUM(marketing_spend) spend, SUM(new_users_acquired_marketing) signups, SUM(new_paying_customers) paying "
        "FROM mart_a2_03_funnel_segment_monthly WHERE segment != 'Total' GROUP BY segment"
    ).fetchdf()
    for _, r in funnel.iterrows():
        add(f"{r['segment']}: marketing spend (T16M)", round(r["spend"], 2), "USD", "mart_a2_02/03")
        add(f"{r['segment']}: new signups per marketing (T16M)", int(r["signups"]), "signups", "marketing_spend.csv")
        add(f"{r['segment']}: new paying customers (T16M, D-06 base)", int(r["paying"]), "customers", "users.csv / mart_a2_01")
        add(f"{r['segment']}: cost per signup (T16M)", round(r["spend"] / r["signups"], 2), "USD/signup", "mart_a2_03")
        add(f"{r['segment']}: signup->paid conversion (T16M)", round(r["paying"] / r["signups"], 4), "ratio", "mart_a2_03",
            "Enterprise > 100%: users.csv (109) > marketing signups (82) -- D-11 caveat")

    channel = con.execute("SELECT * FROM mart_a2_04_funnel_channel_total WHERE period = 'T16M'").fetchdf()
    for _, r in channel.iterrows():
        add(f"{r['segment']}/{r['channel']}: cost per signup (T16M)", round(r["cost_per_signup"], 2), "USD/signup", "mart_a2_04")

    # -- G&A / CAC --
    gna = con.execute("SELECT * FROM mart_a2_05_gna_allocation WHERE period = 'T6M'").fetchdf()
    add("Acquisition share of G&A (T6M)", round(float(gna["acquisition_share_of_gna"].iloc[0]), 4), "ratio", "mart_a2_05")
    add("Total G&A pool allocated to acquisition (T6M)", round(float(gna["allocated_gna_pool"].iloc[0]), 2), "USD", "mart_a2_05")
    for _, r in gna[gna.segment != "Total"].iterrows():
        add(f"{r['segment']}: allocated G&A, base (T6M)", round(r["gna_alloc_base_by_marketing_share"], 2), "USD", "mart_a2_05")

    # -- Final summary (mart_a2_12) --
    summary = con.execute("SELECT * FROM mart_a2_12_unit_economics_summary").fetchdf()
    for _, r in summary.iterrows():
        seg = r["segment"]
        add(f"{seg}: ARPA (T6M avg)", r["arpa_t6m_avg"], "USD/month", "mart_a2_09")
        add(f"{seg}: GM% base, all-by-MRR (T6M avg)", r["gm_pct_t6m_base"], "ratio", "mart_a2_08")
        add(f"{seg}: GM% downside sensitivity, customer-weighted (T6M avg)", r["gm_pct_t6m_sens_customer_weighted"], "ratio", "mart_a2_08")
        add(f"{seg}: CAC fully loaded (T6M)", r["cac_fully_loaded_t6m"], "USD", "mart_a2_06")
        add(f"{seg}: CAC fully loaded (T16M)", r["cac_fully_loaded_t16m"], "USD", "mart_a2_06")
        add(f"{seg}: reliable survival curve horizon", r["reliable_k_max_months"], "months", "mart_a2_10", f"exposed_n >= {MIN_EXPOSURE}")
        add(f"{seg}: lifetime, logo curve (60mo cap)", r["lifetime_logo_months"], "months", "mart_a2_11")
        add(f"{seg}: lifetime, dollar curve (60mo cap, base)", r["lifetime_dollar_months"], "months", "mart_a2_11")
        add(f"{seg}: lifetime, dollar curve (36mo cap)", r["lifetime_dollar_36"], "months", "mart_a2_11")
        add(f"{seg}: lifetime, dollar curve (uncapped, reference)", r["lifetime_dollar_uncapped"], "months", "mart_a2_11")
        add(f"{seg}: lifetime cross-check, 1/logo churn", r["crosscheck_logo_1_over_churn"], "months", "mart_a2_11")
        add(f"{seg}: LTV base (60mo cap)", r["ltv_base"], "USD", "mart_a2_12")
        add(f"{seg}: LTV:CAC (T6M)", r["ltv_cac_t6m"], "ratio", "mart_a2_12", "benchmark >= 3.0x")
        add(f"{seg}: CAC payback (T6M)", r["cac_payback_months_t6m"], "months", "mart_a2_12", f"benchmark <= {r['benchmark_payback_threshold_months']}")
        add(f"{seg}: retention-adjusted payback", r["retention_adjusted_payback_months"], "months", "mart_a2_12", r["retention_adjusted_payback_note"])

    return pd.DataFrame(rows)


def main() -> int:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Copying {DB_SRC} -> {DB_DEV}")
    shutil.copyfile(DB_SRC, DB_DEV)

    con = duckdb.connect(str(DB_DEV))
    try:
        build_marts(con)
        ok = run_tests(con)

        print("== Exporting mart_a2_* to marts_csv/ ==")
        for name in A2_MARTS:
            out_path = CSV_DIR / f"{name}.csv"
            con.execute(f"COPY {name} TO '{out_path.as_posix()}' (HEADER, DELIMITER ',')")
        print(f"  {len(A2_MARTS)} tables -> {CSV_DIR.relative_to(ROOT)}")

        print("== Writing sheet_inputs.csv ==")
        sheet_inputs = write_sheet_inputs(con)
        sheet_inputs.to_csv(WORK_DIR / "sheet_inputs.csv", index=False)
        print(f"  {len(sheet_inputs)} rows -> {(WORK_DIR / 'sheet_inputs.csv').relative_to(ROOT)}")

    finally:
        con.close()

    print()
    if ok:
        print("ALL WP21 TESTS PASSED")
        return 0
    else:
        print("SOME WP21 TESTS FAILED -- see [FAIL] lines above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
