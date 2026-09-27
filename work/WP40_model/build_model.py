"""
WP40 -- build the Google-Sheets-safe financial model workbook.

Reads:
  - db/platzi.duckdb (read_only)
  - work/WP21_unit_economics/sheet_inputs.csv
  - work/WP31_scenarios/sheet_inputs.csv

Writes:
  - outputs/Platzi_FPA_Model.xlsx

Rerun: .venv/Scripts/python.exe work/WP40_model/build_model.py
"""
import duckdb
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter
import datetime as dt
import os

ROOT = r"C:\Users\monic\Documents\PRUEBA_PLATZI"
DB_PATH = os.path.join(ROOT, "db", "platzi.duckdb")
WP21_CSV = os.path.join(ROOT, "work", "WP21_unit_economics", "sheet_inputs.csv")
WP31_CSV = os.path.join(ROOT, "work", "WP31_scenarios", "sheet_inputs.csv")
OUT_PATH = os.path.join(ROOT, "outputs", "Platzi_FPA_Model.xlsx")

# ---------------------------------------------------------------- styles ---
BLUE = Font(color="0000FF")
BLACK = Font(color="000000")
GREEN = Font(color="008000")
BOLD = Font(bold=True)
BOLD_BLUE = Font(bold=True, color="0000FF")
BOLD_GREEN = Font(bold=True, color="008000")
TITLE_FONT = Font(bold=True, size=16, color="1F4E78")
SECTION_FONT = Font(bold=True, size=11, color="1F4E78")
NOTE_FONT = Font(italic=True, size=9, color="595959")
WHITE_BOLD = Font(bold=True, color="FFFFFF")

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
SECTION_FILL = PatternFill("solid", fgColor="D9E1F2")
SUBHEAD_FILL = PatternFill("solid", fgColor="F2F2F2")
PASS_FILL = PatternFill("solid", fgColor="C6EFCE")
FAIL_FILL = PatternFill("solid", fgColor="FFC7CE")

THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

CUR = '$#,##0.00'
CUR0 = '$#,##0'
PCT1 = '0.0%'
PCT2 = '0.00%'
MULT = '0.00"x"'
INT_FMT = '#,##0'
DATE_FMT = 'yyyy-mm-dd'
NUM1 = '#,##0.0'
NUM2 = '#,##0.00'

REFS = {}  # named cell references collected as we build, e.g. REFS['gm_basis'] = "Assumptions!$C$9"

# Fixed row layout for the two traceability registers on the Assumptions tab (kept well below the
# structured selector/driver sections so the two can be built independently without a forward-reference).
WP21_SECTION_ROW = 200
WP21_HEADER_ROW = 201
WP21_DATA_START = 202     # first data row (A2-001)
WP21_DATA_END = 300       # last data row (A2-099); 99 rows

WP31_SECTION_ROW = 303
WP31_HEADER_ROW = 304
WP31_DATA_START = 305     # first data row (S-001)
WP31_DATA_END = 362       # last data row (S-058); 58 rows


def title_row(ws, row, text, span=7):
    ws.cell(row=row, column=1, value=text).font = TITLE_FONT
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=span)


def note_row(ws, row, text, span=7):
    ws.cell(row=row, column=1, value=text).font = NOTE_FONT
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=span)


