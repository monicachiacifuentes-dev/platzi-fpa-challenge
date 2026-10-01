"""WP33 -- verification tests for the Streamlit dashboard.

Run:
    export PYTHONIOENCODING=utf-8
    ./.venv/Scripts/python.exe -m pytest app/test_app.py -v
"""
from itertools import combinations
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent / "streamlit_app.py")
MARTS = Path(__file__).resolve().parents[1] / "outputs" / "marts"
SEGMENT_ORDER = ["B2C", "SMB", "Enterprise"]

# All 7 non-empty combinations of the 3 base segments, in a fixed, readable order.
ALL_COMBOS = [list(c) for n in (1, 2, 3) for c in combinations(SEGMENT_ORDER, n)]


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    assert not at.exception, f"App raised on load: {[e.value for e in at.exception]}"
    return at


def _metric_value(at: AppTest, label_substring: str) -> str:
    for m in at.get("metric"):
        if label_substring in m.label:
            return m.value
    raise AssertionError(f"No metric found with label containing {label_substring!r}; "
                          f"labels were {[m.label for m in at.get('metric')]}")


def test_app_loads_without_exception():
    at = _fresh_app()
    assert len(at.tabs) == 5


def test_headline_kpis_match_executive_summary_when_all_segments():
    at = _fresh_app()
    # sidebar multiselect defaults to all three segments
    mrr_value = _metric_value(at, "MRR, Apr-24")
    subs_value = _metric_value(at, "Active subscriptions")
    assert mrr_value.replace(",", "").replace("$", "") == "204,709".replace(",", "")
    assert subs_value.replace(",", "") == "1941"


def test_segment_combinations_run_without_exception_on_every_tab():
    """No exceptions for every one of the 7 non-empty combinations, and for an
    empty selection, across every tab/toggle combination."""
    for combo in ALL_COMBOS + [[]]:
        at = AppTest.from_file(APP_PATH, default_timeout=60)
        at.run()
        at.sidebar.multiselect[0].set_value(combo).run()
        assert not at.exception, f"Segments={combo} raised on select: {[e.value for e in at.exception]}"

        for t in at.toggle:
            t.set_value(True).run()
            assert not at.exception, f"Segments={combo}, toggle {t.label}=True raised: {[e.value for e in at.exception]}"
            t.set_value(False).run()
            assert not at.exception, f"Segments={combo}, toggle {t.label}=False raised: {[e.value for e in at.exception]}"

        gm_radios = [r for r in at.radio if r.label == "Gross margin basis"]
        for opt in gm_radios[0].options if gm_radios else []:
            gm_radios[0].set_value(opt).run()
            assert not at.exception, f"Segments={combo}, GM basis={opt} raised: {[e.value for e in at.exception]}"

        case_sliders = [s for s in at.select_slider if s.label == "Case"]
        for opt in (["low", "base", "high"] if case_sliders else []):
            case_sliders[0].set_value(opt).run()
            assert not at.exception, f"Segments={combo}, case={opt} raised: {[e.value for e in at.exception]}"

        for s in at.slider:
            s.set_value(s.max).run()
            assert not at.exception, f"Segments={combo}, slider {s.label} raised at max: {[e.value for e in at.exception]}"
            s.set_value(s.min).run()
            assert not at.exception, f"Segments={combo}, slider {s.label} raised at min: {[e.value for e in at.exception]}"


def test_empty_selection_falls_back_to_all_with_caption():
    at = _fresh_app()
    at.sidebar.multiselect[0].set_value([]).run()
    assert not at.exception
    captions = [c.value for c in at.sidebar.caption]
    assert any("showing all segments" in c.lower() for c in captions)
    mrr_value = _metric_value(at, "MRR, Apr-24")
    assert mrr_value.replace(",", "").replace("$", "") == "204709"


def test_segment_kpis_match_expected_values():
    cases = {
        ("B2C", "SMB", "Enterprise"): (204709.09, 1941),
        ("SMB", "Enterprise"): (140344.09, 405),
        ("B2C", "SMB"): (118234.37, 1839),
        ("B2C",): (64365.00, 1536),
    }
    for combo, (expected_mrr, expected_subs) in cases.items():
        at = AppTest.from_file(APP_PATH, default_timeout=60)
        at.run()
        at.sidebar.multiselect[0].set_value(list(combo)).run()
        assert not at.exception, f"Segments={combo} raised: {[e.value for e in at.exception]}"
        mrr_value = _metric_value(at, "MRR, Apr-24")
        subs_value = _metric_value(at, "Active subscriptions")
        got_mrr = float(mrr_value.replace("$", "").replace(",", ""))
        got_subs = int(subs_value.replace(",", ""))
        assert abs(got_mrr - expected_mrr) < 1.0, f"{combo}: MRR {got_mrr} vs {expected_mrr}"
        assert got_subs == expected_subs, f"{combo}: subs {got_subs} vs {expected_subs}"


def test_custom_combo_retention_matches_precomputed_rollup():
    """{SMB, Enterprise} logo retention must equal the precomputed B2B row in
    mart_q2_retention_q1_24.csv exactly (split=all, method=M06_primary) -- this
    proves the aggregation path matches the rollup. All three segments must
    equal the Total row."""
    q2 = pd.read_csv(MARTS / "mart_q2_retention_q1_24.csv")
    b2b_row = q2.loc[(q2.segment == "B2B") & (q2.split == "all") & (q2.method == "M06_primary")].iloc[0]
    total_row = q2.loc[(q2.segment == "Total") & (q2.split == "all") & (q2.method == "M06_primary")].iloc[0]
    assert round(b2b_row.logo_rate, 4) == 0.9377
    assert round(total_row.logo_rate, 4) == 0.9009

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    at.sidebar.multiselect[0].set_value(["SMB", "Enterprise"]).run()
    assert not at.exception
    ret_metric = _metric_value(at, "Q1-24 retention (logo)")
    assert ret_metric.strip("%") == f"{b2b_row.logo_rate * 100:.1f}"

    at2 = AppTest.from_file(APP_PATH, default_timeout=60)
    at2.run()
    ret_metric_all = _metric_value(at2, "Q1-24 retention (logo)")
    assert ret_metric_all.strip("%") == f"{total_row.logo_rate * 100:.1f}"


def test_churn_risk_download_button_present():
    at = _fresh_app()
    assert len(at.get("download_button")) >= 1


def test_ltv_cac_margin_basis_has_three_options_and_runs():
    at = _fresh_app()
    radio = at.radio(key="gm_basis")
    assert [o.split(" (")[0] for o in radio.options] == ["Trailing 6 months", "Trailing 3 months", "Apr-24 run-rate"]
    for opt in radio.options:
        at.radio(key="gm_basis").set_value(opt).run()
        assert not at.exception, f"App raised for margin basis {opt!r}: {[e.value for e in at.exception]}"


def test_payback_table_follows_margin_basis_and_matches_summary():
    at = _fresh_app()
    radio = at.radio(key="gm_basis")
    apr = next(o for o in radio.options if o.startswith("Apr-24"))
    at.radio(key="gm_basis").set_value(apr).run()
    table = next(df.value for df in at.dataframe if "Payback, months (6-mo CAC)" in df.value.columns)
    payback = table["Payback, months (6-mo CAC)"]
    # Executive summary: SMB payback ~10 months, Enterprise ~12 at the Apr-24 41% margin
    assert payback.loc["SMB"] == 10.4 and payback.loc["Enterprise"] == 12.2
