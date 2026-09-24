import math
from datetime import date

import numpy as np
import pandas as pd
import pytest

from dfp.benchmarks import naive_utc_lag, seasonal_naive, trailing_bias_correction
from dfp.metrics import aggregate, gaussian_worst_share, summarize, worst_share
from dfp.timestamps import derive_reference_attributes, expected_period_ends

NY, PHX = "America/New_York", "America/Phoenix"


def make_hourly(start: date, end: date, tz: str = NY, ba: str = "TST", seed: int = 0) -> pd.DataFrame:
    ends = pd.Series(expected_period_ends(start, end, tz))
    h = pd.concat([pd.DataFrame({"ba_code": ba, "utc_period_end": ends}),
                   derive_reference_attributes(ends, tz)], axis=1)
    rng = np.random.default_rng(seed)
    h["actual_mw"] = 1000 + 100 * rng.random(len(h))
    h["forecast_mw"] = h["actual_mw"] + 20  # constant +20 MW overforecast
    h["is_paired"] = True
    return h


# --- metric arithmetic -----------------------------------------------------------

def test_wape_mae_and_bias_known_example():
    m = summarize(pd.Series([100.0, 200.0]), pd.Series([110.0, 180.0]))
    assert m["wape_pct"] == pytest.approx(10.0)        # (10 + 20) / 300
    assert m["mae_mw"] == pytest.approx(15.0)
    assert m["bias_mw"] == pytest.approx(-5.0)         # (+10 - 20) / 2
    assert m["norm_bias_pct"] == pytest.approx(-10 / 3)


def test_bias_sign_positive_means_overforecast():
    assert summarize(pd.Series([100.0]), pd.Series([120.0]))["bias_mw"] > 0
    assert summarize(pd.Series([100.0]), pd.Series([80.0]))["norm_bias_pct"] < 0


def test_metrics_exclude_unpaired_rows():
    m = summarize(pd.Series([100.0, np.nan, 50.0]), pd.Series([110.0, 999.0, np.nan]))
    assert m["n_hours"] == 1 and m["mae_mw"] == 10


def test_segment_sums_reaggregate_to_overall():
    h = make_hourly(date(2025, 1, 1), date(2025, 1, 15))
    h["forecast_mw"] = h["actual_mw"] * (1 + 0.05 * np.sin(h["ref_hour"]))
    by_hour = aggregate(h, ["ba_code", "ref_hour"], "actual_mw", "forecast_mw")
    overall = aggregate(h, ["ba_code"], "actual_mw", "forecast_mw").iloc[0]
    for col in ("n_hours", "sum_actual_mw_h", "sum_abs_error_mw_h", "sum_error_mw_h"):
        assert by_hour[col].sum() == pytest.approx(overall[col])
    assert 100 * by_hour["sum_abs_error_mw_h"].sum() / by_hour["sum_actual_mw_h"].sum() == pytest.approx(overall["wape_pct"])
    # WAPE of the whole is not the mean of segment WAPEs
    assert by_hour["wape_pct"].mean() != pytest.approx(overall["wape_pct"], rel=1e-9)


def test_worst_one_percent_contribution():
    ae = pd.Series([1.0] * 198 + [100.0, 100.0])       # n=200 -> k=2
    assert worst_share(ae) == pytest.approx(100 * 200 / 398)
    assert worst_share(pd.Series([1.0] * 149 + [50.0])) == pytest.approx(100 * 51 / 199)  # n=150 -> k=ceil(1.5)=2


def test_gaussian_reference_values():
    assert gaussian_worst_share(0.01) == pytest.approx(0.0362, abs=5e-4)
    rng = np.random.default_rng(1)
    e = pd.Series(np.abs(rng.normal(size=400_000)))
    assert worst_share(e) / 100 == pytest.approx(gaussian_worst_share(0.01), abs=1e-3)


# --- seasonal naive --------------------------------------------------------------

