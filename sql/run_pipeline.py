#!/usr/bin/env python
"""
run_pipeline.py -- (re)builds db/platzi.duckdb end to end.

Steps:
  1. Load the 7 raw CSVs from Docs/Originals/ into raw_* tables.
  2. Run staging -> intermediate -> marts SQL files, in dependency order.
     Each .sql file holds a pure SELECT statement; this script wraps it in
     `CREATE OR REPLACE TABLE <filename> AS <select>` so the .sql files stay
     portable (they can be pasted into BigQuery later, see sql/README.md).
  3. Run every sql/tests/*.sql file. Each must return zero rows to PASS.
  4. Export every fct_* and mart_* table to outputs/marts/<name>.csv.

Usage:
    .venv/Scripts/python.exe sql/run_pipeline.py

Idempotent: deletes any existing db/platzi.duckdb and rebuilds from scratch.
"""
import importlib.util
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
DATA_DIR = ROOT / "Docs" / "Originals"
DB_PATH = ROOT / "db" / "platzi.duckdb"
OUT_DIR = ROOT / "outputs" / "marts"

RAW_TABLES = {
    "raw_users": "users.csv",
    "raw_subscriptions": "subscriptions.csv",
    "raw_payments": "payments.csv",
    "raw_payment_gateways": "payment_gateways.csv",
    "raw_engagement": "engagement.csv",
    "raw_marketing_spend": "marketing_spend.csv",
    "raw_support_costs": "support_costs.csv",
}

# Explicit dependency order (dbt-style layers: staging -> intermediate -> marts)
STAGING = [
    "stg_users",
    "stg_subscriptions",
    "stg_payments",
    "stg_payment_gateways",
    "stg_engagement",
    "stg_marketing_spend",
    "stg_support_costs",
]
INTERMEDIATE = [
    "int_month_spine",
    "int_subscription_periods",
]
MARTS = [
    "fct_subscriptions",
    "fct_customer_mrr_monthly",
    "mart_mrr_bridge",
    "mart_q1_mrr_apr24",
    "mart_q2_retention_q1_24",
    "mart_q3_active_subs_apr24",
    "mart_q4_ndr_t12m",
]
# Any other marts/*.sql file runs after the core list, in alphabetical order
# (analysis marts are named mart_a<N>_<NN>_<name>.sql so dependencies sort first).
MARTS += sorted(
    p.stem for p in (SQL_DIR / "marts").glob("*.sql") if p.stem not in MARTS
)

LAYER_DIRS = {
    "staging": STAGING,
    "intermediate": INTERMEDIATE,
    "marts": MARTS,
}


def sql_path(layer: str, name: str) -> Path:
    return SQL_DIR / layer / f"{name}.sql"


def build(con: duckdb.DuckDBPyConnection) -> None:
    print("== Loading raw CSVs ==")
    for table, filename in RAW_TABLES.items():
        csv_path = DATA_DIR / filename
        con.execute(
            f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_csv_auto(?, ALL_VARCHAR=FALSE)",
            [str(csv_path)],
        )
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<24} <- {filename:<24} {n:>7} rows")

    for layer, names in LAYER_DIRS.items():
        print(f"== Building layer: {layer} ==")
        for name in names:
            path = sql_path(layer, name)
            select_sql = path.read_text(encoding="utf-8")
            con.execute(f"CREATE OR REPLACE TABLE {name} AS\n{select_sql}")
            n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            print(f"  {name:<32} {n:>7} rows")


def build_python_models(con: duckdb.DuckDBPyConnection) -> None:
    """Runs every sql/python_models/*.py file that exposes a build(con) function,
    sorted by filename, after the SQL marts and before tests/export (e.g. WP31's
    sql/python_models/scenarios.py). Each module writes its own tables via `con`."""
    models_dir = SQL_DIR / "python_models"
    if not models_dir.exists():
        return
    print("== Building layer: python_models ==")
    for path in sorted(models_dir.glob("*.py")):
        if path.stem.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(f"python_models.{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(module, "build"):
            print(f"  {path.name:<32} (skipped, no build(con) function)")
            continue
        module.build(con)
        print(f"  {path.name:<32} build(con) OK")


def run_tests(con: duckdb.DuckDBPyConnection) -> bool:
    print("== Running tests ==")
    test_files = sorted((SQL_DIR / "tests").glob("*.sql"))
    all_pass = True
    for path in test_files:
        sql = path.read_text(encoding="utf-8")
        df = con.execute(sql).fetchdf()
        status = "PASS" if len(df) == 0 else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  [{status}] {path.stem}")
        if status == "FAIL":
            print(df.to_string(index=False))
    return all_pass


def export_outputs(con: duckdb.DuckDBPyConnection) -> None:
    print("== Exporting fct_*/mart_* tables to outputs/marts/ ==")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tables = con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_name LIKE 'fct_%' OR table_name LIKE 'mart_%' "
        "ORDER BY table_name"
    ).fetchall()
    for (table_name,) in tables:
        out_path = OUT_DIR / f"{table_name}.csv"
        con.execute(f"COPY {table_name} TO '{out_path.as_posix()}' (HEADER, DELIMITER ',')")
        print(f"  {table_name:<32} -> {out_path.relative_to(ROOT)}")


def main() -> int:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()  # rebuild from scratch every run (idempotent)

    con = duckdb.connect(str(DB_PATH))
    try:
        build(con)
        build_python_models(con)
        ok = run_tests(con)
        export_outputs(con)
    finally:
        con.close()

    print()
    if ok:
        print("ALL TESTS PASSED")
        return 0
    else:
        print("SOME TESTS FAILED -- see [FAIL] lines above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