def section_header(ws, row, text, span=7):
    for c in range(1, span + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = SECTION_FILL
    ws.cell(row=row, column=1, value=text).font = SECTION_FONT


def col_headers(ws, row, headers, start_col=1):
    for i, h in enumerate(headers):
        cell = ws.cell(row=row, column=start_col + i, value=h)
        cell.font = WHITE_BOLD
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", wrap_text=True)


def freeze(ws, cell="A2"):
    ws.freeze_panes = cell


def set_widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def write_row(ws, row, values, fonts=None, formats=None, start_col=1):
    """values: list; fonts: list or single Font; formats: list or single fmt string or None"""
    n = len(values)
    if fonts is None:
        fonts = [BLACK] * n
    elif isinstance(fonts, Font):
        fonts = [fonts] * n
    if formats is None:
        formats = [None] * n
    elif isinstance(formats, str) or formats is None:
        formats = [formats] * n
    for i, v in enumerate(values):
        cell = ws.cell(row=row, column=start_col + i, value=v)
        cell.font = fonts[i]
        if formats[i]:
            cell.number_format = formats[i]
    return row


def dump_df(ws, df, start_row, start_col=1, value_font=BLUE, number_formats=None, date_cols=None):
    """Dump a dataframe with a bold header row, returns last row written (header row included)."""
    date_cols = date_cols or []
    number_formats = number_formats or {}
    col_headers(ws, start_row, list(df.columns), start_col=start_col)
    for i, row in enumerate(df.itertuples(index=False), start=1):
        r = start_row + i
        for j, val in enumerate(row):
            colname = df.columns[j]
            cell = ws.cell(row=r, column=start_col + j)
            if pd.isna(val):
                continue
            if colname in date_cols:
                if isinstance(val, pd.Timestamp):
                    cell.value = val.to_pydatetime()
                else:
                    cell.value = val
                cell.number_format = DATE_FMT
            else:
                if isinstance(val, str) and val.startswith("="):
                    val = " " + val  # avoid Excel/Sheets/openpyxl interpreting plain text as a formula
                cell.value = val
                if colname in number_formats:
                    cell.number_format = number_formats[colname]
            cell.font = value_font
    return start_row + len(df)


# =====================================================================
# README
# =====================================================================
def build_readme(wb):
    ws = wb.create_sheet("README")
    set_widths(ws, [4, 100])
    r = 1
    title_row(ws, r, "Platzi FP&A Financial Model", span=2); r += 1
    note_row(ws, r, "WP40 deliverable D1. Built by work/WP40_model/build_model.py -- rerun that script to regenerate this file from db/platzi.duckdb + the WP21/WP31 sheet_inputs.csv exports.", span=2); r += 2

    section_header(ws, r, "Purpose", span=2); r += 1
    for line in [
        "This workbook holds the assumptions, unit economics and scenario model for Platzi's FP&A take-home",
        "challenge, with every number traceable to a formula, an assumption ID, or a named SQL mart export.",
        "The heavy data work (fact tables, MRR bridge, retention, NDR decomposition, CAC/LTV synthesis, the",
        "scenario simulation engine) lives in the SQL/DuckDB pipeline (sql/staging -> sql/intermediate ->",
        "sql/marts, plus sql/python_models/scenarios.py). This Sheet consumes that pipeline's outputs as",
        "'Data_*' tabs (verbatim exports of named marts) and rebuilds the assumptions, unit-economics and",
        "scenario CALCULATIONS on top of them with visible spreadsheet formulas, per the 2026-09-26 update",
        "to Docs/Deliverables_Framework.md (D1): 'the data and calculation layer is SQL ... a small Google",
        "Sheet holds Assumptions, Unit Economics and Scenarios with visible formulas, fed by mart exports.'",
    ]:
        ws.cell(row=r, column=2, value=line).font = BLACK
        r += 1
    r += 1

    section_header(ws, r, "Tab map", span=2); r += 1
    tabs = [
        ("README", "This tab."),
        ("Assumptions", "Every driver with an ID (A-xx/D-xx/A2-xx/S-xx), value, unit, source, note. Scenario "
                         "selector, GM-basis selector, lifetime-cap, benchmarks, starting stock, scenario "
                         "engine drivers, and the full WP21/WP31 assumption registers."),
        ("Data_MRR", "Monthly MRR bridge by segment (mart_mrr_bridge): opening/new/expansion/contraction/"
                      "churn/closing MRR + active customers, Jan-23..Apr-24."),
        ("Data_Costs", "Monthly marketing spend by segment x channel (stg_marketing_spend), support costs "
                        "by category (stg_support_costs), and new paying customers by month x segment "
                        "(mart_a2_01_new_paying_customers)."),
        ("Data_Survival", "Logo and $ survival curves by segment, k=0..15 months (mart_a2_10_survival_curve)."),
        ("Answers_Q1_Q4", "The 4 ad-hoc answers. Q1 (MRR) and Q3 (active subs) are rebuilt with formulas from "
                           "Data_MRR / a small Q3 data block. Q2 (Q1-24 retention) and Q4 (NDR T12M) link to "
                           "small data blocks exported from mart_q2_retention_q1_24 / mart_q4_ndr_t12m -- a "
                           "full formula rebuild would require the row-level subscription table, which is out "
                           "of this workbook's scope (that computation lives in SQL); this is stated on the tab."),
        ("UnitEconomics", "Fully loaded CAC, revenue, COGS, GM% (driven by the GM-basis selector), ARPA, "
                           "the 60-month survival-curve build, LTV, LTV:CAC, CAC payback, and the "
                           "retention-adjusted payback on the full 60-month curve, by segment. Includes a "
                           "GM-basis x lifetime-cap sensitivity grid."),
        ("Scenarios", "A 12-month (May-24..Apr-25) formula-driven projection by segment, in three parallel "
                       "Base/Bull/Bear blocks (no selector needed), plus a summary and a reconciliation "
                       "block against the Python scenario engine (mart_s_03_scenario_summary)."),
        ("Strategies", "The WP23 retention-strategy table (6mo/12mo MRR delta, NDR delta, effort), linked to "
                        "Assumptions where the impact is a simple formula, labelled 'from engine' where it "
                        "comes from the Python simulation."),
        ("Checks", "TRUE/FALSE reconciliation checks with a master ALL CHECKS PASS cell."),
    ]
    col_headers(ws, r, ["Tab", "Contents"]); r += 1
    for name, desc in tabs:
        ws.cell(row=r, column=1, value=name).font = BOLD
        ws.cell(row=r, column=2, value=desc).font = BLACK
        ws.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = 30
        r += 1
    r += 1

    section_header(ws, r, "Conventions", span=2); r += 1
    conv = [
        ("Blue font", "Hard-coded input (an assumption, or a value pasted from a SQL mart export on a Data_* tab)."),
        ("Black font", "A formula computed from other cells in this workbook."),
        ("Green font", "A formula that links to a value on another tab (a cross-sheet reference / lookup)."),
        ("No hard-coded numbers in formulas", "Every formula points at an Assumptions/Data_* cell instead of "
                                               "embedding a number, except structural constants (12 months/year, 1)."),
        ("No macros / data tables / structured refs / dynamic-array-only functions / external links",
         "Only SUM, SUMIFS, SUMPRODUCT, INDEX/MATCH, IF, MIN/MAX, ROUND, AVERAGE, COUNTIFS, IFERROR, AND/OR "
         "and basic arithmetic are used, so the workbook opens and recalculates identically in Excel and "
         "Google Sheets."),
    ]
    col_headers(ws, r, ["Convention", "Meaning"]); r += 1
    for k, v in conv:
        ws.cell(row=r, column=1, value=k).font = BOLD
        ws.cell(row=r, column=2, value=v).font = BLACK
        ws.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = 28
        r += 1
    r += 1

    section_header(ws, r, "Data window", span=2); r += 1
    for line in [
        "Historical data: Jan-2023 .. Apr-2024 (16 months). As-of / snapshot date (M-01): 2024-04-30.",
        "Scenario projection: May-2024 .. Apr-2025 (12 months), seeded from the Apr-24 actuals.",
        "CAC / GM / ARPA windows: T6M = Nov-2023..Apr-2024 (base); T16M = Jan-2023..Apr-2024 (reference).",
    ]:
        ws.cell(row=r, column=2, value=line).font = BLACK
        r += 1
    r += 1

    section_header(ws, r, "How this links to the SQL pipeline", span=2); r += 1
    for line in [
        "Every Data_* tab is a verbatim export of one or more named marts/staging tables from db/platzi.duckdb",
        "(built by sql/run_pipeline.py from sql/staging -> sql/intermediate -> sql/marts, plus the Python",
        "scenario engine in sql/python_models/scenarios.py). This workbook does NOT recompute the SQL layer's",
        "own logic (retention definitions, the survival-curve tail-rate cascade, the monthly compartment",
        "simulation) -- it re-derives the assumptions/unit-economics/scenario CALCULATIONS from those exports",
        "using its own visible formulas, and cross-checks the results against the SQL/Python outputs on the",
        "Checks tab. Rerun sql/run_pipeline.py, then work/WP40_model/build_model.py, to refresh this file.",
    ]:
        ws.cell(row=r, column=2, value=line).font = BLACK
        r += 1
    r += 1

    section_header(ws, r, "Key caveats", span=2); r += 1
    for line in [
        "- GM% base case (all COGS allocated by MRR share) is uniform across segments BY CONSTRUCTION -- it "
        "cannot itself show any segment as more/less profitable than the company average (see UnitEconomics).",
        "- Retention-adjusted payback is now computed on the full extrapolated 60-month curve (this resolves "
        "the open issue in Docs/Plan_and_Index.md -- WP21's version only checked the observed 11-15 month "
        "horizon and always said 'never').",
        "- The Scenarios tab is a deliberately simplified single-bucket-per-segment model (it blends monthly/"
        "annual plan rates using the Apr-24 stock mix and ignores the B2C monthly->annual migration lever); "
        "it is reconciled against the full monthly-compartment Python engine within 3% on Apr-25 total MRR "
        "per scenario -- see the reconciliation block on the Scenarios tab for the exact gaps and why.",
        "- Q2 and Q4 are small linked data blocks from the SQL marts, not formula rebuilds (see Answers_Q1_Q4).",
        "- Enterprise and SMB unit-economics/survival figures rest on small samples (as few as ~58 new "
        "customers/6mo for Enterprise) -- treat them as directional, per WP20/21/22/31's repeated caveat.",
    ]:
        ws.cell(row=r, column=2, value=line).font = BLACK
        ws.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = 28
        r += 1

    freeze(ws, "A2")
    return ws


# =====================================================================
# ASSUMPTIONS
# =====================================================================
def build_assumptions(wb, wp21_df, wp31_df, tail_df, stock_df, mrr_apr24, flagged_mrr, at_risk_mrr):
    ws = wb.create_sheet("Assumptions")
    set_widths(ws, [46, 16, 16, 16, 12, 22, 46])
    r = 1
    title_row(ws, r, "Assumptions"); r += 1
    note_row(ws, r, "Purpose: every input driver used anywhere in this workbook, with its ID, value, unit, "
                     "source and note. Source = sql/marts/*.sql, sql/python_models/scenarios.py, or a "
                     "WP results.md. Blue = hard-coded input pasted from the SQL layer or the brief; "
                     "nothing on this tab is a formula."); r += 2

    # ---------------- selectors ----------------
    section_header(ws, r, "Key selectors & horizon dates"); r += 1
    col_headers(ws, r, ["Label", "Value", "Unit", "Source", "Note", "", ""]); r += 1

    def sel_row(label, value, unit, source, note, font=BLUE, fmt=None):
        nonlocal r
        write_row(ws, r, [label, value, unit, source, note],
                  fonts=[BLACK, font, BLACK, BLACK, NOTE_FONT], formats=[None, fmt, None, None, None])
        row_ = r
        r += 1
        return row_

    scen_row = sel_row("Scenario selector (informational -- Scenarios tab computes Base/Bull/Bear in "
                        "parallel blocks, so no tab actually reads this cell)", "Base", "Base/Bull/Bear",
                        "brief", "dropdown; kept for spec compliance / manual what-if reading")
    dv = DataValidation(type="list", formula1='"Base,Bull,Bear"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(ws.cell(row=scen_row, column=2))
    REFS['scenario_selector'] = f"Assumptions!$B${scen_row}"

    gm_row = sel_row("GM basis selector", "T6M avg", "T6M avg/Apr-24 run-rate", "D-17",
                      "T6M avg 29.3%% (conservative, base) vs Apr-24 run-rate 40.9%% (upside sensitivity); "
                      "drives GM% and LTV on UnitEconomics")
    dv2 = DataValidation(type="list", formula1='"T6M avg,Apr-24 run-rate"', allow_blank=False)
    ws.add_data_validation(dv2)
    dv2.add(ws.cell(row=gm_row, column=2))
    REFS['gm_basis_selector'] = f"Assumptions!$B${gm_row}"

    REFS['ltv_cap_base'] = f"Assumptions!$B${sel_row('LTV horizon cap -- base', 60, 'months', 'A-18', 'proposed WP21; standard 5-yr SaaS planning horizon')}"
    REFS['ltv_cap_sens'] = f"Assumptions!$B${sel_row('LTV horizon cap -- sensitivity', 36, 'months', 'A-18', 'conservative alternative reported alongside the 60mo base')}"
    REFS['asof_date'] = f"Assumptions!$B${sel_row('As-of / snapshot date (M-01)', dt.date(2024, 4, 30), 'date', 'M-01', 'April 2024 = snapshot at 2024-04-30', fmt=DATE_FMT)}"
    REFS['t6m_end_eom'] = REFS['asof_date']
    REFS['t6m_start_eom'] = f"Assumptions!$B${sel_row('T6M window start (month-end basis, for Data_MRR)', dt.date(2023, 11, 30), 'date', 'D-19/WP21', 'Nov-23..Apr-24', fmt=DATE_FMT)}"
    REFS['t6m_start_mstart'] = f"Assumptions!$B${sel_row('T6M window start (month-start basis, for Data_Costs)', dt.date(2023, 11, 1), 'date', 'D-19/WP21', 'stg_marketing_spend/stg_support_costs use month-start dates', fmt=DATE_FMT)}"
    REFS['t6m_end_mstart'] = f"Assumptions!$B${sel_row('T6M window end (month-start basis, for Data_Costs)', dt.date(2024, 4, 1), 'date', 'D-19/WP21', '', fmt=DATE_FMT)}"
    REFS['t16m_start_eom'] = f"Assumptions!$B${sel_row('T16M window start (month-end basis, for Data_MRR)', dt.date(2023, 1, 31), 'date', 'WP21', 'Jan-23..Apr-24', fmt=DATE_FMT)}"
    REFS['t16m_start_mstart'] = f"Assumptions!$B${sel_row('T16M window start (month-start basis, for Data_Costs)', dt.date(2023, 1, 1), 'date', 'WP21', '', fmt=DATE_FMT)}"
    REFS['t16m_end_mstart'] = REFS['t6m_end_mstart']
    REFS['scenario_h_start'] = f"Assumptions!$B${sel_row('Scenario horizon start (month 1 = May-24)', dt.date(2024, 5, 31), 'date', 'brief/WP31', '12-month projection starts the month after the as-of date', fmt=DATE_FMT)}"
    REFS['scenario_h_end'] = f"Assumptions!$B${sel_row('Scenario horizon end (month 12 = Apr-25)', dt.date(2025, 4, 30), 'date', 'brief/WP31', '', fmt=DATE_FMT)}"
    REFS['benchmark_ltv_cac'] = f"Assumptions!$B${sel_row('Benchmark: LTV:CAC', 3.0, 'x', 'brief/A2-012', 'SaaS rule of thumb, all segments', fmt=MULT)}"
    REFS['benchmark_payback_b2c_smb'] = f"Assumptions!$B${sel_row('Benchmark: CAC payback, B2C/SMB', 12, 'months', 'brief/A2-012', '', fmt=INT_FMT)}"
    REFS['benchmark_payback_ent'] = f"Assumptions!$B${sel_row('Benchmark: CAC payback, Enterprise', 18, 'months', 'brief/A2-012', 'longer sales cycle allowance', fmt=INT_FMT)}"
    REFS['tol_scenario'] = f"Assumptions!$B${sel_row('Tolerance: scenario reconciliation vs engine', 0.03, 'relative %', 'WP40 spec', 'target <= 3% on Apr-25 total MRR per scenario', fmt=PCT1)}"
    REFS['tol_scenario_seg'] = f"Assumptions!$B${sel_row('Tolerance: scenario reconciliation, single segment', 0.05, 'relative %', 'Lead review (D-20)', 'segment-level gaps are larger on small bases (e.g. SMB Bull stacks 3 levers); totals keep 3%', fmt=PCT1)}"
    REFS['tol_cac_ltv'] = f"Assumptions!$B${sel_row('Tolerance: sheet CAC/LTV vs mart_a2_12', 0.01, 'relative %', 'WP40 spec', '', fmt=PCT1)}"
    REFS['q1_target'] = f"Assumptions!$B${sel_row('QA target: Q1 total MRR Apr-24', 204709.09, 'USD', 'mart_q1_mrr_apr24', 'sum of segments must tie to this', fmt=CUR)}"
    REFS['q3_target'] = f"Assumptions!$B${sel_row('QA target: Q3 total active subs Apr-24', 1941, 'customers', 'mart_q3_active_subs_apr24', '', fmt=INT_FMT)}"
    r += 1

    # ---------------- starting stock ----------------
    section_header(ws, r, "Starting stock -- Apr-24 actuals (source: mart_q3_active_subs_apr24)"); r += 1
    col_headers(ws, r, ["Segment", "Plan type", "Active subs (Apr-24)", "", "", "", ""]); r += 1
    stock_start = r
    for _, row in stock_df.iterrows():
        write_row(ws, r, [row["segment"], row["plan_type"], row["active_subs"]],
                  fonts=[BLACK, BLACK, BLUE], formats=[None, None, INT_FMT])
        r += 1
    stock_end = r - 1
    REFS['stock_seg_col'] = f"Assumptions!$A${stock_start}:$A${stock_end}"
    REFS['stock_plan_col'] = f"Assumptions!$B${stock_start}:$B${stock_end}"
    REFS['stock_val_col'] = f"Assumptions!$C${stock_start}:$C${stock_end}"
    r += 1

    section_header(ws, r, "Starting MRR & customers -- Apr-24 actuals (link to Data_MRR)"); r += 1
    col_headers(ws, r, ["Segment", "Opening MRR (Apr-24)", "Opening customers (Apr-24)", "", "", "", ""]); r += 1
    opening_start = r
    for seg in ["B2C", "SMB", "Enterprise"]:
        f_mrr = (f'=SUMIFS(Data_MRR!$H:$H,Data_MRR!$B:$B,"{seg}",Data_MRR!$A:$A,{REFS["asof_date"]})')
        f_cust = (f'=SUMIFS(Data_MRR!$I:$I,Data_MRR!$B:$B,"{seg}",Data_MRR!$A:$A,{REFS["asof_date"]})')
        write_row(ws, r, [seg, f_mrr, f_cust], fonts=[BLACK, GREEN, GREEN], formats=[None, CUR, INT_FMT])
        r += 1
    opening_end = r - 1
    REFS['opening_start'] = opening_start
    REFS['opening_end'] = opening_end
    r += 1

    # ---------------- survival tail parameters ----------------
    section_header(ws, r, "Survival-curve tail parameters (Proposed A-23; source: mart_a2_11_lifetime.sql)"); r += 1
    col_headers(ws, r, ["Segment", "Reliable horizon k_rel (months)", "Dollar tail decay/mo",
                         "Logo tail churn/mo", "", "", ""]); r += 1
    tail_start = r
    for _, row in tail_df.iterrows():
        write_row(ws, r, [row["segment"], row["k_rel"], row["dollar_tail_decay"], row["logo_tail_churn"]],
                  fonts=[BLACK, BLUE, BLUE, BLUE], formats=[None, INT_FMT, '0.0000', '0.0000'])
        r += 1
    tail_end = r - 1
    REFS['tail_start'] = tail_start
    REFS['tail_end'] = tail_end
    note_row(ws, r, "A-23 (new, proposed): the tail decay/churn rate itself (computed in SQL by the "
                     "cascading last3->last6->full_range fallback logic, A-16/A-17) is exposed here as a "
                     "plain input so the 60-month curve can be rebuilt with formulas on UnitEconomics, per "
                     "the WP40 spec ('build the 60-row monthly curve on the tab itself... using the tail "
                     "churn from Assumptions'). The cascading SELECTION of which window to use is not "
                     "re-derived in the Sheet.")
    r += 2

    # ---------------- scenario engine drivers ----------------
    section_header(ws, r, "Scenario engine drivers -- T6M calibration (source: mart_s_01_drivers / WP31 "
                           "sheet_inputs.csv S-002..S-037)")
    r += 1
    col_headers(ws, r, ["Driver", "B2C", "SMB", "Enterprise", "Unit", "Source IDs (B2C/SMB/Ent)", "Note"]); r += 1

    driver_rows = [
        ("new_customers_per_month_avg", "S-002", "S-026", "S-014", "customers/month",
         "T6M average new paying customers"),
        ("new_customers_trend_slope", "S-003", "S-027", "S-015", "customers/month per month",
         "OLS trend over the T6M window; used in Bull only, floored at the flat average"),
        ("arpa_new_customer_monthly_plan", "S-009", "S-033", "S-021", "$/month", "avg mrr of new monthly-plan subs, T6M"),
        ("arpa_new_customer_annual_plan", "S-004", "S-028", "S-016", "$/month", "avg mrr of new annual-plan subs, T6M"),
        ("plan_mix_share_monthly (of new custs)", "S-013", "S-037", "S-025", "fraction", "T6M share of new customers on the monthly plan"),
        ("plan_mix_share_annual (of new custs)", "S-008", "S-032", "S-020", "fraction", "T6M share of new customers on the annual plan"),
        ("churn_rate_monthly_plan", "S-010", "S-034", "S-022", "fraction/month", "renewal-basis, T6M"),
        ("churn_rate_annual_plan (monthly-equiv, A-19c)", "S-005", "S-029", "S-017", "fraction/month",
         "annual rate converted via 1-(1-r)^(1/12)"),
        ("expansion_rate_monthly (B2B; B2C=0 by construction)", "S-012", "S-036", "S-024",
         "fraction/mo of retained MRR", "identical for monthly/annual buckets in the source decomposition"),
        ("contraction_rate_monthly (B2B; B2C=0 by construction)", "S-011", "S-035", "S-023",
         "fraction/mo of retained MRR", "identical for monthly/annual buckets in the source decomposition"),
    ]
    def wp31_lookup(_id):
        # NOTE: returns the bare INDEX/MATCH expression (no leading "="), so it can be embedded as a
        # sub-expression inside a larger formula. Callers that use it as a standalone cell formula
        # must prepend "=" themselves.
        return (f'INDEX(Assumptions!$C${WP31_DATA_START}:$C${WP31_DATA_END},'
                f'MATCH("{_id}",Assumptions!$A${WP31_DATA_START}:$A${WP31_DATA_END},0))')

    def wp21_lookup(_id):
        return (f'INDEX(Assumptions!$C${WP21_DATA_START}:$C${WP21_DATA_END},'
                f'MATCH("{_id}",Assumptions!$A${WP21_DATA_START}:$A${WP21_DATA_END},0))')

    def wp31_val(_id):
        """Standalone-cell version (with the leading '=') for use as a whole formula."""
        return f"={wp31_lookup(_id)}"

    REFS['wp31_lookup'] = wp31_lookup
    REFS['wp21_lookup'] = wp21_lookup

    driver_start = r
    driver_id_row = {}
    for name, id_b2c, id_smb, id_ent, unit, note in driver_rows:
        f = [f"={wp31_lookup(id_b2c)}", f"={wp31_lookup(id_smb)}", f"={wp31_lookup(id_ent)}"]
        write_row(ws, r, [name, f[0], f[1], f[2], unit, f"{id_b2c}/{id_smb}/{id_ent}", note],
                  fonts=[BLACK, GREEN, GREEN, GREEN, BLACK, BLACK, NOTE_FONT],
                  formats=[None, NUM2, NUM2, NUM2, None, None, None])
        driver_id_row[name] = r
        r += 1
    driver_end = r - 1
    REFS['driver_rows'] = driver_id_row
    r += 1

    section_header(ws, r, "Bear scenario stress constants (Proposed A-19; source: WP31 sheet_inputs.csv)"); r += 1
    col_headers(ws, r, ["Constant", "Value", "Unit", "Source ID", "Note", "", ""]); r += 1
    bear_rows = {}
    bear_rows['acq_decline'] = sel_row("Acquisition relative decline (all segments)", wp31_val("S-038"), "relative %", "S-038",
                                        "~1.5x the worst observed single-month new-customer decline, sustained 12mo", font=GREEN)
    bear_rows['churn_increase'] = sel_row("Churn relative increase (all segments)", wp31_val("S-039"), "relative %", "S-039",
                                           "largest observed positive MoM deviation in B2C-monthly churn", font=GREEN)
    bear_rows['smb_exp_mult'] = sel_row("SMB expansion multiplier", wp31_val("S-041"), "multiplier", "S-041", "brief: bear = expansion halved", font=GREEN)
    bear_rows['ent_exp_mult'] = sel_row("Enterprise expansion multiplier", wp31_val("S-040"), "multiplier", "S-040", "brief: bear = expansion halved", font=GREEN)
    REFS['bear_rows'] = bear_rows
    r += 1

    section_header(ws, r, "Bull scenario levers -- WP23 strategies at base case (Proposed A-20/A-21/A-22; "
                           "source: WP31 sheet_inputs.csv)")
    r += 1
    col_headers(ws, r, ["Lever", "Value", "Unit", "Source ID", "Note", "", ""]); r += 1
    bull_rows = {}
    bull_rows['churn_save_rate'] = sel_row("Strategy-1 churn save rate (monthly-plan churn only, all segments)",
                                            wp31_val("S-043"), "fraction saved", "S-043", "base case (low 10% / high 30%)", font=GREEN)
    bull_rows['migration_rate'] = sel_row("Strategy-2 B2C monthly->annual migration rate",
                                           wp31_val("S-044"), "fraction/month", "S-044",
                                           "NOT modelled in the simplified Scenarios engine below (see gap note); "
                                           "shown here for completeness / used on the Strategies tab", font=GREEN)
    bull_rows['smb_exp_uplift'] = sel_row("Strategy-3 SMB expansion uplift", wp31_val("S-046"), "relative %", "S-046",
                                           "base case (low 20% / high 60%)", font=GREEN)
    bull_rows['ent_contr_reduction'] = sel_row("Strategy-3 Enterprise contraction reduction", wp31_val("S-045"), "relative %", "S-045",
                                                "base case (low 30% / high 70%)", font=GREEN)
    REFS['bull_rows'] = bull_rows
    r += 1

    section_header(ws, r, "Strategy-1 illustrative check inputs (source: mart_a1_06_may24_churn_risk, D-16 risk tiers)"); r += 1
    REFS['strategy1_flagged_mrr'] = f"Assumptions!$B${sel_row('May-24 High+Medium risk MRR (flagged)', flagged_mrr, 'USD', 'mart_a1_06_may24_churn_risk', 'sum(mrr) where risk_tier in (High, Medium)', fmt=CUR)}"
    REFS['strategy1_at_risk_mrr'] = f"Assumptions!$B${sel_row('...of which expected to churn (mrr_at_risk)', at_risk_mrr, 'USD', 'mart_a1_06_may24_churn_risk', 'sum(mrr_at_risk) where risk_tier in (High, Medium)', fmt=CUR)}"
    r += 1

    # ---------------- traceability registers (fixed rows, see module constants) ----------------
    section_header(ws, WP21_SECTION_ROW,
                    "Full assumptions register -- traceability (WP21 sheet_inputs.csv, A2-001..A2-099)")
    last21 = dump_df(ws, wp21_df, WP21_HEADER_ROW,
                      number_formats={"value": NUM2})
    assert last21 == WP21_DATA_END, f"WP21 register ended at row {last21}, expected {WP21_DATA_END}"

    section_header(ws, WP31_SECTION_ROW,
                    "Full assumptions register -- scenario/strategy drivers (WP31 sheet_inputs.csv, S-001..S-058)")
    last31 = dump_df(ws, wp31_df, WP31_HEADER_ROW,
                      number_formats={"value": NUM2})
    assert last31 == WP31_DATA_END, f"WP31 register ended at row {last31}, expected {WP31_DATA_END}"

    freeze(ws, "A2")
    return ws, max(r, WP31_DATA_END + 1)


# =====================================================================
# DATA_MRR
# =====================================================================
def build_data_mrr(wb, mrr_df):
    ws = wb.create_sheet("Data_MRR")
    set_widths(ws, [12, 12, 13, 12, 13, 14, 12, 13, 15, 12])
    r = 1
    title_row(ws, r, "Data_MRR", span=10); r += 1
    note_row(ws, r, "Source: mart_mrr_bridge.sql (verbatim export). Monthly MRR bridge by segment, "
                     "Jan-23..Apr-24: opening -> +new +expansion -contraction -churn -> closing, plus "
                     "active customers. Blank expansion/contraction/churn cells = $0 (no movement of that "
                     "type that month) -- treated as 0 in all downstream formulas.", span=10); r += 2

    header_row = r
    df = mrr_df.copy()
    number_formats = {
        "opening_mrr": CUR, "new_mrr": CUR, "expansion_mrr": CUR, "contraction_mrr": CUR,
        "churn_mrr": CUR, "closing_mrr": CUR, "active_customers": INT_FMT,
    }
    last = dump_df(ws, df, header_row, date_cols=["month_end"], number_formats=number_formats)

    # bridge identity check column J
    ws.cell(row=header_row, column=10, value="bridge_check (opening+new+exp-contr-churn=closing)").font = WHITE_BOLD
    ws.cell(row=header_row, column=10).fill = HEADER_FILL
    ws.cell(row=header_row, column=10).alignment = Alignment(horizontal="center", wrap_text=True)
    for i in range(header_row + 1, last + 1):
        f = (f'=ROUND(IFERROR(C{i},0)+IFERROR(D{i},0)+IFERROR(E{i},0)-IFERROR(F{i},0)-IFERROR(G{i},0)-IFERROR(H{i},0),2)=0')
        ws.cell(row=i, column=10, value=f).font = BLACK
    REFS['data_mrr_header'] = header_row
    REFS['data_mrr_last'] = last
    REFS['data_mrr_check_col'] = f"Data_MRR!$J${header_row + 1}:$J${last}"

    freeze(ws, f"A{header_row + 1}")
    return ws


# =====================================================================
# DATA_COSTS
# =====================================================================
def build_data_costs(wb, mkt_df, support_df, newcust_df):
    ws = wb.create_sheet("Data_Costs")
    set_widths(ws, [12, 14, 14, 16, 22, 20])
    r = 1
    title_row(ws, r, "Data_Costs", span=6); r += 1
    note_row(ws, r, "Source: stg_marketing_spend, stg_support_costs, mart_a2_01_new_paying_customers "
                     "(verbatim exports). Three blocks: marketing spend by segment x channel, support "
                     "costs by category (incl. G&A), and new paying customers by month x segment.", span=6)
    r += 2

    section_header(ws, r, "Block A -- Marketing spend by segment x channel (stg_marketing_spend)", span=6); r += 1
    hdr_a = r
    fmt_a = {"spend": CUR, "new_users_acquired": INT_FMT}
    last_a = dump_df(ws, mkt_df, hdr_a, date_cols=["month"], number_formats=fmt_a)
    REFS['data_costs_mkt_header'] = hdr_a
    REFS['data_costs_mkt_last'] = last_a
    r = last_a + 2

    section_header(ws, r, "Block B -- Support costs by category, incl. G&A (stg_support_costs)", span=6); r += 1
    hdr_b = r
    fmt_b = {"amount": CUR}
    last_b = dump_df(ws, support_df, hdr_b, date_cols=["month"], number_formats=fmt_b)
    REFS['data_costs_support_header'] = hdr_b
    REFS['data_costs_support_last'] = last_b
    r = last_b + 2

    section_header(ws, r, "Block C -- New paying customers by month x segment (mart_a2_01_new_paying_customers)", span=6); r += 1
    hdr_c = r
    fmt_c = {"new_paying_customers": INT_FMT}
    last_c = dump_df(ws, newcust_df, hdr_c, date_cols=["month"], number_formats=fmt_c)
    REFS['data_costs_newcust_header'] = hdr_c
    REFS['data_costs_newcust_last'] = last_c

    freeze(ws, "A4")
    return ws


# =====================================================================
# DATA_SURVIVAL
# =====================================================================
def build_data_survival(wb, survival_df):
    ws = wb.create_sheet("Data_Survival")
    set_widths(ws, [12, 6, 11, 10, 14, 14, 14, 16, 15])
    r = 1
    title_row(ws, r, "Data_Survival", span=9); r += 1
    note_row(ws, r, "Source: mart_a2_10_survival_curve.sql (verbatim export). Logo and dollar survival "
                     "curves by segment, k=0..15 months since signup. Used by UnitEconomics to build the "
                     "60-month lifetime curve (observed k=0..k_rel, then an extrapolated tail).", span=9)
    r += 2
    hdr = r
    fmt = {"exposed_n": INT_FMT, "active_n": INT_FMT, "logo_survival": PCT2, "mrr_at_k_sum": CUR,
           "mrr_at_0_sum": CUR, "dollar_retention": PCT2, "arpa_at_signup": CUR}
    last = dump_df(ws, survival_df, hdr, number_formats=fmt)
    REFS['data_survival_header'] = hdr
    REFS['data_survival_last'] = last
    freeze(ws, f"A{hdr + 1}")
    return ws


# =====================================================================
# ANSWERS_Q1_Q4
# =====================================================================
def build_answers(wb, q2_df, q4_df):
    ws = wb.create_sheet("Answers_Q1_Q4")
    set_widths(ws, [14, 12, 14, 14, 13, 13, 14, 16, 16, 12])
    r = 1
    title_row(ws, r, "Answers_Q1_Q4", span=10); r += 1
    note_row(ws, r, "The four ad-hoc questions. Q1 (MRR by segment) and Q3 (active subs by segment x "
                     "plan) are rebuilt with formulas from Data_MRR / the Assumptions starting-stock block. "
                     "Q2 (Q1-24 retention) and Q4 (NDR T12M) link to small data blocks exported from "
                     "mart_q2_retention_q1_24 / mart_q4_ndr_t12m: their definitions (M-06 renewal-event "
                     "retention; M-08/M-09/M-10 NDR/GRR/expansion-contraction) require row-level "
                     "subscription-period data and a customer-level cohort join that are impractical to "
                     "rebuild as spreadsheet formulas -- that computation lives in SQL "
                     "(sql/marts/mart_q2_retention_q1_24.sql, mart_q4_ndr_t12m.sql); this tab links the "
                     "finished mart output instead of re-deriving it.", span=10)
    r += 2

    def asof():
        return REFS['asof_date']

    # ---------------- Q1 ----------------
    section_header(ws, r, "Q1 -- MRR by segment, Apr-24 (M-01..M-04; formula from Data_MRR)", span=10); r += 1
    col_headers(ws, r, ["Segment", "MRR Apr-24", "% of total", "", "", "", "", "", "", ""]); r += 1
    q1_start = r
    for seg in ["B2C", "SMB", "Enterprise"]:
        f = f'=SUMIFS(Data_MRR!$H:$H,Data_MRR!$B:$B,"{seg}",Data_MRR!$A:$A,{asof()})'
        write_row(ws, r, [seg, f], fonts=[BLACK, GREEN], formats=[None, CUR])
        r += 1
    q1_seg_end = r - 1
    write_row(ws, r, ["Total (= sum of segments)", f"=SUM(B{q1_start}:B{q1_seg_end})"],
              fonts=[BOLD, Font(bold=True, color="008000")], formats=[None, CUR])
    q1_total_row = r
    r += 1
    for i in range(q1_start, q1_total_row + 1):
        ws.cell(row=i, column=3, value=f"=B{i}/$B${q1_total_row}").number_format = PCT1
    REFS['q1_total_row'] = q1_total_row
    REFS['q1_range'] = f"Answers_Q1_Q4!$B${q1_start}:$B${q1_seg_end}"
    r += 1

    # ---------------- Q2 ----------------
    section_header(ws, r, "Q2 -- Q1-2024 retention, B2C vs B2B (M-06 primary; linked from mart_q2_retention_q1_24)", span=10); r += 1
    col_headers(ws, r, ["Segment", "Logo retention (all plans)", "$ retention (all plans)", "", "", "", "", "", "", ""]); r += 1
    q2_head_start = r
    hdr_row_q2 = None  # set after we know where the data block lands
    for seg in ["B2C", "SMB", "Enterprise", "B2B", "Total"]:
        write_row(ws, r, [seg, None, None], fonts=[BLACK, GREEN, GREEN], formats=[None, PCT2, PCT2])
        r += 1
    q2_head_end = r - 1
    r += 1
    note_row(ws, r, "Data block below: mart_q2_retention_q1_24 (M-06 renewal-event basis: renewed / "
                     "(renewed + churned), over subscriptions with end_date in 2024-01-01..2024-03-31).", span=10)
    r += 1
    q2_data_hdr = r
    q2_data_last = dump_df(ws, q2_df, q2_data_hdr,
                            number_formats={"n_renewed": INT_FMT, "n_churned": INT_FMT, "n_ended": INT_FMT,
                                             "logo_rate": PCT2, "dollar_numerator": CUR, "dollar_denominator": CUR,
                                             "dollar_rate": PCT2})
    # backfill the headline formulas now that we know the data block's location
    for i, seg in zip(range(q2_head_start, q2_head_end + 1), ["B2C", "SMB", "Enterprise", "B2B", "Total"]):
        # SUMPRODUCT-based lookup (avoids an array-context MATCH so it evaluates identically in Excel/Sheets).
        # Filters on method="M06_primary" too: the mart also carries an M07 cross-check row per
        # segment/split=all, which must NOT be summed together with the primary method's row.
        f_logo = (f'=SUMPRODUCT(($A${q2_data_hdr + 1}:$A${q2_data_last}="{seg}")*'
                  f'($B${q2_data_hdr + 1}:$B${q2_data_last}="all")*'
                  f'($C${q2_data_hdr + 1}:$C${q2_data_last}="M06_primary")*'
                  f'$G${q2_data_hdr + 1}:$G${q2_data_last})')
        f_dollar = (f'=SUMPRODUCT(($A${q2_data_hdr + 1}:$A${q2_data_last}="{seg}")*'
                    f'($B${q2_data_hdr + 1}:$B${q2_data_last}="all")*'
                    f'($C${q2_data_hdr + 1}:$C${q2_data_last}="M06_primary")*'
                    f'$J${q2_data_hdr + 1}:$J${q2_data_last})')
        ws.cell(row=i, column=2, value=f_logo)
        ws.cell(row=i, column=3, value=f_dollar)
    r = q2_data_last + 2

    # ---------------- Q3 ----------------
    section_header(ws, r, "Q3 -- Active subscriptions, Apr-24, by segment x plan (M-02; formula from Assumptions starting stock)", span=10); r += 1
    col_headers(ws, r, ["Segment", "Monthly", "Annual", "Total", "", "", "", "", "", ""]); r += 1
    q3_start = r
    for seg in ["B2C", "SMB", "Enterprise"]:
        f_m = f'=SUMIFS({REFS["stock_val_col"]},{REFS["stock_seg_col"]},"{seg}",{REFS["stock_plan_col"]},"monthly")'
        f_a = f'=SUMIFS({REFS["stock_val_col"]},{REFS["stock_seg_col"]},"{seg}",{REFS["stock_plan_col"]},"annual")'
        write_row(ws, r, [seg, f_m, f_a, f"=B{r}+C{r}"], fonts=[BLACK, GREEN, GREEN, BLACK], formats=[None, INT_FMT, INT_FMT, INT_FMT])
        r += 1
    q3_seg_end = r - 1
    write_row(ws, r, ["Total", f"=SUM(B{q3_start}:B{q3_seg_end})", f"=SUM(C{q3_start}:C{q3_seg_end})",
                       f"=SUM(D{q3_start}:D{q3_seg_end})"], fonts=BOLD, formats=[None, INT_FMT, INT_FMT, INT_FMT])
    q3_total_row = r
    REFS['q3_total_row'] = q3_total_row
    r += 2

    # ---------------- Q4 ----------------
    section_header(ws, r, "Q4 -- NDR T12M, company & segment (M-08/M-09; linked from mart_q4_ndr_t12m)", span=10); r += 1
    col_headers(ws, r, ["Segment", "NDR (T12M)", "GRR (T12M)", "", "", "", "", "", "", ""]); r += 1
    q4_head_start = r
    for seg in ["B2C", "SMB", "Enterprise", "B2B", "Total"]:
        write_row(ws, r, [seg, None, None], fonts=[BLACK, GREEN, GREEN], formats=[None, PCT1, PCT1])
        r += 1
    q4_head_end = r - 1
    r += 1
    note_row(ws, r, "Data block below: mart_q4_ndr_t12m (M-08 snapshot method: customers active on "
                     "2023-04-30; NDR = their Apr-24 MRR / their Apr-23 MRR; GRR caps expansion at 100%).", span=10)
    r += 1
    q4_data_hdr = r
    q4_data_last = dump_df(ws, q4_df, q4_data_hdr,
                            number_formats={"base_customers": INT_FMT, "start_mrr": CUR, "expansion_mrr": CUR,
                                             "contraction_mrr": CUR, "churn_mrr": CUR, "end_mrr": CUR,
                                             "ndr": PCT2, "grr": PCT2})
    for i, seg in zip(range(q4_head_start, q4_head_end + 1), ["B2C", "SMB", "Enterprise", "B2B", "Total"]):
        # method="M08_M09_M10" filter added defensively (the mart's other row per segment, "renewal_crosscheck",
        # currently has blank ndr/grr so contributes 0 either way, but the filter makes the intent explicit).
        f_ndr = (f'=SUMPRODUCT(($B${q4_data_hdr + 1}:$B${q4_data_last}="{seg}")*'
                 f'($A${q4_data_hdr + 1}:$A${q4_data_last}="M08_M09_M10")*$I${q4_data_hdr + 1}:$I${q4_data_last})')
        f_grr = (f'=SUMPRODUCT(($B${q4_data_hdr + 1}:$B${q4_data_last}="{seg}")*'
                 f'($A${q4_data_hdr + 1}:$A${q4_data_last}="M08_M09_M10")*$J${q4_data_hdr + 1}:$J${q4_data_last})')
        ws.cell(row=i, column=2, value=f_ndr)
        ws.cell(row=i, column=3, value=f_grr)

    freeze(ws, "A4")
    return ws


# =====================================================================
# UNITECONOMICS
# =====================================================================
def build_unit_economics(wb):
    ws = wb.create_sheet("UnitEconomics")
    set_widths(ws, [30] + [14] * 14)
    r = 1
    title_row(ws, r, "UnitEconomics", span=15); r += 1
    note_row(ws, r, "Source: Data_Costs, Data_MRR, Data_Survival + Assumptions (D-05/D-06/D-07, M-12..M-15, "
                     "A-15..A-18, A-23). Fully loaded CAC, gross margin, ARPA, the 60-month survival-based "
                     "lifetime curve, LTV, LTV:CAC, CAC payback and the retention-adjusted payback, by "
                     "segment -- all computed with formulas from the Data_* tabs, cross-checked on the "
                     "Checks tab against mart_a2_12_unit_economics_summary within 1%.", span=15)
    r += 2

    mkt_h = REFS['data_costs_mkt_header']; mkt_l = REFS['data_costs_mkt_last']
    sup_h = REFS['data_costs_support_header']; sup_l = REFS['data_costs_support_last']
    nc_h = REFS['data_costs_newcust_header']; nc_l = REFS['data_costs_newcust_last']
    mrr_h = REFS['data_mrr_header']; mrr_l = REFS['data_mrr_last']
    surv_h = REFS['data_survival_header']; surv_l = REFS['data_survival_last']

    MKT_MONTH = f"Data_Costs!$A${mkt_h + 1}:$A${mkt_l}"
    MKT_SEG = f"Data_Costs!$B${mkt_h + 1}:$B${mkt_l}"
    MKT_SPEND = f"Data_Costs!$D${mkt_h + 1}:$D${mkt_l}"
    SUP_MONTH = f"Data_Costs!$A${sup_h + 1}:$A${sup_l}"
    SUP_CAT = f"Data_Costs!$B${sup_h + 1}:$B${sup_l}"
    SUP_AMT = f"Data_Costs!$C${sup_h + 1}:$C${sup_l}"
    COGS_CATEGORIES = ["CS Salaries", "Infrastructure", "Content Production"]

    def cogs_sum(*month_criteria):
        # COGS = CS Salaries + Infrastructure + Content Production (i.e. all support-cost categories
        # except G&A). Written as an explicit sum of the three named categories -- not a single
        # SUMIFS(...,"<>G&A",...) -- because a not-equal text criterion combined with other criteria
        # is unreliable across spreadsheet engines/verification tools; the explicit sum is equally
        # correct in Excel/Sheets and is what verify_model.py's `formulas` engine can evaluate.
        month_args = "".join(f",{SUP_MONTH},{c}" for c in month_criteria)
        terms = [f'SUMIFS({SUP_AMT},{SUP_CAT},"{cat}"{month_args})' for cat in COGS_CATEGORIES]
        return "+".join(terms)
    NC_MONTH = f"Data_Costs!$A${nc_h + 1}:$A${nc_l}"
    NC_SEG = f"Data_Costs!$B${nc_h + 1}:$B${nc_l}"
    NC_VAL = f"Data_Costs!$C${nc_h + 1}:$C${nc_l}"
    MRR_MONTH = f"Data_MRR!$A${mrr_h + 1}:$A${mrr_l}"
    MRR_SEG = f"Data_MRR!$B${mrr_h + 1}:$B${mrr_l}"
    MRR_CLOSE = f"Data_MRR!$H${mrr_h + 1}:$H${mrr_l}"
    MRR_CUST = f"Data_MRR!$I${mrr_h + 1}:$I${mrr_l}"
    SURV_SEG = f"Data_Survival!$A${surv_h + 1}:$A${surv_l}"
    SURV_K = f"Data_Survival!$B${surv_h + 1}:$B${surv_l}"
    SURV_DOLLAR = f"Data_Survival!$H${surv_h + 1}:$H${surv_l}"

    t6m_ms = REFS['t6m_start_mstart']; t6m_me = REFS['t6m_end_mstart']
    t16m_ms = REFS['t16m_start_mstart']; t16m_me = REFS['t16m_end_mstart']
    asof = REFS['asof_date']
    gm_sel = REFS['gm_basis_selector']

    SEGMENTS = ["B2C", "SMB", "Enterprise"]

    # ---------------- G&A allocation build (company-level) ----------------
    section_header(ws, r, "G&A allocation build (D-05): company-level marketing, COGS (non-G&A support "
                           "costs) and G&A pool, T6M and T16M", span=15)
    r += 1
    col_headers(ws, r, ["Metric", "T6M (Nov-23..Apr-24)", "T16M (Jan-23..Apr-24)"] + [""] * 12); r += 1
    write_row(ws, r, ["Total marketing spend (all segments)",
                       f'=SUMIFS({MKT_SPEND},{MKT_MONTH},">="&{t6m_ms},{MKT_MONTH},"<="&{t6m_me})',
                       f'=SUMIFS({MKT_SPEND},{MKT_MONTH},">="&{t16m_ms},{MKT_MONTH},"<="&{t16m_me})'],
              fonts=[BLACK, GREEN, GREEN], formats=[None, CUR, CUR])
    row_total_mkt = r; r += 1
    t6m_ge = '">="&' + t6m_ms
    t6m_le = '"<="&' + t6m_me
    t16m_ge = '">="&' + t16m_ms
    t16m_le = '"<="&' + t16m_me
    write_row(ws, r, ["Total support costs, non-G&A (= company COGS)",
                       f'={cogs_sum(t6m_ge, t6m_le)}',
                       f'={cogs_sum(t16m_ge, t16m_le)}'],
              fonts=[BLACK, GREEN, GREEN], formats=[None, CUR, CUR])
    row_total_cogs = r; r += 1
    write_row(ws, r, ["Total G&A",
                       f'=SUMIFS({SUP_AMT},{SUP_CAT},"G&A",{SUP_MONTH},">="&{t6m_ms},{SUP_MONTH},"<="&{t6m_me})',
                       f'=SUMIFS({SUP_AMT},{SUP_CAT},"G&A",{SUP_MONTH},">="&{t16m_ms},{SUP_MONTH},"<="&{t16m_me})'],
              fonts=[BLACK, GREEN, GREEN], formats=[None, CUR, CUR])
    row_total_gna = r; r += 1
    write_row(ws, r, ["Acquisition share of G&A = marketing / (marketing + COGS)",
                       f'=B{row_total_mkt}/(B{row_total_mkt}+B{row_total_cogs})',
                       f'=C{row_total_mkt}/(C{row_total_mkt}+C{row_total_cogs})'],
              fonts=[BLACK, BLACK, BLACK], formats=[None, PCT1, PCT1])
    row_acq_share = r; r += 1
    write_row(ws, r, ["Allocated G&A pool = acquisition share x total G&A",
                       f'=B{row_acq_share}*B{row_total_gna}', f'=C{row_acq_share}*C{row_total_gna}'],
              fonts=[BLACK, BLACK, BLACK], formats=[None, CUR, CUR])
    row_gna_pool = r; r += 2

    # ---------------- Monthly ARPA / GM% helper block ----------------
    section_header(ws, r, "Monthly ARPA (by segment) & company GM% helper (T6M window, Nov-23..Apr-24). "
                           "M-12: revenue=MRR, COGS=CS Salaries+Infrastructure+Content, all allocated by "
                           "MRR share -> GM% is uniform across segments by construction (test_a2_gm_base_uniform)",
                   span=15)
    r += 1
    col_headers(ws, r, ["Month-end", "Revenue (Total MRR)", "COGS (non-G&A)", "GM% (month)",
                         "B2C ARPA", "SMB ARPA", "Enterprise ARPA", "",
                         "Month-start (helper, for Data_Costs lookups)"] + [""] * 6)
    r += 1
    t6m_months = [dt.date(2023, 11, 30), dt.date(2023, 12, 31), dt.date(2024, 1, 31),
                  dt.date(2024, 2, 29), dt.date(2024, 3, 31), dt.date(2024, 4, 30)]
    t6m_months_mstart = [dt.date(2023, 11, 1), dt.date(2023, 12, 1), dt.date(2024, 1, 1),
                          dt.date(2024, 2, 1), dt.date(2024, 3, 1), dt.date(2024, 4, 1)]
    month_rows = []
    for me, ms in zip(t6m_months, t6m_months_mstart):
        rev_f = f'=SUMIFS({MRR_CLOSE},{MRR_SEG},"Total",{MRR_MONTH},$A{r})'
        cogs_f = f'={cogs_sum(f"$I{r}")}'
        gm_f = f'=1-C{r}/B{r}'
        arpa_fs = []
        for seg in SEGMENTS:
            arpa_fs.append(f'=SUMIFS({MRR_CLOSE},{MRR_SEG},"{seg}",{MRR_MONTH},$A{r})/'
                            f'SUMIFS({MRR_CUST},{MRR_SEG},"{seg}",{MRR_MONTH},$A{r})')
        write_row(ws, r, [me, rev_f, cogs_f, gm_f, arpa_fs[0], arpa_fs[1], arpa_fs[2], None, ms],
                  fonts=[BLUE, GREEN, GREEN, BLACK, GREEN, GREEN, GREEN, BLACK, BLUE],
                  formats=[DATE_FMT, CUR, CUR, PCT2, CUR, CUR, CUR, None, DATE_FMT])
        month_rows.append(r)
        r += 1
    month_first, month_last = month_rows[0], month_rows[-1]
    write_row(ws, r, ["T6M average GM% (base, D-17)", None, None, f'=AVERAGE(D{month_first}:D{month_last})'],
              fonts=[NOTE_FONT, BLACK, BLACK, BOLD], formats=[None, None, None, PCT2])
    gm_t6m_row = r; r += 1
    write_row(ws, r, ["Apr-24 run-rate GM% (single month, D-17 sensitivity)", None, None, f'=D{month_last}'],
              fonts=[NOTE_FONT, BLACK, BLACK, BOLD], formats=[None, None, None, PCT2])
    gm_apr24_row = r; r += 1
    write_row(ws, r, ["ARPA T6M avg by segment ->", None, None, None,
                       f'=AVERAGE(E{month_first}:E{month_last})', f'=AVERAGE(F{month_first}:F{month_last})',
                       f'=AVERAGE(G{month_first}:G{month_last})'],
              fonts=[NOTE_FONT, BLACK, BLACK, BLACK, BOLD, BOLD, BOLD],
              formats=[None, None, None, None, CUR, CUR, CUR])
    arpa_avg_row = r
    ARPA_CELL = {"B2C": f"$E${arpa_avg_row}", "SMB": f"$F${arpa_avg_row}", "Enterprise": f"$G${arpa_avg_row}"}
    r += 2

    write_row(ws, r, ["GM% selected (per Assumptions GM-basis selector)",
                       f'=IF({gm_sel}="T6M avg",D{gm_t6m_row},D{gm_apr24_row})'],
              fonts=[BOLD, BOLD], formats=[None, PCT2])
    gm_selected_row = r
    GM_SEL_CELL = f"$B${gm_selected_row}"
    r += 2

    # ---------------- Headline segment table ----------------
    section_header(ws, r, "Headline unit economics by segment (D-05/D-06/M-12..M-15; GM% uniform by "
                           "construction -- see note above)", span=15)
    r += 1
    headers = ["Segment", "Marketing spend T6M", "Marketing spend T16M", "New paying customers T6M",
               "New paying customers T16M", "Allocated G&A T6M", "Allocated G&A T16M",
               "CAC fully loaded T6M", "CAC fully loaded T16M", "ARPA (T6M avg)", "GM% (selected)",
               "Revenue Apr-24", "Lifetime, $ curve (60mo cap)", "LTV (60mo cap)", "LTV:CAC (T6M)"]
    col_headers(ws, r, headers)
    r += 1
    head_start = r
    seg_row = {}
    for seg in SEGMENTS + ["Total"]:
        seg_row[seg] = r
        if seg != "Total":
            mkt6 = f'=SUMIFS({MKT_SPEND},{MKT_SEG},"{seg}",{MKT_MONTH},">="&{t6m_ms},{MKT_MONTH},"<="&{t6m_me})'
            mkt16 = f'=SUMIFS({MKT_SPEND},{MKT_SEG},"{seg}",{MKT_MONTH},">="&{t16m_ms},{MKT_MONTH},"<="&{t16m_me})'
            nc6 = f'=SUMIFS({NC_VAL},{NC_SEG},"{seg}",{NC_MONTH},">="&{t6m_ms},{NC_MONTH},"<="&{t6m_me})'
            nc16 = f'=SUMIFS({NC_VAL},{NC_SEG},"{seg}",{NC_MONTH},">="&{t16m_ms},{NC_MONTH},"<="&{t16m_me})'
        else:
            mkt6 = f"=SUM(B{seg_row['B2C']}:B{seg_row['Enterprise']})"
            mkt16 = f"=SUM(C{seg_row['B2C']}:C{seg_row['Enterprise']})"
            nc6 = f"=SUM(D{seg_row['B2C']}:D{seg_row['Enterprise']})"
            nc16 = f"=SUM(E{seg_row['B2C']}:E{seg_row['Enterprise']})"
        gna6 = f'=$B${row_gna_pool}*B{r}/$B${row_total_mkt}'
        gna16 = f'=$C${row_gna_pool}*C{r}/$C${row_total_mkt}'
        cac6 = f'=(B{r}+F{r})/D{r}'
        cac16 = f'=(C{r}+G{r})/E{r}'
        arpa = f"={ARPA_CELL[seg]}" if seg in ARPA_CELL else f"=AVERAGE(E{arpa_avg_row}:G{arpa_avg_row})"
        gm_ref = f"={GM_SEL_CELL}"
        rev_apr = f'=SUMIFS({MRR_CLOSE},{MRR_SEG},"{seg}",{MRR_MONTH},{asof})'
        write_row(ws, r, [seg, mkt6, mkt16, nc6, nc16, gna6, gna16, cac6, cac16, arpa, gm_ref, rev_apr, None, None, None],
                  fonts=[BOLD if seg == "Total" else BLACK, GREEN, GREEN, GREEN, GREEN, BLACK, BLACK,
                         BLACK, BLACK, GREEN, GREEN, GREEN, BLACK, BLACK, BLACK],
                  formats=[None, CUR, CUR, INT_FMT, INT_FMT, CUR, CUR, CUR, CUR, CUR, PCT2, CUR, NUM1, CUR, MULT])
        r += 1
    head_end = r - 1
    r += 1

    # ---------------- 60-month survival-based lifetime curve ----------------
    section_header(ws, r, "60-month lifetime curve, $ basis (M-14; A-15..A-18, A-23): observed dollar "
                           "retention for k=0..k_rel (Data_Survival), then an extrapolated geometric tail "
                           "using each segment's tail decay rate (Assumptions). Lifetime = sum of the curve.",
                   span=15)
    r += 1
    curve_headers = ["k (months since signup)"]
    for seg in SEGMENTS:
        curve_headers += [f"{seg} curve", f"{seg} cumulative (=lifetime thru k)", f"{seg} cum. gross profit/cust"]
    col_headers(ws, r, curve_headers)
    r += 1
    curve_first = r
    for k in range(0, 60):
        rr = curve_first + k
        ws.cell(row=rr, column=1, value=k).font = BLUE
        ws.cell(row=rr, column=1).number_format = INT_FMT
        col = 2
        for seg in SEGMENTS:
            trow = REFS['tail_start'] + SEGMENTS.index(seg)
            k_rel_ref = f"Assumptions!$B${trow}"
            decay_ref = f"Assumptions!$C${trow}"
            curve_col_letter = get_column_letter(col)
            cum_col_letter = get_column_letter(col + 1)
            gp_col_letter = get_column_letter(col + 2)
            if k == 0:
                curve_f = f'=SUMIFS({SURV_DOLLAR},{SURV_SEG},"{seg}",{SURV_K},$A{rr})'
            else:
                prev = rr - 1
                curve_f = (f'=IF($A{rr}<={k_rel_ref},SUMIFS({SURV_DOLLAR},{SURV_SEG},"{seg}",{SURV_K},$A{rr}),'
                           f'{curve_col_letter}{prev}*(1-{decay_ref}))')
            ws.cell(row=rr, column=col, value=curve_f).font = BLACK
            ws.cell(row=rr, column=col).number_format = PCT2
            if k == 0:
                cum_f = f'={curve_col_letter}{rr}'
            else:
                cum_f = f'={cum_col_letter}{rr - 1}+{curve_col_letter}{rr}'
            ws.cell(row=rr, column=col + 1, value=cum_f).font = BLACK
            ws.cell(row=rr, column=col + 1).number_format = NUM2
            gp_f = f'={cum_col_letter}{rr}*{ARPA_CELL[seg]}*{GM_SEL_CELL}'
            ws.cell(row=rr, column=col + 2, value=gp_f).font = BLACK
            ws.cell(row=rr, column=col + 2).number_format = CUR
            col += 3
    curve_last = curve_first + 59
    r = curve_last + 2

    CUM_COL = {"B2C": "C", "SMB": "F", "Enterprise": "I"}
    GP_COL = {"B2C": "D", "SMB": "G", "Enterprise": "J"}

    # backfill headline table: lifetime (60mo), LTV, LTV:CAC
    for seg in SEGMENTS:
        rr = seg_row[seg]
        cum_col = CUM_COL[seg]
        ws.cell(row=rr, column=13, value=f'={cum_col}{curve_last}')
        ws.cell(row=rr, column=13).font = BLACK
        ws.cell(row=rr, column=13).number_format = NUM1
        ws.cell(row=rr, column=14, value=f'=J{rr}*K{rr}*M{rr}')
        ws.cell(row=rr, column=14).font = BLACK
        ws.cell(row=rr, column=14).number_format = CUR
        ws.cell(row=rr, column=15, value=f'=N{rr}/H{rr}')
        ws.cell(row=rr, column=15).font = BLACK
        ws.cell(row=rr, column=15).number_format = MULT
    # Total row: LTV-weighted by new customers (T6M), so Total LTV:CAC is a customer-weighted blend
    tr = seg_row["Total"]
    ws.cell(row=tr, column=13, value=f"=SUMPRODUCT(D{seg_row['B2C']}:D{seg_row['Enterprise']},"
                                      f"M{seg_row['B2C']}:M{seg_row['Enterprise']})/D{tr}")
    ws.cell(row=tr, column=13).number_format = NUM1
    ws.cell(row=tr, column=14, value=f"=SUMPRODUCT(D{seg_row['B2C']}:D{seg_row['Enterprise']},"
                                      f"N{seg_row['B2C']}:N{seg_row['Enterprise']})/D{tr}")
    ws.cell(row=tr, column=14).number_format = CUR
    ws.cell(row=tr, column=15, value=f'=N{tr}/H{tr}')
    ws.cell(row=tr, column=15).number_format = MULT

    # ---------------- CAC payback & retention-adjusted payback ----------------
    section_header(ws, r, "CAC payback & retention-adjusted payback (M-15; resolves the WP40 open issue -- "
                           "computed on the full extrapolated 60-month curve, not just the observed horizon)",
                   span=15)
    r += 1
    col_headers(ws, r, ["Segment", "CAC payback = CAC / (ARPA x GM%), months", "Retention-adjusted payback "
                         "(first month cum. gross profit/customer >= CAC; '> 60' if never)"] + [""] * 12)
    r += 1
    payback_start = r
    for seg in SEGMENTS + ["Total"]:
        rr = seg_row[seg]
        simple_payback = f'=H{rr}/(J{rr}*K{rr})'
        if seg != "Total":
            gp_col = GP_COL[seg]
            n_below = f'SUMPRODUCT(({gp_col}{curve_first}:{gp_col}{curve_last}<$H${rr})*1)'
            retention_payback = f'=IF({n_below}=60,"> 60",{n_below}+1)'
        else:
            retention_payback = '="n/a (company blend)"'
        write_row(ws, r, [seg, simple_payback, retention_payback],
                  fonts=[BOLD if seg == "Total" else BLACK, BLACK, BLACK],
                  formats=[None, NUM1, None])
        r += 1
    payback_end = r - 1
    r += 1

    # ---------------- Sensitivity grid: GM basis x lifetime cap ----------------
    section_header(ws, r, "Sensitivity grid: LTV by GM basis x lifetime cap (36 / 60 months) -- formulas "
                           "only, no data tables", span=15)
    r += 1
    col_headers(ws, r, ["Segment", "T6M avg GM% x 36mo cap", "T6M avg GM% x 60mo cap",
                         "Apr-24 run-rate GM% x 36mo cap", "Apr-24 run-rate GM% x 60mo cap"] + [""] * 10)
    r += 1
    sens_start = r
    for seg in SEGMENTS:
        cum_col = CUM_COL[seg]
        cum36 = f'{cum_col}{curve_first + 35}'
        cum60 = f'{cum_col}{curve_last}'
        arpa_c = ARPA_CELL[seg]
        f_t6_36 = f'={arpa_c}*$D${gm_t6m_row}*{cum36}'
        f_t6_60 = f'={arpa_c}*$D${gm_t6m_row}*{cum60}'
        f_ap_36 = f'={arpa_c}*$D${gm_apr24_row}*{cum36}'
        f_ap_60 = f'={arpa_c}*$D${gm_apr24_row}*{cum60}'
        write_row(ws, r, [seg, f_t6_36, f_t6_60, f_ap_36, f_ap_60], fonts=BLACK, formats=[None, CUR, CUR, CUR, CUR])
        r += 1
    sens_end = r - 1

    freeze(ws, f"A{head_start}")
    return ws, dict(seg_row=seg_row, head_start=head_start, head_end=head_end,
                     payback_start=payback_start, payback_end=payback_end,
                     row_total_mkt=row_total_mkt, row_total_cogs=row_total_cogs, row_total_gna=row_total_gna,
                     gm_t6m_row=gm_t6m_row, gm_apr24_row=gm_apr24_row, arpa_avg_row=arpa_avg_row,
                     gm_selected_row=gm_selected_row, curve_first=curve_first, curve_last=curve_last,
                     CUM_COL=CUM_COL, GP_COL=GP_COL, ARPA_CELL=ARPA_CELL, GM_SEL_CELL=GM_SEL_CELL,
                     sens_start=sens_start, sens_end=sens_end)


# =====================================================================
# SCENARIOS
# =====================================================================
def build_scenarios(wb, engine_df):
    ws = wb.create_sheet("Scenarios")
    set_widths(ws, [14] + [13] * 10)
    r = 1
    title_row(ws, r, "Scenarios", span=11); r += 1
    note_row(ws, r, "A simplified, formula-driven 12-month (May-24..Apr-25) projection by segment, in three "
                     "parallel Base/Bull/Bear blocks (no selector needed -- all three are always computed). "
                     "Simplification vs. the Python engine (sql/python_models/scenarios.py): this sheet "
                     "tracks ONE bucket per segment (not per plan_type), blends monthly/annual rates using "
                     "the Apr-24 stock mix (churn) and the T6M new-customer plan mix (ARPA) held constant "
                     "for the whole horizon, and does not model the B2C monthly->annual migration lever. "
                     "See the reconciliation block at the bottom (target <= 3% gap on Apr-25 total MRR).",
              span=11)
    r += 2

    SEGMENTS = ["B2C", "SMB", "Enterprise"]
    driver_rows = REFS['driver_rows']
    bear_rows = REFS['bear_rows']
    bull_rows = REFS['bull_rows']

    def drv(name, seg):
        col = {"B2C": "B", "SMB": "C", "Enterprise": "D"}[seg]
        return f"Assumptions!${col}${driver_rows[name]}"

    def bear(name):
        return f"Assumptions!$B${bear_rows[name]}"

    def bull(name):
        return f"Assumptions!$B${bull_rows[name]}"

    stock_seg = REFS['stock_seg_col']; stock_plan = REFS['stock_plan_col']; stock_val = REFS['stock_val_col']

    # ---------------- Blended driver build ----------------
    section_header(ws, r, "Blended driver build (per segment): stock-mix-weighted churn, new-customer-mix "
                           "ARPA blend, and the Base/Bull/Bear variant of each rate -- all linked to "
                           "Assumptions (no hard-coded numbers)", span=15)
    r += 1
    col_headers(ws, r, ["Segment", "Stock share, monthly (Apr-24)", "Stock share, annual (Apr-24)",
                         "Churn blend, Base", "Churn blend, Bull", "Churn blend, Bear",
                         "New-cust ARPA blend", "Expansion, Base", "Expansion, Bull", "Expansion, Bear",
                         "Contraction, Base", "Contraction, Bull", "Contraction, Bear",
                         "New customers/mo, Base", "Trend slope/mo (Bull)"])
    r += 1
    blend_start = r
    blend_row = {}
    for seg in SEGMENTS:
        rr = r
        blend_row[seg] = rr
        f_share_m = (f'=SUMIFS({stock_val},{stock_seg},"{seg}",{stock_plan},"monthly")/'
                     f'(SUMIFS({stock_val},{stock_seg},"{seg}",{stock_plan},"monthly")+'
                     f'SUMIFS({stock_val},{stock_seg},"{seg}",{stock_plan},"annual"))')
        f_share_a = f'=1-B{rr}'
        churn_m = drv("churn_rate_monthly_plan", seg)
        churn_a = drv("churn_rate_annual_plan (monthly-equiv, A-19c)", seg)
        f_churn_base = f'=B{rr}*{churn_m}+C{rr}*{churn_a}'
        f_churn_bull = f'=B{rr}*{churn_m}*(1-{bull("churn_save_rate")})+C{rr}*{churn_a}'
        f_churn_bear = f'=D{rr}*(1+{bear("churn_increase")})'
        arpa_m = drv("arpa_new_customer_monthly_plan", seg)
        arpa_a = drv("arpa_new_customer_annual_plan", seg)
        pm_m = drv("plan_mix_share_monthly (of new custs)", seg)
        pm_a = drv("plan_mix_share_annual (of new custs)", seg)
        f_arpa_blend = f'={pm_m}*{arpa_m}+{pm_a}*{arpa_a}'
        exp_base = drv("expansion_rate_monthly (B2B; B2C=0 by construction)", seg)
        contr_base = drv("contraction_rate_monthly (B2B; B2C=0 by construction)", seg)
        f_exp_base = f'={exp_base}'
        f_contr_base = f'={contr_base}'
        if seg == "SMB":
            f_exp_bull = f'={exp_base}*(1+{bull("smb_exp_uplift")})'
            f_exp_bear = f'={exp_base}*{bear("smb_exp_mult")}'
            f_contr_bull = f'={contr_base}'
            f_contr_bear = f'={contr_base}'
        elif seg == "Enterprise":
            f_exp_bull = f'={exp_base}'
            f_exp_bear = f'={exp_base}*{bear("ent_exp_mult")}'
            f_contr_bull = f'={contr_base}*(1-{bull("ent_contr_reduction")})'
            f_contr_bear = f'={contr_base}'
        else:  # B2C -- expansion/contraction are 0 by construction; bull/bear = base for consistency
            f_exp_bull = f'={exp_base}'
            f_exp_bear = f'={exp_base}'
            f_contr_bull = f'={contr_base}'
            f_contr_bear = f'={contr_base}'
        new_avg = drv("new_customers_per_month_avg", seg)
        trend = drv("new_customers_trend_slope", seg)
        write_row(ws, rr, [seg, f_share_m, f_share_a, f_churn_base, f_churn_bull, f_churn_bear, f_arpa_blend,
                            f_exp_base, f_exp_bull, f_exp_bear, f_contr_base, f_contr_bull, f_contr_bear,
                            f'={new_avg}', f'={trend}'],
                  fonts=[BLACK] + [BLACK] * 14,
                  formats=[None, PCT2, PCT2, PCT2, PCT2, PCT2, CUR, PCT3 := '0.000%', PCT3, PCT3,
                           PCT3, PCT3, PCT3, NUM1, NUM2])
        r += 1
    blend_end = r - 1
    REFS['blend_row'] = blend_row
    r += 1

    COL = {"churn": {"Base": "D", "Bull": "E", "Bear": "F"},
           "exp": {"Base": "H", "Bull": "I", "Bear": "J"},
           "contr": {"Base": "K", "Bull": "L", "Bear": "M"}}

    def month_dates():
        return [dt.date(2024, 5, 31), dt.date(2024, 6, 30), dt.date(2024, 7, 31), dt.date(2024, 8, 31),
                dt.date(2024, 9, 30), dt.date(2024, 10, 31), dt.date(2024, 11, 30), dt.date(2024, 12, 31),
                dt.date(2025, 1, 31), dt.date(2025, 2, 28), dt.date(2025, 3, 31), dt.date(2025, 4, 30)]

    scenario_blocks = {}
    asof = REFS['asof_date']

    for scenario in ["Base", "Bull", "Bear"]:
        section_header(ws, r, f"Scenario: {scenario} -- 12-month projection by segment (May-24..Apr-25)", span=11)
        r += 1
        for seg in SEGMENTS:
            brow = blend_row[seg]
            ws.cell(row=r, column=1, value=f"{scenario} / {seg}").font = BOLD
            r += 1
            col_headers(ws, r, ["Month #", "Opening customers", "New customers", "Churn customers",
                                 "Closing customers", "Opening MRR", "New MRR", "Expansion MRR",
                                 "Contraction MRR", "Churn MRR", "Closing MRR"])
            r += 1
            first = r
            churn_ref = f"${COL['churn'][scenario]}${brow}"
            exp_ref = f"${COL['exp'][scenario]}${brow}"
            contr_ref = f"${COL['contr'][scenario]}${brow}"
            arpa_blend_ref = f"$G${brow}"
            new_avg_ref = f"$N${brow}"
            trend_ref = f"$O${brow}"
            for m, mdate in enumerate(month_dates(), start=1):
                rr = first + m - 1
                if m == 1:
                    open_cust_f = f'=SUMIFS(Data_MRR!$I:$I,Data_MRR!$B:$B,"{seg}",Data_MRR!$A:$A,{asof})'
                    open_mrr_f = f'=SUMIFS(Data_MRR!$H:$H,Data_MRR!$B:$B,"{seg}",Data_MRR!$A:$A,{asof})'
                else:
                    open_cust_f = f'=E{rr - 1}'
                    open_mrr_f = f'=K{rr - 1}'
                if scenario == "Base":
                    new_cust_f = f'={new_avg_ref}'
                elif scenario == "Bull":
                    new_cust_f = f'=MAX({new_avg_ref},{new_avg_ref}+{trend_ref}*A{rr})'
                else:
                    new_cust_f = f'={new_avg_ref}*(1-{bear("acq_decline")})'
                churn_cust_f = f'=B{rr}*{churn_ref}'
                close_cust_f = f'=B{rr}-D{rr}+C{rr}'
                new_mrr_f = f'=C{rr}*{arpa_blend_ref}'
                exp_mrr_f = f'=F{rr}*{exp_ref}'
                contr_mrr_f = f'=F{rr}*{contr_ref}'
                churn_mrr_f = f'=F{rr}*{churn_ref}'
                close_mrr_f = f'=F{rr}-J{rr}+G{rr}+H{rr}-I{rr}'
                write_row(ws, rr, [m, open_cust_f, new_cust_f, churn_cust_f, close_cust_f, open_mrr_f,
                                    new_mrr_f, exp_mrr_f, contr_mrr_f, churn_mrr_f, close_mrr_f],
                          fonts=[BLUE, GREEN if m == 1 else BLACK, BLACK, BLACK, BLACK,
                                 GREEN if m == 1 else BLACK, BLACK, BLACK, BLACK, BLACK, BLACK],
                          formats=[INT_FMT, NUM1, NUM1, NUM1, NUM1, CUR, CUR, CUR, CUR, CUR, CUR])
            last = first + 11
            scenario_blocks[(scenario, seg)] = dict(first=first, last=last)
            r = last + 2
        r += 1

    REFS['scenario_blocks'] = scenario_blocks

    # ---------------- Scenario summary ----------------
    section_header(ws, r, "Scenario summary -- Apr-25 MRR, growth %, subscribers, all three scenarios "
                           "side by side", span=11)
    r += 1
    col_headers(ws, r, ["Segment", "MRR Apr-24 (actual)", "MRR Apr-25 Bear", "MRR Apr-25 Base",
                         "MRR Apr-25 Bull", "Growth % Bear", "Growth % Base", "Growth % Bull",
                         "Subs Apr-24 (actual)", "Subs Apr-25 Bear", "Subs Apr-25 Base", "Subs Apr-25 Bull"])
    r += 1
    summary_start = r
    for seg in SEGMENTS + ["Total"]:
        if seg != "Total":
            mrr_actual = f'=SUMIFS(Data_MRR!$H:$H,Data_MRR!$B:$B,"{seg}",Data_MRR!$A:$A,{asof})'
            subs_actual = f'=SUMIFS(Data_MRR!$I:$I,Data_MRR!$B:$B,"{seg}",Data_MRR!$A:$A,{asof})'
            mrr_bear = f"=K{scenario_blocks[('Bear', seg)]['last']}"
            mrr_base = f"=K{scenario_blocks[('Base', seg)]['last']}"
            mrr_bull = f"=K{scenario_blocks[('Bull', seg)]['last']}"
            subs_bear = f"=E{scenario_blocks[('Bear', seg)]['last']}"
            subs_base = f"=E{scenario_blocks[('Base', seg)]['last']}"
            subs_bull = f"=E{scenario_blocks[('Bull', seg)]['last']}"
        else:
            mrr_actual = f"=SUM(B{summary_start}:B{summary_start+2})"
            subs_actual = f"=SUM(I{summary_start}:I{summary_start+2})"
            mrr_bear = f"=SUM(C{summary_start}:C{summary_start+2})"
            mrr_base = f"=SUM(D{summary_start}:D{summary_start+2})"
            mrr_bull = f"=SUM(E{summary_start}:E{summary_start+2})"
            subs_bear = f"=SUM(J{summary_start}:J{summary_start+2})"
            subs_base = f"=SUM(K{summary_start}:K{summary_start+2})"
            subs_bull = f"=SUM(L{summary_start}:L{summary_start+2})"
        write_row(ws, r, [seg, mrr_actual, mrr_bear, mrr_base, mrr_bull,
                           f"=C{r}/B{r}-1", f"=D{r}/B{r}-1", f"=E{r}/B{r}-1",
                           subs_actual, subs_bear, subs_base, subs_bull],
                  fonts=[BOLD if seg == "Total" else BLACK] + [GREEN if seg != "Total" else BLACK] * 4 +
                        [BLACK] * 3 + [GREEN if seg != "Total" else BLACK] * 4,
                  formats=[None, CUR, CUR, CUR, CUR, PCT1, PCT1, PCT1, INT_FMT, NUM1, NUM1, NUM1])
        r += 1
    summary_end = r - 1
    REFS['scenario_summary_start'] = summary_start
    REFS['scenario_summary_end'] = summary_end
    r += 1

    # ---------------- Reconciliation vs. the Python engine ----------------
    section_header(ws, r, "Reconciliation vs. the Python engine (mart_s_03_scenario_summary) -- Sheet vs. "
                           "engine Apr-25 MRR, target <= 3% |delta|", span=11)
    r += 1
    col_headers(ws, r, ["Scenario", "Segment", "Sheet MRR Apr-25", "Engine MRR Apr-25 (mart_s_03, input)",
                         "Delta %", "Within tolerance? (Total 3% / segment 5%)"] + [""] * 5)
    r += 1
    recon_start = r
    engine_df_sorted = engine_df.copy()
    engine_df_sorted["scenario"] = engine_df_sorted["scenario"].str.capitalize()
    for _, row in engine_df_sorted.iterrows():
        scenario = row["scenario"]
        seg = row["segment"]
        if seg not in SEGMENTS + ["Total"]:
            continue
        if seg == "B2B":
            continue
        if seg == "Total":
            sheet_f = f"=D{summary_start + 3}" if scenario == "Base" else (
                f"=C{summary_start + 3}" if scenario == "Bear" else f"=E{summary_start + 3}")
        else:
            offset = SEGMENTS.index(seg)
            col = {"Base": "D", "Bull": "E", "Bear": "C"}[scenario]
            sheet_f = f"={col}{summary_start + offset}"
        engine_val = row["mrr_apr25"]
        write_row(ws, r, [scenario, seg, sheet_f, engine_val, f"=(C{r}-D{r})/D{r}",
                           f'=IF(ABS(E{r})<={REFS["tol_scenario"] if seg == "Total" else REFS["tol_scenario_seg"]},TRUE,FALSE)'],
                  fonts=[BLACK, BLACK, BLACK, BLUE, BLACK, BLACK],
                  formats=[None, None, CUR, CUR, PCT1, None])
        r += 1
    recon_end = r - 1
    REFS['recon_start'] = recon_start
    REFS['recon_end'] = recon_end
    r += 1
    note_row(ws, r, "Gap explanation: the Sheet model blends monthly/annual plan rates into one bucket per "
                     "segment (held at the Apr-24 stock/new-customer mix) instead of running six separate "
                     "monthly-compartment buckets, and it does not model the Strategy-2 B2C annual-migration "
                     "lever that the Python Bull case includes. Both are deliberate simplifications so the "
                     "Sheet stays formula-auditable; the gap is consistently <=3% on Apr-25 total MRR per "
                     "scenario (see Checks tab).", span=11)
    r += 1

    freeze(ws, "A4")
    return ws, dict(blend_row=blend_row, scenario_blocks=scenario_blocks, blend_start=blend_start,
                     blend_end=blend_end, summary_start=summary_start, summary_end=summary_end,
                     recon_start=recon_start, recon_end=recon_end)


# =====================================================================
# STRATEGIES
# =====================================================================
def build_strategies(wb, strategy_df):
    ws = wb.create_sheet("Strategies")
    set_widths(ws, [30, 12, 14, 14, 14, 14, 10, 16])
    r = 1
    title_row(ws, r, "Strategies", span=8); r += 1
    note_row(ws, r, "Source: WP23 results.md + mart_s_04_strategy_impact (from the Python scenario engine, "
                     "sql/python_models/scenarios.py -- each strategy is sized as an isolated lever on top "
                     "of the Base scenario). The company-wide 6mo/12mo MRR and NDR deltas are simulation "
                     "outputs ('from engine', not spreadsheet formulas -- the underlying monthly compartment "
                     "simulation is not re-derived here, same as the Scenarios tab's engine comparison). One "
                     "illustrative figure IS a simple in-sheet formula: Strategy-1's immediate monthly save "
                     "on the concrete May-24 at-risk list.", span=8)
    r += 2

    section_header(ws, r, "Illustrative simple-formula check: Strategy-1 applied to the May-24 at-risk list "
                           "(source: mart_a1_06_may24_churn_risk, D-16 risk tiers)", span=8)
    r += 1
    col_headers(ws, r, ["Metric", "Value", "Unit", "Source", "", "", "", ""]); r += 1
    write_row(ws, r, ["May-24 High+Medium risk MRR (flagged)", f'={REFS["strategy1_flagged_mrr"]}',
                       "USD", "Assumptions (mart_a1_06_may24_churn_risk)"],
              fonts=[BLACK, GREEN, BLACK, BLACK], formats=[None, CUR, None, None])
    r += 1
    write_row(ws, r, ["...of which expected to churn (mrr_at_risk)", f'={REFS["strategy1_at_risk_mrr"]}',
                       "USD", "Assumptions (mart_a1_06_may24_churn_risk)"],
              fonts=[BLACK, GREEN, BLACK, BLACK], formats=[None, CUR, None, None])
    at_risk_row = r
    r += 1
    save_rate_row = REFS['bull_rows']['churn_save_rate']
    write_row(ws, r, ["Strategy-1 base-case save rate (link to Assumptions)", f"=Assumptions!$B${save_rate_row}",
                       "fraction saved", "A-20 (Assumptions)"],
              fonts=[BLACK, GREEN, BLACK, BLACK], formats=[None, PCT1, None, None])
    save_rate_local = r
    r += 1
    write_row(ws, r, ["-> Immediate monthly MRR saved if applied once to the May-24 list",
                       f"=B{at_risk_row}*B{save_rate_local}", "USD/month",
                       "simple formula (at-risk MRR x save rate)"],
              fonts=[BOLD, BOLD, BLACK, NOTE_FONT], formats=[None, CUR, None, None])
    r += 2
    note_row(ws, r, "This single-month figure is smaller than the engine's $7,690/6-month company number "
                     "below because the engine compounds the same save rate over every month's newly "
                     "flagged cohort, not just the May-24 list once (see WP23 results.md).", span=8)
    r += 2

    section_header(ws, r, "Company-wide strategy impact, low/base/high (from engine: mart_s_04_strategy_impact)", span=8)
    r += 1
    col_headers(ws, r, ["Strategy", "Case", "6-mo MRR impact ($)", "6-mo MRR impact (%)",
                         "12-mo MRR impact ($)", "NDR impact, 6-mo (pp)", "Effort", "Time to impact (months)"])
    r += 1
    df = strategy_df[strategy_df["segment"] == "Total"].copy()
    order_case = {"low": 0, "base": 1, "high": 2}
    df["case_order"] = df["case"].map(order_case)
    df = df.sort_values(["strategy", "case_order"])
    strategy_labels = {
        "strategy_1_engagement_alert": "1. Engagement alert + save play",
        "strategy_2_annual_migration": "2. B2C monthly -> annual migration",
        "strategy_3_b2b_playbook": "3. B2B expansion/contraction playbook",
    }
    for _, row in df.iterrows():
        label = strategy_labels.get(row["strategy"], row["strategy"])
        write_row(ws, r, [label, row["case"], row["mrr_delta_m6"], row["mrr_delta_pct_m6"] / 100.0,
                           row["mrr_delta_m12"], row["ndr_delta_pp_m6"], row["effort"],
                           row["time_to_impact_months"]],
                  fonts=[BLACK, BLACK, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE],
                  formats=[None, None, CUR0, PCT1, CUR0, NUM2, None, INT_FMT])
        r += 1
    r += 1

    section_header(ws, r, "Recommended sequence (WP23; unchanged narrative from the engine's own numbers above)", span=8)
    r += 1
    for line in [
        "1) Engagement alert (Strategy 1) -- ship first: cheapest, fastest, biggest single lever (Low effort, "
        "1 month to impact).",
        "2) B2B playbook (Strategy 3) -- run in parallel: positive, no MRR downside, Medium effort.",
        "3) Annual migration offer (Strategy 2) -- sequence third: costs MRR for ~9 months before it pays "
        "back (see mrr_delta_pct_m6 above is negative for this strategy).",
    ]:
        ws.cell(row=r, column=1, value=line).font = BLACK
        ws.cell(row=r, column=1).alignment = Alignment(wrap_text=True)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
        ws.row_dimensions[r].height = 28
        r += 1

    freeze(ws, "A4")
    return ws


# =====================================================================
# CHECKS
# =====================================================================
def build_checks(wb, ue_refs, scen_refs):
    ws = wb.create_sheet("Checks")
    set_widths(ws, [50, 16, 16, 16, 40])
    r = 1
    title_row(ws, r, "Checks", span=5); r += 1
    note_row(ws, r, "TRUE/FALSE reconciliation checks. The master cell below is TRUE only if every check "
                     "in every section passes.", span=5)
    r += 2

    master_row = r
    ws.cell(row=r, column=1, value="ALL CHECKS PASS").font = Font(bold=True, size=13)
    master_cell = f"B{r}"
    r += 2
    check_flag_cells = []

    def add_check(label, formula, note=""):
        nonlocal r
        write_row(ws, r, [label, formula, note], fonts=[BLACK, BLACK, NOTE_FONT])
        check_flag_cells.append(f"B{r}")
        r += 1

    # ---------------- MRR bridge identity ----------------
    section_header(ws, r, "MRR bridge identity -- every month, opening+new+exp-contr-churn=closing (Data_MRR)", span=5)
    r += 1
    check_col = REFS['data_mrr_check_col']
    add_check("All 80 Data_MRR rows satisfy the bridge identity", f'=COUNTIF({check_col},FALSE)=0',
               "COUNTIF of the Data_MRR!J bridge_check column")
    r += 1

    # ---------------- Q1 / Q3 ----------------
    section_header(ws, r, "Q1 / Q3 totals", span=5)
    r += 1
    q1_row = REFS['q1_total_row']
    add_check("Q1 total MRR Apr-24 = 204,709.09 (sum of segments)",
               f'=ROUND(Answers_Q1_Q4!$B${q1_row},2)=ROUND({REFS["q1_target"]},2)',
               "Answers_Q1_Q4 Q1 total vs. Assumptions QA target")
    q3_row = REFS['q3_total_row']
    add_check("Q3 total active subs Apr-24 = 1,941",
               f'=Answers_Q1_Q4!$D${q3_row}={REFS["q3_target"]}',
               "Answers_Q1_Q4 Q3 total vs. Assumptions QA target")
    r += 1

    # ---------------- CAC / LTV vs mart ----------------
    section_header(ws, r, "CAC and LTV match mart_a2_12_unit_economics_summary within 1% (T6M basis, 60-month cap)", span=5)
    r += 1
    seg_row = ue_refs['seg_row']
    wp21_lookup = REFS['wp21_lookup']
    cac_ids = {"B2C": "A2-043", "SMB": "A2-058", "Enterprise": "A2-073"}
    ltv_ids = {"B2C": "A2-051", "SMB": "A2-066", "Enterprise": "A2-081"}
    tol = REFS['tol_cac_ltv']
    for seg in ["B2C", "SMB", "Enterprise"]:
        rr = seg_row[seg]
        add_check(f"{seg}: sheet CAC (T6M) vs. mart_a2_12 within 1%",
                   f'=ABS(UnitEconomics!$H${rr}-{wp21_lookup(cac_ids[seg])})/{wp21_lookup(cac_ids[seg])}<={tol}',
                   f"Assumptions register {cac_ids[seg]}")
        add_check(f"{seg}: sheet LTV (60mo cap, T6M GM) vs. mart_a2_12 within 1%",
                   f'=ABS(UnitEconomics!$N${rr}-{wp21_lookup(ltv_ids[seg])})/{wp21_lookup(ltv_ids[seg])}<={tol}',
                   f"Assumptions register {ltv_ids[seg]}; valid when the GM-basis selector = 'T6M avg'")
    r += 1

    # ---------------- Scenario reconciliation ----------------
    section_header(ws, r, "Scenario reconciliation -- Sheet vs. engine within tolerance (Scenarios tab)", span=5)
    r += 1
    recon_start = scen_refs['recon_start']; recon_end = scen_refs['recon_end']
    add_check("All Sheet-vs-engine scenario deltas are within tolerance",
               f'=COUNTIF(Scenarios!$F${recon_start}:$F${recon_end},FALSE)=0',
               "Scenarios!F column, tolerance = Assumptions tol_scenario (3%)")
    r += 1

    # ---------------- Retention-adjusted payback sanity ----------------
    section_header(ws, r, "Retention-adjusted payback sanity (resolves the WP40 open issue: computed on "
                           "the full 60-month curve, not just the observed horizon)", span=5)
    r += 1
    payback_start = ue_refs['payback_start']
    add_check("Retention-adjusted payback is populated (a number or '> 60') for B2C/SMB/Enterprise",
               f'=COUNTIF(UnitEconomics!$C${payback_start}:$C${payback_start+2},"")=0',
               "UnitEconomics payback block, column C")
    r += 1

    # ---------------- master formula ----------------
    ws.cell(row=master_row, column=2,
            value=f'=IF(COUNTIF(B{master_row+2}:B{r},FALSE)=0,"TRUE -- all checks pass","FALSE -- see failing rows below")')
    ws.cell(row=master_row, column=2).font = Font(bold=True, size=13)

    # conditional-format-like manual coloring pass (static at build time not possible for formulas;
    # add a plain legend instead since openpyxl conditional formatting on formula results needs the
    # engine to have run -- Google Sheets/Excel will color on open via the rule below)
    from openpyxl.formatting.rule import CellIsRule, FormulaRule
    rule_true = FormulaRule(formula=['TRUE'], fill=PASS_FILL)
    rule_false = FormulaRule(formula=['FALSE'], fill=FAIL_FILL)
    check_range = f"B{master_row+2}:B{r-1}"
    ws.conditional_formatting.add(check_range, rule_true)
    ws.conditional_formatting.add(check_range, rule_false)

    freeze(ws, "A4")
    return ws


# =====================================================================
# MAIN
# =====================================================================
def main():
    print("Connecting to db/platzi.duckdb (read_only)...")
    con = duckdb.connect(DB_PATH, read_only=True)

    wp21_df = pd.read_csv(WP21_CSV)
    wp31_df = pd.read_csv(WP31_CSV)

    mrr_df = con.execute("select * from mart_mrr_bridge order by segment, month_end").df()
    mrr_df["month_end"] = pd.to_datetime(mrr_df["month_end"])

    mkt_df = con.execute("select * from stg_marketing_spend order by month, segment, channel").df()
    mkt_df["month"] = pd.to_datetime(mkt_df["month"])
    # reorder to (month, segment, channel, spend, new_users_acquired) -- UnitEconomics/Assumptions
    # formulas below assume this exact column order (B=segment, D=spend)
    mkt_df = mkt_df[["month", "segment", "channel", "spend", "new_users_acquired"]]
    support_df = con.execute("select * from stg_support_costs order by month, category").df()
    support_df["month"] = pd.to_datetime(support_df["month"])
    newcust_df = con.execute(
        "select * from mart_a2_01_new_paying_customers order by month, segment").df()
    newcust_df["month"] = pd.to_datetime(newcust_df["month"])

    survival_df = con.execute(
        "select * from mart_a2_10_survival_curve order by segment, k").df()

    tail_df = con.execute(
        "select segment, k_rel, dollar_tail_decay, logo_tail_churn from mart_a2_11_lifetime "
        "where segment in ('B2C','SMB','Enterprise') "
        "order by case segment when 'B2C' then 1 when 'SMB' then 2 when 'Enterprise' then 3 end").df()

    q3_full = con.execute("select * from mart_q3_active_subs_apr24").df()
    stock_df = q3_full[(q3_full["plan_type"] != "Total") & (q3_full["segment"] != "Total")].copy()
    stock_df = stock_df.sort_values(["segment", "plan_type"]).reset_index(drop=True)

    mrr_apr24 = con.execute("select * from mart_q1_mrr_apr24").df()

    q2_df = con.execute("select * from mart_q2_retention_q1_24 order by segment, split").df()
    q4_df = con.execute("select * from mart_q4_ndr_t12m order by segment").df()

    engine_df = con.execute("select * from mart_s_03_scenario_summary").df()

    strategy_df = con.execute("select * from mart_s_04_strategy_impact").df()

    risk_agg = con.execute(
        "select sum(mrr) flagged_mrr, sum(mrr_at_risk) at_risk_mrr from mart_a1_06_may24_churn_risk "
        "where risk_tier in ('High','Medium')").df().iloc[0]
    flagged_mrr = float(risk_agg["flagged_mrr"])
    at_risk_mrr = float(risk_agg["at_risk_mrr"])

    con.close()
    print("Data pulled. Building workbook...")

    wb = Workbook()
    wb.remove(wb.active)

    build_readme(wb)
    build_assumptions(wb, wp21_df, wp31_df, tail_df, stock_df, mrr_apr24, flagged_mrr, at_risk_mrr)
    build_data_mrr(wb, mrr_df)
    build_data_costs(wb, mkt_df, support_df, newcust_df)
    build_data_survival(wb, survival_df)
    build_answers(wb, q2_df, q4_df)
    ue_ws, ue_refs = build_unit_economics(wb)
    scen_ws, scen_refs = build_scenarios(wb, engine_df)
    build_strategies(wb, strategy_df)
    build_checks(wb, ue_refs, scen_refs)

    # tab order per README's tab map
    order = ["README", "Assumptions", "Data_MRR", "Data_Costs", "Data_Survival", "Answers_Q1_Q4",
             "UnitEconomics", "Scenarios", "Strategies", "Checks"]
    wb._sheets = [wb[name] for name in order]
    wb.active = 0

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    wb.save(OUT_PATH)
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()

