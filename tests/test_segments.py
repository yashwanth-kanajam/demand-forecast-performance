from dataclasses import replace
from datetime import date

import numpy as np
import pandas as pd
import pytest

from dfp.analysis import enrich, segment_metrics
from dfp.config import load_config
from tests.test_metrics_benchmarks import make_hourly


@pytest.fixture(scope="module")
def enriched():
    cfg = replace(load_config(), start_ref_date=date(2025, 1, 1), end_ref_date=date(2025, 4, 1))
    h = make_hourly(cfg.start_ref_date, cfg.end_ref_date)
    h.loc[h.index[5], ["actual_mw", "is_paired"]] = [np.nan, False]   # one unpaired hour
    return enrich(h, cfg), h


def test_peak_is_top_decile_of_actual_within_ba_over_paired_hours(enriched):
    e, h = enriched
    paired = e[e["is_paired"]]
    q90 = paired["actual_mw"].quantile(0.90)
    assert ((paired["high_demand"] == "high") == (paired["actual_mw"] >= q90)).all()
    assert (paired["high_demand"] == "high").mean() == pytest.approx(0.10, abs=0.002)
    assert e.loc[~e["is_paired"], "high_demand"].isna().all()


def test_forecast_defined_peak_uses_published_forecast_not_actual(enriched):
    e, _ = enriched
    paired = e[e["is_paired"]]
    q90 = paired["forecast_mw"].quantile(0.90)
    assert ((paired["high_forecast"] == "high") == (paired["forecast_mw"] >= q90)).all()


def test_demand_bands_are_within_ba_quintiles(enriched):
    e, _ = enriched
    paired = e[e["is_paired"]]
    counts = paired["demand_band"].value_counts()
    assert sorted(counts.index) == ["Q1", "Q2", "Q3", "Q4", "Q5"]
    assert (counts.max() - counts.min()) <= 1
    band_max = paired.groupby("demand_band")["actual_mw"].max()
    band_min = paired.groupby("demand_band")["actual_mw"].min()
    for lo, hi in zip(["Q1", "Q2", "Q3", "Q4"], ["Q2", "Q3", "Q4", "Q5"]):
        assert band_max[lo] <= band_min[hi]
    assert e.loc[~e["is_paired"], "demand_band"].isna().all()


def test_demand_bands_are_scale_free_across_bas():
    cfg = replace(load_config(), start_ref_date=date(2025, 1, 1), end_ref_date=date(2025, 2, 1))
    small = make_hourly(cfg.start_ref_date, cfg.end_ref_date, ba="SMALL")
    big = make_hourly(cfg.start_ref_date, cfg.end_ref_date, ba="BIG")
    big[["actual_mw", "forecast_mw"]] *= 50
    e = enrich(pd.concat([small, big], ignore_index=True), cfg)
    shares = e.groupby(["ba_code", "demand_band"]).size().unstack()
    assert (shares.loc["SMALL"] == shares.loc["BIG"]).all()


def test_segment_rows_cover_every_paired_hour_once_per_segment_type(enriched):
    e, _ = enriched
    seg = segment_metrics(e)
    pub = seg[(seg["eval_set"] == "paired") & (seg["forecast_type"] == "published")]
    n = pub.groupby("segment_type")["n_hours"].sum()
    assert (n == e["is_paired"].sum()).all()


# --- Phase 2.5: peak robustness and category logic ---------------------------------

from dfp.analysis import assign_category, classify_peak  # noqa: E402


@pytest.mark.parametrize("actual,forecast,expected", [
    ("under", "under", "robust underforecast"),
    ("over", "over", "robust overforecast"),
    ("under", None, "selection-sensitive (underforecast on actual-defined peaks only)"),
    (None, "over", "forecast-defined overforecast only"),
    ("under", "over", "contradictory"),
    (None, None, "no consistent peak bias"),
])
def test_peak_robustness_classification(actual, forecast, expected):
    assert classify_peak(actual, forecast) == expected


@pytest.mark.parametrize("rule,bias,persistent,flagged,expected", [
    ("improvement: project rule met", -1.5, True, False, "A"),
    ("improvement: project rule met", -5.8, True, True, "B"),
    ("below project rule (|change| < 5%)", 1.1, True, False, "C"),
    ("below project rule (|change| < 5%)", -0.02, False, False, "D"),
    ("degradation: project rule met", 0.3, False, False, "D"),
    ("mixed across years", 2.0, False, False, "u"),
])
def test_category_assignment(rule, bias, persistent, flagged, expected):
    assert assign_category(rule, bias, persistent, flagged, 1.0)[0] == expected