def naive_for(h):
    return pd.concat([h, seasonal_naive(h, 7)], axis=1)


def test_naive_is_causal_and_exactly_one_reference_week_earlier():
    h = naive_for(make_hourly(date(2025, 6, 1), date(2025, 7, 1)))
    ok = h[h["naive_status"] == "ok"]
    assert (ok["naive_source_utc_period_end"] < ok["utc_period_end"]).all()
    src = h.set_index("utc_period_end")["ref_period_start"]
    assert ((ok["ref_period_start"] - src.loc[ok["naive_source_utc_period_end"]].values)
            == pd.Timedelta(days=7)).all()
    assert (h.loc[h["ref_date"] < "2025-06-08", "naive_status"] == "before_window").all()


def test_naive_ignores_future_values():
    h = make_hourly(date(2025, 6, 1), date(2025, 7, 1))
    base = seasonal_naive(h)["naive_forecast_mw"]
    cutoff = h["utc_period_end"] >= pd.Timestamp("2025-06-20", tz="UTC")
    h2 = h.copy()
    h2.loc[cutoff, "actual_mw"] *= 5
    after = seasonal_naive(h2)["naive_forecast_mw"]
    pd.testing.assert_series_equal(base[~cutoff], after[~cutoff])


def test_naive_spring_forward_week_after_has_no_baseline_for_2am():
    h = naive_for(make_hourly(date(2025, 3, 1), date(2025, 3, 25)))
    target = h[(h["ref_date"] == "2025-03-16") & (h["ref_hour"] == 2)]
    assert len(target) == 1 and target["naive_status"].iloc[0] == "hour_absent"
    assert np.isnan(target["naive_forecast_mw"].iloc[0])
    # 03:00 the same day: both instants are EDT, so the clock lookup is 168 UTC hours back ...
    t3 = h[(h["ref_date"] == "2025-03-16") & (h["ref_hour"] == 3)].iloc[0]
    assert t3["utc_period_end"] - t3["naive_source_utc_period_end"] == pd.Timedelta(hours=168)
    # ... but on the transition day itself the baseline is EST: same clock hour, 167 UTC hours back
    t_day_of = h[(h["ref_date"] == "2025-03-09") & (h["ref_hour"] == 3)].iloc[0]
    assert t_day_of["utc_period_end"] - t_day_of["naive_source_utc_period_end"] == pd.Timedelta(hours=167)


def test_naive_fall_back_duplicated_hour_is_deterministic():
    h = naive_for(make_hourly(date(2024, 10, 25), date(2024, 11, 15)))
    day_of = h[(h["ref_date"] == "2024-11-03") & (h["ref_hour"] == 1)]
    assert len(day_of) == 2 and day_of["naive_source_utc_period_end"].nunique() == 1   # both use the single prior 01:00
    week_after = h[(h["ref_date"] == "2024-11-10") & (h["ref_hour"] == 1)].iloc[0]
    first_instance = day_of["utc_period_end"].min()
    assert week_after["naive_source_utc_period_end"] == first_instance


def test_naive_fixed_offset_zone_equals_168h_lag():
    h = make_hourly(date(2025, 3, 1), date(2025, 4, 1), tz=PHX)
    n = seasonal_naive(h)["naive_forecast_mw"]
    pd.testing.assert_series_equal(n, naive_utc_lag(h, 168), check_names=False)


def test_naive_missing_baseline_actual_is_not_filled():
    h = make_hourly(date(2025, 6, 1), date(2025, 7, 1))
    gap = (h["ref_date"] == "2025-06-10") & (h["ref_hour"] == 12)
    h.loc[gap, "actual_mw"] = np.nan
    n = pd.concat([h, seasonal_naive(h)], axis=1)
    t = n[(n["ref_date"] == "2025-06-17") & (n["ref_hour"] == 12)].iloc[0]
    assert t["naive_status"] == "actual_missing" and np.isnan(t["naive_forecast_mw"])


