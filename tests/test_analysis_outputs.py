"""Reconciliation invariants on generated analytical outputs. Skipped until the pipeline has run."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from dfp.analysis import extreme_concentration_threshold_pct
from dfp.config import load_config
from dfp.metrics import worst_share

ROOT = Path(__file__).resolve().parents[1]
HOURLY = ROOT / "data" / "curated" / "fact_hourly_performance.parquet"
OUT = ROOT / "data" / "analysis"
pytestmark = pytest.mark.skipif(not (HOURLY.exists() and (OUT / "ba_reconciliation.csv").exists()),
                                reason="run `python -m dfp.pipeline` first")
KNOWN_EXCEPTIONS = {"PERSISTENT_DIRECTIONAL_BIAS", "HOUR_SPECIFIC_BIAS", "HIGH_DEMAND_UNDERFORECAST",
                    "HIGH_DEMAND_OVERFORECAST", "EXTREME_HOUR_CONCENTRATION", "SEASON_SPECIFIC_DETERIORATION",
                    "PRACTICAL_GAIN_FROM_CORRECTION", "CORRECTION_DEGRADES_FORECAST",
                    "ERROR_NOT_BIAS_CORRECTABLE", "WEAK_SKILL_VS_NAIVE",
                    "SOURCE_SEMANTIC_FORECAST_LEVEL_ANOMALY"}


@pytest.fixture(scope="module")
def h():
    return pd.read_parquet(HOURLY)


@pytest.fixture(scope="module")
def rec():
    return pd.read_csv(OUT / "ba_reconciliation.csv").set_index("ba_code")


@pytest.fixture(scope="module")
def seg():
    return pd.read_csv(OUT / "segment_metrics.csv", dtype={"segment_value": str})


def test_threshold_is_in_percent_units():
    assert extreme_concentration_threshold_pct(load_config()) == pytest.approx(7.249, abs=0.01)


def test_reconciliation_recomputes_from_hourly(h, rec):
    p = h[h["is_paired"]]
    for ba, g in p.groupby("ba_code"):
        r = rec.loc[ba]
        e = g["forecast_mw"] - g["actual_mw"]
        assert r["paired_n_hours"] == len(g)
        assert r["published_wape_pct_all_paired"] == pytest.approx(100 * e.abs().sum() / g["actual_mw"].sum(), rel=1e-5)
        assert r["published_mae_mw_all_paired"] == pytest.approx(e.abs().mean(), rel=1e-5)
        assert r["published_norm_bias_pct_all_paired"] == pytest.approx(100 * e.sum() / g["actual_mw"].sum(), rel=1e-4)
        assert r["worst1_contribution_pct_all_paired"] == pytest.approx(worst_share(e.abs(), g["utc_period_end"]), rel=1e-5)
        c = g[g["in_common_set"]]
        corr = 100 * (c["corrected_forecast_mw"] - c["actual_mw"]).abs().sum() / c["actual_mw"].sum()
        assert r["corrected_wape_pct_common"] == pytest.approx(corr, rel=1e-5)


def test_common_set_is_subset_of_paired(h, rec):
    assert not (h["in_common_set"] & ~h["is_paired"]).any()
    assert (rec["common_n_hours"] <= rec["paired_n_hours"]).all()


def test_segment_sums_add_up_to_overall(seg):
    base = seg[(seg["eval_set"] == "paired") & (seg["forecast_type"] == "published")]
    overall = base[base["segment_type"] == "overall"].set_index("ba_code")
    for t in ("ref_hour", "day_type", "season", "year_month", "eval_year", "demand_band", "high_demand"):
        s = base[base["segment_type"] == t].groupby("ba_code")[["n_hours", "sum_abs_error_mw_h", "sum_actual_mw_h"]].sum()
        np.testing.assert_allclose(s.values, overall[s.columns].loc[s.index].values, rtol=1e-6)


def test_correction_is_causal_on_real_rows(h):
    # every corrected value exists only with >= min_days of history and a usable published forecast
    c = h[h["corrected_forecast_mw"].notna()]
    assert (c["adjustment_days"] >= load_config().analysis["correction_min_days"]).all()
    assert c["forecast_mw"].notna().all()


def test_naive_baseline_always_precedes_target(h):
    ok = h[h["naive_status"] == "ok"]
    lag = ok["utc_period_end"] - ok["naive_source_utc_period_end"]
    assert lag.between(pd.Timedelta(hours=167), pd.Timedelta(hours=169)).all()


def test_exceptions_reference_known_codes_and_selected_bas():
    x = pd.read_csv(OUT / "exception_candidates.csv")
    assert set(x["exception"]) <= KNOWN_EXCEPTIONS
    assert set(x["ba_code"]) <= set(load_config().selected_bas)
    assert x["evidence"].str.len().gt(0).all()


# --- BI handoff ------------------------------------------------------------------

BI = ROOT / "data" / "bi"


def test_bi_fact_reconciles_to_metric_summary(rec):
    f = pd.read_csv(BI / "fact_hourly_performance.csv")
    s = pd.read_csv(BI / "ba_metric_summary.csv").set_index("ba_code")
    assert set(f.columns) >= {"ba_code", "utc_period_end", "ref_date", "actual_mw", "forecast_mw"}
    assert "Unnamed: 0" not in f.columns
    p = f[f["is_paired"]]
    for ba, g in p.groupby("ba_code"):
        wape = 100 * (g["forecast_mw"] - g["actual_mw"]).abs().sum() / g["actual_mw"].sum()
        assert wape == pytest.approx(s.loc[ba, "published_wape_pct_all_paired"], rel=1e-9)
        c = g[g["in_common_set"]]
        cw = 100 * (c["corrected_forecast_mw"] - c["actual_mw"]).abs().sum() / c["actual_mw"].sum()
        assert cw == pytest.approx(s.loc[ba, "corrected_wape_pct_common"], rel=1e-9)
    pd.testing.assert_frame_equal(s.reset_index(), rec.reset_index(), check_dtype=False)


def test_bi_dates_are_iso_and_keys_join():
    f = pd.read_csv(BI / "fact_hourly_performance.csv", dtype=str)
    d = pd.read_csv(BI / "dim_date.csv", dtype=str)
    b = pd.read_csv(BI / "dim_ba.csv", dtype=str)
    assert f["utc_period_end"].str.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:00:00Z").all()
    assert f["ref_date"].str.fullmatch(r"\d{4}-\d{2}-\d{2}").all()
    assert d["date"].is_unique and set(f["ref_date"]) <= set(d["date"])
    assert b["ba_code"].is_unique and set(f["ba_code"]) == set(b["ba_code"])
    assert set(f["is_paired"].unique()) <= {"true", "false"}
    assert not f.duplicated(["ba_code", "utc_period_end"]).any()


def test_exceptions_state_rule_and_sample_size():
    x = pd.read_csv(BI / "exception_candidates.csv")
    assert (x["n_hours"] > 0).all() and x["rule"].str.len().gt(0).all()


# --- fair comparison set -----------------------------------------------------------

def test_three_comparison_variants_use_identical_target_hour_keys(h):
    """Published, naive and corrected common-set metrics are computed on exactly the same (BA, UTC) keys."""
    c = h[h["in_common_set"]]
    keys = {}
    for col in ("forecast_mw", "naive_forecast_mw", "corrected_forecast_mw"):
        used = c[c["actual_mw"].notna() & c[col].notna()]
        keys[col] = set(zip(used["ba_code"], used["utc_period_end"]))
    assert keys["forecast_mw"] == keys["naive_forecast_mw"] == keys["corrected_forecast_mw"]
    assert len(keys["forecast_mw"]) == len(c)


def test_common_segment_counts_identical_across_forecast_types(seg):
    c = seg[seg["eval_set"] == "common"]
    n = c.pivot_table(index=["ba_code", "segment_type", "segment_value"], columns="forecast_type", values="n_hours")
    assert (n["published"] == n["seasonal_naive"]).all() and (n["published"] == n["bias_corrected"]).all()


def test_common_set_published_metrics_recompute(h, rec):
    for ba, g in h[h["in_common_set"]].groupby("ba_code"):
        r = rec.loc[ba]
        e = g["forecast_mw"] - g["actual_mw"]
        assert r["common_n_hours"] == len(g)
        assert r["published_wape_pct_common"] == pytest.approx(100 * e.abs().sum() / g["actual_mw"].sum(), rel=1e-9)
        assert r["published_mae_mw_common"] == pytest.approx(e.abs().mean(), rel=1e-9)
        assert r["published_norm_bias_pct_common"] == pytest.approx(100 * e.sum() / g["actual_mw"].sum(), rel=1e-9)
        en = g["naive_forecast_mw"] - g["actual_mw"]
        assert r["naive_mae_mw_common"] == pytest.approx(en.abs().mean(), rel=1e-9)


def test_delta_is_computed_from_common_set_metrics_only(rec):
    rel = 100 * (rec["corrected_wape_pct_common"] / rec["published_wape_pct_common"] - 1)
    np.testing.assert_allclose(rec["corrected_vs_published_common_relative_delta_pct"], rel, rtol=1e-12)
    pp = rec["corrected_wape_pct_common"] - rec["published_wape_pct_common"]
    np.testing.assert_allclose(rec["corrected_vs_published_common_delta_pp"], pp, rtol=1e-12)


def test_peak_exceptions_only_for_robust_peak_patterns():
    x = pd.read_csv(OUT / "exception_candidates.csv")
    pk = pd.read_csv(OUT / "peak_robustness.csv").set_index("ba_code")
    for _, row in x[x["exception"].str.startswith("HIGH_DEMAND_")].iterrows():
        assert pk.loc[row["ba_code"], "peak_robustness"].startswith("robust")


def test_categories_follow_rules(rec):
    cfg = load_config()
    for ba, r in rec.iterrows():
        cat = r["category"]
        if r["project_rule_class"] == "improvement: project rule met":
            assert cat.startswith("B") == (ba in cfg.source_flagged_bas) and cat[0] in "AB"
        else:
            assert cat[0] in "CD"


# --- DAX-logic replica from BI CSVs ---------------------------------------------

def test_dax_logic_replica_reproduces_reference_values(rec):
    from dfp.bi_replica import RECONCILED, replicate
    rep = replicate()
    s = pd.read_csv(BI / "ba_metric_summary.csv").set_index("ba_code")
    for m in RECONCILED:
        np.testing.assert_allclose(rep[m].loc[s.index].astype(float), s[m].astype(float), rtol=1e-9, atol=1e-9, err_msg=m)


def test_dim_ba_labels_and_flags_reconcile_to_summary():
    cfg = load_config()
    d = pd.read_csv(BI / "dim_ba.csv", dtype=str, keep_default_na=False).set_index("ba_code")
    s = pd.read_csv(BI / "ba_metric_summary.csv").set_index("ba_code")
    assert d.index.is_unique and set(d.index) == set(cfg.selected_bas)
    assert (d["category_code"] == s.loc[d.index, "category"].str[0]).all()
    flagged = set(d.index[d["source_semantic_flag"] == "true"])
    assert flagged == set(cfg.source_flagged_bas) == set(s.index[s["source_semantic_flag"].astype(bool)])
    assert (d.loc[list(flagged), "source_semantics_display"] == "SOURCE SEMANTICS UNCERTAIN").all()
    assert (d.loc[d.index.difference(list(flagged)), "source_semantics_display"] == "").all()


def test_all_bi_csvs_load_with_unique_keys():
    f = pd.read_csv(BI / "fact_hourly_performance.csv", usecols=["ba_code", "utc_period_end", "is_paired", "in_common_set",
                                                                  "actual_mw", "forecast_mw", "naive_forecast_mw",
                                                                  "corrected_forecast_mw"])
    assert not f.duplicated(["ba_code", "utc_period_end"]).any()
    common = f["in_common_set"]
    assert (f.loc[common, ["actual_mw", "forecast_mw", "naive_forecast_mw", "corrected_forecast_mw"]].notna().all().all())
    assert (f["is_paired"] | ~common).all()
    assert pd.read_csv(BI / "dim_date.csv")["date"].is_unique
    x = pd.read_csv(BI / "exception_candidates.csv")
    assert not x.duplicated(["ba_code", "exception"]).any()
