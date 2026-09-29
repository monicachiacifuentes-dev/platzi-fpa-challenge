"""WP34b -- reconcile the four BigQuery bq_q*_* tables against the DuckDB
mart CSVs (outputs/marts/mart_q*.csv).

Pulls each bq_ table via `bq query --format=csv` (raw-table-only queries,
see sql/bigquery/q1..q4*.sql), aligns rows to the corresponding DuckDB mart
row by the key columns (segment [+ split/method/plan_type as applicable]),
diffs every numeric column with the metric-appropriate tolerance:
  - money columns (mrr, *_mrr, dollar_numerator/denominator, amount_paid): 0.01
  - rate columns (pct_of_total, *_rate, ndr, grr): 0.0001
  - count columns (active_subs, base_customers, n_renewed, n_churned, n_ended): exact (0)
Prints a PASS/FAIL table to stdout and writes
outputs/bigquery_reconciliation.csv with columns:
  question, segment, metric, duckdb, bigquery, abs_diff, status

Run: .venv/Scripts/python.exe sql/bigquery/reconcile.py
(bq CLI must be on PATH -- see sql/bigquery/run_bigquery.ps1 for the PATH trick
 on Windows/Git Bash.)
"""
import csv
import io
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROJECT = "project-b7f9b2e4-dcdc-4e36-b89"
DATASET = "platzi_fpa"

MONEY_TOL = 0.01
RATE_TOL = 0.0001

# (question, bq_table, duckdb_csv, key_cols, money_cols, rate_cols, count_cols)
SPECS = [
    (
        "Q1",
        "bq_q1_mrr_apr24",
        "outputs/marts/mart_q1_mrr_apr24.csv",
        ["segment"],
        ["mrr"],
        ["pct_of_total"],
        [],
    ),
    (
        "Q2",
        "bq_q2_retention_q1_24",
        "outputs/marts/mart_q2_retention_q1_24.csv",
        ["method", "segment", "split"],
        ["dollar_numerator", "dollar_denominator"],
        ["logo_rate", "dollar_rate"],
        ["n_renewed", "n_churned", "n_ended"],
    ),
    (
        "Q3",
        "bq_q3_active_subs_apr24",
        "outputs/marts/mart_q3_active_subs_apr24.csv",
        ["segment", "plan_type"],
        [],
        [],
        ["active_subs"],
    ),
    (
        "Q4",
        "bq_q4_ndr_t12m",
        "outputs/marts/mart_q4_ndr_t12m.csv",
        ["method", "segment"],
        ["start_mrr", "expansion_mrr", "contraction_mrr", "churn_mrr", "end_mrr"],
        ["ndr", "grr"],
        ["base_customers"],
    ),
]


def find_bq():
    localappdata = os.environ.get("LOCALAPPDATA", "")
    candidate = os.path.join(localappdata, "gcloud", "google-cloud-sdk", "bin")
    if os.path.isdir(candidate):
        os.environ["PATH"] = candidate + os.pathsep + os.environ.get("PATH", "")
    return "bq.cmd" if os.name == "nt" else "bq"


def run_bq_query(bq_bin, sql):
    cmd = [
        bq_bin,
        f"--project_id={PROJECT}",
        "query",
        "--use_legacy_sql=false",
        "--format=csv",
        sql,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, shell=(os.name == "nt"))
    if result.returncode != 0:
        raise RuntimeError(f"bq query failed:\n{result.stderr}")
    return result.stdout


def parse_csv_text(text):
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def to_float(v):
    if v is None or v == "" or v.upper() == "NULL":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def main():
    bq_bin = find_bq()
    all_rows = []
    n_pass = 0
    n_fail = 0

    print(f"{'Q':<3} {'segment/key':<28} {'metric':<20} {'duckdb':>14} {'bigquery':>14} {'abs_diff':>12} status")
    print("-" * 100)

    for question, bq_table, duckdb_csv_rel, key_cols, money_cols, rate_cols, count_cols in SPECS:
        duckdb_path = os.path.join(ROOT, duckdb_csv_rel)
        with open(duckdb_path, newline="", encoding="utf-8") as f:
            duckdb_rows = list(csv.DictReader(f))

        bq_csv_text = run_bq_query(bq_bin, f"SELECT * FROM `{PROJECT}.{DATASET}.{bq_table}`")
        bq_rows = parse_csv_text(bq_csv_text)

        bq_index = {tuple(r[k] for k in key_cols): r for r in bq_rows}

        metric_cols = [(c, MONEY_TOL) for c in money_cols] + \
                      [(c, RATE_TOL) for c in rate_cols] + \
                      [(c, 0) for c in count_cols]

        for drow in duckdb_rows:
            key = tuple(drow[k] for k in key_cols)
            segment_label = "/".join(key)
            brow = bq_index.get(key)
            if brow is None:
                for metric, _tol in metric_cols:
                    n_fail += 1
                    print(f"{question:<3} {segment_label:<28} {metric:<20} {'(row missing in BigQuery)':>14}")
                    all_rows.append([question, segment_label, metric, drow.get(metric, ""), "", "", "FAIL_MISSING_ROW"])
                continue
            for metric, tol in metric_cols:
                dval = to_float(drow.get(metric))
                bval = to_float(brow.get(metric))
                if dval is None and bval is None:
                    status = "PASS"
                    diff = 0.0
                elif dval is None or bval is None:
                    status = "FAIL"
                    diff = float("nan")
                else:
                    diff = abs(dval - bval)
                    status = "PASS" if diff <= tol else "FAIL"
                if status == "PASS":
                    n_pass += 1
                else:
                    n_fail += 1
                print(f"{question:<3} {segment_label:<28} {metric:<20} {str(dval):>14} {str(bval):>14} {diff:>12.4f} {status}")
                all_rows.append([question, segment_label, metric, dval, bval, diff, status])

    print("-" * 100)
    print(f"TOTAL: {n_pass} PASS, {n_fail} FAIL")

    out_path = os.path.join(ROOT, "outputs", "bigquery_reconciliation.csv")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["question", "segment", "metric", "duckdb", "bigquery", "abs_diff", "status"])
        writer.writerows(all_rows)
    print(f"\nWrote {out_path}")

    if n_fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
