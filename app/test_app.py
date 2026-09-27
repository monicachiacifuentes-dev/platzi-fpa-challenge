"""WP33 -- verification tests for the Streamlit dashboard.

Run:
    export PYTHONIOENCODING=utf-8
    ./.venv/Scripts/python.exe -m pytest app/test_app.py -v
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent / "streamlit_app.py")


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
    # sidebar segment radio defaults to "All"
    mrr_value = _metric_value(at, "MRR, Apr-24")
    subs_value = _metric_value(at, "Active subscriptions")
    assert mrr_value.replace(",", "").replace("$", "") == "204,709".replace(",", "")
    assert subs_value.replace(",", "") == "1941"


def test_segment_filter_options_run_without_exception():
    for choice in ["All", "B2C", "SMB", "Enterprise"]:
        at = AppTest.from_file(APP_PATH, default_timeout=60)
        at.run()
        radio = at.sidebar.radio[0]
        radio.set_value(choice).run()
        assert not at.exception, f"Segment={choice} raised: {[e.value for e in at.exception]}"


def test_segment_kpis_reconcile_to_mart_totals():
    import pandas as pd
    marts = Path(__file__).resolve().parents[1] / "outputs" / "marts"
    bridge = pd.read_csv(marts / "mart_mrr_bridge.csv", parse_dates=["month_end"])
    q3 = pd.read_csv(marts / "mart_q3_active_subs_apr24.csv")
    expected_mrr = {
        "All": bridge.loc[(bridge.month_end == "2024-04-30") & (bridge.segment == "Total"), "closing_mrr"].iloc[0],
        "B2C": bridge.loc[(bridge.month_end == "2024-04-30") & (bridge.segment == "B2C"), "closing_mrr"].iloc[0],
        "SMB": bridge.loc[(bridge.month_end == "2024-04-30") & (bridge.segment == "SMB"), "closing_mrr"].iloc[0],
        "Enterprise": bridge.loc[(bridge.month_end == "2024-04-30") & (bridge.segment == "Enterprise"), "closing_mrr"].iloc[0],
    }
    expected_subs = {
        "All": q3.loc[(q3.segment == "Total") & (q3.plan_type == "Total"), "active_subs"].iloc[0],
        "B2C": q3.loc[(q3.segment == "B2C") & (q3.plan_type == "Total"), "active_subs"].iloc[0],
        "SMB": q3.loc[(q3.segment == "SMB") & (q3.plan_type == "Total"), "active_subs"].iloc[0],
        "Enterprise": q3.loc[(q3.segment == "Enterprise") & (q3.plan_type == "Total"), "active_subs"].iloc[0],
    }
    for choice in ["All", "B2C", "SMB", "Enterprise"]:
        at = AppTest.from_file(APP_PATH, default_timeout=60)
        at.run()
        at.sidebar.radio[0].set_value(choice).run()
        assert not at.exception
        mrr_value = _metric_value(at, "MRR, Apr-24")
        subs_value = _metric_value(at, "Active subscriptions")
        got_mrr = float(mrr_value.replace("$", "").replace(",", ""))
        got_subs = int(subs_value.replace(",", ""))
        assert abs(got_mrr - expected_mrr[choice]) < 1.0, f"{choice}: {got_mrr} vs {expected_mrr[choice]}"
        assert got_subs == int(expected_subs[choice]), f"{choice}: {got_subs} vs {expected_subs[choice]}"


def test_retention_toggles_run_without_exception():
    at = _fresh_app()
    toggles = at.toggle
    assert len(toggles) >= 2
    for t in toggles:
        t.set_value(True).run()
        assert not at.exception, f"Toggle {t.label} raised: {[e.value for e in at.exception]}"
        t.set_value(False).run()
        assert not at.exception


def test_gm_basis_radio_runs_without_exception():
    at = _fresh_app()
    radios = [r for r in at.radio if r.label == "Gross margin basis"]
    assert radios, "Gross margin basis radio not found"
    r = radios[0]
    for opt in r.options:
        r.set_value(opt).run()
        assert not at.exception, f"GM basis={opt} raised: {[e.value for e in at.exception]}"


def test_scenario_sliders_run_without_exception():
    at = _fresh_app()
    sliders = at.slider
    assert len(sliders) >= 3
    for s in sliders:
        lo, hi = s.min, s.max
        s.set_value(hi).run()
        assert not at.exception, f"Slider {s.label} raised at max: {[e.value for e in at.exception]}"
        s.set_value(lo).run()
        assert not at.exception, f"Slider {s.label} raised at min: {[e.value for e in at.exception]}"


def test_case_select_slider_runs_without_exception():
    at = _fresh_app()
    case_sliders = [s for s in at.select_slider if s.label == "Case"]
    assert case_sliders
    s = case_sliders[0]
    for opt in ["low", "base", "high"]:
        s.set_value(opt).run()
        assert not at.exception, f"Case={opt} raised: {[e.value for e in at.exception]}"


def test_churn_risk_download_button_present():
    at = _fresh_app()
    assert len(at.get("download_button")) >= 1