# --- trailing bias correction ---------------------------------------------------

def corr_at(h, day, hour, **kw):
    c = pd.concat([h, trailing_bias_correction(h, **kw)], axis=1)
    return c[(c["ref_date"] == day) & (c["ref_hour"] == hour)].iloc[0]


def test_correction_removes_constant_bias():
    h = make_hourly(date(2025, 1, 1), date(2025, 3, 1))
    r = corr_at(h, "2025-02-20", 12)
    assert r["adjustment_mw"] == pytest.approx(-20.0)   # residual = actual - forecast
    assert r["corrected_forecast_mw"] == pytest.approx(r["actual_mw"])


@pytest.mark.parametrize("offset_days,changes", [(0, False), (1, False), (2, True), (29, True), (30, False)])
def test_correction_uses_only_days_d_minus_29_to_d_minus_2(offset_days, changes):
    h = make_hourly(date(2025, 1, 1), date(2025, 3, 1))
    target = pd.Timestamp("2025-02-20")
    before = corr_at(h, target, 12)["adjustment_mw"]
    h2 = h.copy()
    day = h2["ref_date"] == target - pd.Timedelta(days=offset_days)
    h2.loc[day, "actual_mw"] += 5000  # perturb that whole day's residuals
    after = corr_at(h2, target, 12)["adjustment_mw"]
    assert (before != pytest.approx(after)) is changes


def test_correction_is_hour_specific():
    h = make_hourly(date(2025, 1, 1), date(2025, 3, 1))
    h.loc[h["ref_hour"] == 7, "forecast_mw"] += 100
    assert corr_at(h, "2025-02-20", 7)["adjustment_mw"] == pytest.approx(-120.0)
    assert corr_at(h, "2025-02-20", 8)["adjustment_mw"] == pytest.approx(-20.0)


def test_correction_min_history():
    h = make_hourly(date(2025, 1, 1), date(2025, 3, 1))
    # target D uses D-29..D-2; with the window starting 2025-01-01, D = 2025-01-15 has 13 days, D = 2025-01-16 has 14
    assert np.isnan(corr_at(h, "2025-01-15", 12, min_days=14)["corrected_forecast_mw"])
    assert corr_at(h, "2025-01-16", 12, min_days=14)["adjustment_days"] == 14
    assert not np.isnan(corr_at(h, "2025-01-16", 12, min_days=14)["corrected_forecast_mw"])


def test_correction_counts_days_not_hours_and_skips_missing_residuals():
    h = make_hourly(date(2025, 1, 1), date(2025, 3, 1))
    h.loc[(h["ref_date"] >= "2025-01-20") & (h["ref_date"] < "2025-02-10") & (h["ref_hour"] == 12), "actual_mw"] = np.nan
    r = corr_at(h, "2025-02-20", 12)
    # window 2025-01-22 .. 2025-02-18 (28 days); 19 of them blanked -> 9 days < 14
    assert r["adjustment_days"] == 9 and np.isnan(r["corrected_forecast_mw"])


def test_no_target_leakage_corrected_value_independent_of_target_actual():
    h = make_hourly(date(2025, 1, 1), date(2025, 3, 1))
    a = corr_at(h, "2025-02-20", 12)["corrected_forecast_mw"]
    h.loc[(h["ref_date"] == "2025-02-20") & (h["ref_hour"] == 12), "actual_mw"] = 1e6
    assert corr_at(h, "2025-02-20", 12)["corrected_forecast_mw"] == pytest.approx(a)


def test_correction_null_when_published_forecast_missing():
    h = make_hourly(date(2025, 1, 1), date(2025, 3, 1))
    h.loc[(h["ref_date"] == "2025-02-20") & (h["ref_hour"] == 12), "forecast_mw"] = np.nan
    assert np.isnan(corr_at(h, "2025-02-20", 12)["corrected_forecast_mw"])
