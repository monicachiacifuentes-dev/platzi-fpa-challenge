"""
WP40 -- verify outputs/Platzi_FPA_Model.xlsx by evaluating its formulas with the `formulas` Python
engine (openpyxl does not calculate formulas) and asserting the key outputs against the SQL/DuckDB
marts and the brief's known answers.

Run: .venv/Scripts/python.exe work/WP40_model/verify_model.py
"""
import duckdb
import formulas
import time
import os

ROOT = r"C:\Users\monic\Documents\PRUEBA_PLATZI"
XLSX_PATH = os.path.join(ROOT, "outputs", "Platzi_FPA_Model.xlsx")
DB_PATH = os.path.join(ROOT, "db", "platzi.duckdb")
BOOK = "Platzi_FPA_Model.xlsx"  # NOTE: the `formulas` engine's cell keys keep the workbook filename's
# original case but always uppercase the sheet name -- e.g. "'[Platzi_FPA_Model.xlsx]CHECKS'!A1"

FAILS = []
PASSES = []


def key(sheet, cell):
    return f"'[{BOOK}]{sheet.upper()}'!{cell}"


def get(sol, sheet, cell):
    v = sol[key(sheet, cell)].value
    try:
        return v[0, 0]
    except Exception:
        return v


def check(label, actual, expected, tol_abs=None, tol_rel=None):
    ok = False
    if tol_rel is not None and expected not in (0, None):
        ok = abs(actual - expected) / abs(expected) <= tol_rel
    elif tol_abs is not None:
        ok = abs(actual - expected) <= tol_abs
    else:
        ok = actual == expected
    line = f"{'PASS' if ok else 'FAIL'}  {label}: actual={actual!r} expected={expected!r}"
    if tol_rel is not None:
        line += f" (tol_rel={tol_rel})"
    elif tol_abs is not None:
        line += f" (tol_abs={tol_abs})"
    print(line)
    (PASSES if ok else FAILS).append(label)
    return ok


