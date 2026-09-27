#!/usr/bin/env python
"""
dev_build.py -- WP20 isolated dev build.

Copies db/platzi.duckdb (built by the shared sql/run_pipeline.py) into
work/WP20_cohorts_churn/dev.duckdb, builds the WP20 marts (sql/marts/mart_a1_*.sql,
in filename order) on top of it, runs the WP20 tests (sql/tests/test_a1_*.sql),
and exports each mart to a CSV in this folder.

Does NOT touch db/platzi.duckdb (read-only copy source) or sql/run_pipeline.py.
Usage:
    export PYTHONIOENCODING=utf-8
    ./.venv/Scripts/python.exe work/WP20_cohorts_churn/dev_build.py
"""
import shutil
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent.parent
SQL_DIR = ROOT / "sql"
SRC_DB = ROOT / "db" / "platzi.duckdb"
WORK_DIR = Path(__file__).resolve().parent
DEV_DB = WORK_DIR / "dev.duckdb"

MART_PREFIX = "mart_a1_"
TEST_PREFIX = "test_a1_"


def build(con: duckdb.DuckDBPyConnection) -> None:
    print("== Building WP20 marts (mart_a1_*) ==")
    mart_files = sorted((SQL_DIR / "marts").glob(f"{MART_PREFIX}*.sql"))
    for path in mart_files:
        name = path.stem
        select_sql = path.read_text(encoding="utf-8")
        con.execute(f"CREATE OR REPLACE TABLE {name} AS\n{select_sql}")
        n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"  {name:<40} {n:>7} rows")


def run_tests(con: duckdb.DuckDBPyConnection) -> bool:
    print("== Running WP20 tests (test_a1_*) ==")
    test_files = sorted((SQL_DIR / "tests").glob(f"{TEST_PREFIX}*.sql"))
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
    print("== Exporting mart_a1_* tables to work/WP20_cohorts_churn/ ==")
    tables = con.execute(
        "SELECT table_name FROM information_schema.tables "
        f"WHERE table_name LIKE '{MART_PREFIX}%' ORDER BY table_name"
    ).fetchall()
    for (table_name,) in tables:
        out_path = WORK_DIR / f"{table_name}.csv"
        con.execute(f"COPY {table_name} TO '{out_path.as_posix()}' (HEADER, DELIMITER ',')")
        print(f"  {table_name:<40} -> {out_path.name}")


def main() -> int:
    if not SRC_DB.exists():
        print(f"ERROR: {SRC_DB} not found. Build it first with sql/run_pipeline.py "
              "(shared pipeline, do not run it from here -- ask the orchestrator if missing).")
        return 2
    print(f"Copying {SRC_DB} -> {DEV_DB}")
    shutil.copyfile(SRC_DB, DEV_DB)

    con = duckdb.connect(str(DEV_DB))
    try:
        build(con)
        ok = run_tests(con)
        export_outputs(con)
    finally:
        con.close()

    print()
    print("ALL WP20 TESTS PASSED" if ok else "SOME WP20 TESTS FAILED -- see [FAIL] lines above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
