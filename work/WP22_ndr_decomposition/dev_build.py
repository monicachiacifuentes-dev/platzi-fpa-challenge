#!/usr/bin/env python
"""
dev_build.py -- WP22 (Analysis 3: NDR decomposition) isolated dev build.

Re-copies db/platzi.duckdb (already built by the shared sql/run_pipeline.py) into
work/WP22_ndr_decomposition/dev.duckdb, then builds this WP's mart_a3_* tables on
top of it (in dependency order) and runs this WP's tests (sql/tests/test_a3_*.sql).

Isolation: does NOT touch db/platzi.duckdb and does NOT run sql/run_pipeline.py,
so it is safe to run in parallel with WP20/WP21's own dev.duckdb copies.

Usage:
    export PYTHONIOENCODING=utf-8
    ./.venv/Scripts/python.exe work/WP22_ndr_decomposition/dev_build.py
"""
import shutil
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent.parent
SQL_DIR = ROOT / "sql"
SRC_DB = ROOT / "db" / "platzi.duckdb"
DEV_DIR = Path(__file__).resolve().parent
DEV_DB = DEV_DIR / "dev.duckdb"
OUT_DIR = DEV_DIR / "exports"

# Dependency order: 01/03 (decomposition) before 02/04 (their waterfall long
# formats); 05 before 06 (compounding depends on the monthly series); 07 before
# 08/09/10 (they read the same renewal population, 10 also depends on 01 + mart_q1).
MARTS_A3 = [
    "mart_a3_01_t12m_decomposition",
    "mart_a3_02_t12m_waterfall_long",
    "mart_a3_03_t6m_decomposition",
    "mart_a3_04_t6m_waterfall_long",
    "mart_a3_05_monthly_ndr_series",
    "mart_a3_06_monthly_compounded_t12m",
    "mart_a3_07_renewal_segmentation",
    "mart_a3_08_renewal_pctchange_bins",
    "mart_a3_09_renewal_engagement",
    "mart_a3_10_expansion_contraction_answer",
]

TEST_GLOB = "test_a3_*.sql"


def build(con: duckdb.DuckDBPyConnection) -> None:
    print("== Building mart_a3_* tables ==")
    for name in MARTS_A3:
        path = SQL_DIR / "marts" / f"{name}.sql"
        select_sql = path.read_text(encoding="utf-8")
        con.execute(f"CREATE OR REPLACE TABLE {name} AS\n{select_sql}")
        n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"  {name:<42} {n:>6} rows")


def run_tests(con: duckdb.DuckDBPyConnection) -> bool:
    print("== Running WP22 tests (sql/tests/test_a3_*.sql) ==")
    all_pass = True
    for path in sorted((SQL_DIR / "tests").glob(TEST_GLOB)):
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
    print("== Exporting mart_a3_* to work/WP22_ndr_decomposition/exports/ ==")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in MARTS_A3:
        out_path = OUT_DIR / f"{name}.csv"
        con.execute(f"COPY {name} TO '{out_path.as_posix()}' (HEADER, DELIMITER ',')")
        print(f"  {name:<42} -> {out_path.relative_to(ROOT)}")


def main() -> int:
    print(f"== Copying {SRC_DB.relative_to(ROOT)} -> {DEV_DB.relative_to(ROOT)} ==")
    if not SRC_DB.exists():
        print("ERROR: db/platzi.duckdb not found. Run sql/run_pipeline.py once "
              "(not part of WP22) before using this dev build.")
        return 2
    shutil.copyfile(SRC_DB, DEV_DB)

    con = duckdb.connect(str(DEV_DB))
    try:
        build(con)
        ok = run_tests(con)
        export_outputs(con)
    finally:
        con.close()

    print()
    print("ALL WP22 TESTS PASSED" if ok else "SOME WP22 TESTS FAILED -- see [FAIL] lines above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