def main():
    print("Loading workbook into the formulas engine (this can take a couple of minutes)...")
    t0 = time.time()
    xl = formulas.ExcelModel().loads(XLSX_PATH).finish()
    print(f"  loaded in {time.time() - t0:.1f}s")

    outputs = [
        key("Answers_Q1_Q4", "B9"),   # Q1 total MRR
        key("Answers_Q1_Q4", "B6"), key("Answers_Q1_Q4", "B7"), key("Answers_Q1_Q4", "B8"),  # Q1 by segment
        key("Answers_Q1_Q4", "D47"),  # Q3 total active subs
        key("Answers_Q1_Q4", "B13"), key("Answers_Q1_Q4", "C13"),  # Q2 B2C logo/$ retention
        key("Answers_Q1_Q4", "B16"), key("Answers_Q1_Q4", "C16"),  # Q2 B2B logo/$ retention
        key("Answers_Q1_Q4", "B51"), key("Answers_Q1_Q4", "C51"),  # Q4 B2C NDR/GRR
        key("Answers_Q1_Q4", "B55"), key("Answers_Q1_Q4", "C55"),  # Q4 Total NDR/GRR
        key("UnitEconomics", "H28"), key("UnitEconomics", "H29"), key("UnitEconomics", "H30"),  # CAC T6M
        key("UnitEconomics", "N28"), key("UnitEconomics", "N29"), key("UnitEconomics", "N30"),  # LTV 60mo
        key("UnitEconomics", "O28"), key("UnitEconomics", "O29"), key("UnitEconomics", "O30"),  # LTV:CAC
        key("UnitEconomics", "J28"), key("UnitEconomics", "J29"), key("UnitEconomics", "J30"),  # ARPA
        key("UnitEconomics", "K28"),  # GM% selected
        key("UnitEconomics", "M28"), key("UnitEconomics", "M29"), key("UnitEconomics", "M30"),  # lifetime 60mo
        key("UnitEconomics", "B98"), key("UnitEconomics", "B99"), key("UnitEconomics", "B100"),  # CAC payback
        key("UnitEconomics", "C98"), key("UnitEconomics", "C99"), key("UnitEconomics", "C100"),  # retention-adj payback
        key("Scenarios", "D153"), key("Scenarios", "D154"), key("Scenarios", "D155"), key("Scenarios", "D156"),  # Base MRR Apr25
        key("Scenarios", "E153"), key("Scenarios", "E154"), key("Scenarios", "E155"), key("Scenarios", "E156"),  # Bull MRR Apr25
        key("Scenarios", "C153"), key("Scenarios", "C154"), key("Scenarios", "C155"), key("Scenarios", "C156"),  # Bear MRR Apr25
    ] + [key("Scenarios", f"E{r}") for r in range(160, 172)]  # reconciliation delta% column

    check_col_cells = [key("Checks", f"B{r}") for r in [7, 10, 11, 14, 15, 16, 17, 18, 19, 22, 25]]
    outputs += check_col_cells + [key("Checks", "B4")]

    print(f"Calculating {len(outputs)} targeted outputs (dependency-pruned)...")
    t0 = time.time()
    sol = xl.calculate(outputs=outputs)
    print(f"  calculated in {time.time() - t0:.1f}s")

    print("\n=== Q1 / Q3 ===")
    q1_total = get(sol, "Answers_Q1_Q4", "B9")
    check("Q1 total MRR Apr-24", q1_total, 204709.09, tol_abs=0.01)
    q1_b2c = get(sol, "Answers_Q1_Q4", "B6")
    q1_smb = get(sol, "Answers_Q1_Q4", "B7")
    q1_ent = get(sol, "Answers_Q1_Q4", "B8")
    check("Q1 B2C MRR", q1_b2c, 64365.00, tol_abs=0.01)
    check("Q1 SMB MRR", q1_smb, 53869.37, tol_abs=0.01)
    check("Q1 Enterprise MRR", q1_ent, 86474.72, tol_abs=0.01)
    q3_total = get(sol, "Answers_Q1_Q4", "D47")
    check("Q3 total active subs Apr-24", q3_total, 1941, tol_abs=0)

    print("\n=== Q2 / Q4 (linked mart values, sanity) ===")
    check("Q2 B2C logo retention", get(sol, "Answers_Q1_Q4", "B13"), 0.8955, tol_abs=0.001)
    check("Q4 B2C NDR", get(sol, "Answers_Q1_Q4", "B51"), 0.4308, tol_abs=0.001)
    check("Q4 Total NDR", get(sol, "Answers_Q1_Q4", "B55"), 0.6370, tol_abs=0.001)

    print("\n=== UnitEconomics: CAC / LTV / LTV:CAC vs. mart_a2_12 (within 1%) ===")
    con = duckdb.connect(DB_PATH, read_only=True)
    mart = con.execute(
        "select segment, cac_fully_loaded_t6m, ltv_base, ltv_cac_t6m, arpa_t6m_avg, gm_pct_t6m_base "
        "from mart_a2_12_unit_economics_summary where segment in ('B2C','SMB','Enterprise')").df()
    mart = mart.set_index("segment")
    seg_cells = {"B2C": 28, "SMB": 29, "Enterprise": 30}
    for seg, row in seg_cells.items():
        cac = get(sol, "UnitEconomics", f"H{row}")
        ltv = get(sol, "UnitEconomics", f"N{row}")
        ltv_cac = get(sol, "UnitEconomics", f"O{row}")
        arpa = get(sol, "UnitEconomics", f"J{row}")
        gm = get(sol, "UnitEconomics", f"K{row}")
        m = mart.loc[seg]
        check(f"{seg} CAC (T6M) vs mart_a2_12", cac, m["cac_fully_loaded_t6m"], tol_rel=0.01)
        check(f"{seg} LTV (60mo, T6M GM) vs mart_a2_12", ltv, m["ltv_base"], tol_rel=0.01)
        check(f"{seg} LTV:CAC vs mart_a2_12", ltv_cac, m["ltv_cac_t6m"], tol_rel=0.02)
        check(f"{seg} ARPA (T6M avg) vs mart_a2_12", arpa, m["arpa_t6m_avg"], tol_rel=0.005)
        check(f"{seg} GM% selected vs mart_a2_12 (T6M base)", gm, m["gm_pct_t6m_base"], tol_abs=0.001)

    print("\n=== UnitEconomics: retention-adjusted payback (60-month curve) ===")
    for seg, row in seg_cells.items():
        payback = get(sol, "UnitEconomics", f"C{row + 70}")
        print(f"  {seg}: retention-adjusted payback = {payback}")

    print("\n=== Scenarios: Apr-25 MRR vs. mart_s_03_scenario_summary (target <=3%) ===")
    engine = con.execute("select scenario, segment, mrr_apr25 from mart_s_03_scenario_summary").df()
    engine["scenario"] = engine["scenario"].str.capitalize()
    engine = engine.set_index(["scenario", "segment"])
    summary_rows = {"B2C": 153, "SMB": 154, "Enterprise": 155, "Total": 156}
    col = {"Bear": "C", "Base": "D", "Bull": "E"}
    for scenario in ["Base", "Bull", "Bear"]:
        for seg, row in summary_rows.items():
            sheet_val = get(sol, "Scenarios", f"{col[scenario]}{row}")
            engine_val = engine.loc[(scenario, seg), "mrr_apr25"]
            check(f"Scenario {scenario} / {seg} Apr-25 MRR vs engine", sheet_val, engine_val, tol_rel=(0.03 if seg == "Total" else 0.05))  # D-20: total 3%, segment 5%

    con.close()

    print("\n=== Checks tab ===")
    check_labels = {
        "B7": "MRR bridge identity (all 80 rows)",
        "B10": "Q1 total matches QA target",
        "B11": "Q3 total matches QA target",
        "B14": "B2C CAC within 1% of mart",
        "B15": "B2C LTV within 1% of mart",
        "B16": "SMB CAC within 1% of mart",
        "B17": "SMB LTV within 1% of mart",
        "B18": "Enterprise CAC within 1% of mart",
        "B19": "Enterprise LTV within 1% of mart",
        "B22": "Scenario reconciliation within tolerance",
        "B25": "Retention-adjusted payback populated",
    }
    all_true = True
    for cell, label in check_labels.items():
        v = get(sol, "Checks", cell)
        ok = bool(v) is True or v == True  # noqa: E712
        all_true = all_true and ok
        print(f"  {'PASS' if ok else 'FAIL'}  Checks!{cell} ({label}) = {v}")
        (PASSES if ok else FAILS).append(f"Checks!{cell} {label}")
    master = get(sol, "Checks", "B4")
    print(f"\n  Checks!B4 (ALL CHECKS PASS) = {master!r}")

    print("\n" + "=" * 70)
    print(f"TOTAL: {len(PASSES)} passed, {len(FAILS)} failed")
    if FAILS:
        print("FAILED:")
        for f in FAILS:
            print(f"  - {f}")
    else:
        print("ALL VERIFICATION CHECKS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
