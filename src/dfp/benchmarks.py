"""Benchmarks compared with the published forecast. Definitions: docs/metric_catalogue.md.

Every function takes the curated hourly table (one row per BA x UTC hour, with
ref_* reference-time fields and usable actual_mw / forecast_mw) and uses only
information dated before the target hour.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def seasonal_naive(hourly: pd.DataFrame, lag_days: int = 7) -> pd.DataFrame:
    """Actual demand at the same BA reference-clock time `lag_days` calendar days earlier.

    Returns naive_forecast_mw, naive_source_utc_period_end and naive_status
    ('ok', 'before_window', 'hour_absent', 'actual_missing'), aligned to `hourly`.
    Fall-back duplicate wall-clock hours resolve to the first (earlier-UTC) instance.
    """
    out = pd.DataFrame(index=hourly.index, columns=["naive_forecast_mw", "naive_source_utc_period_end", "naive_status"])
    lag = pd.Timedelta(days=lag_days)
    for ba, rows in hourly.groupby("ba_code", sort=False):
        lookup = (rows.sort_values("utc_period_end")
                  .drop_duplicates("ref_period_start", keep="first")
                  .set_index("ref_period_start")[["actual_mw", "utc_period_end"]])
        key = rows["ref_period_start"] - lag
        found = key.isin(lookup.index)
        src = lookup.reindex(key.values)
        status = np.where(key < rows["ref_period_start"].min(), "before_window",
                 np.where(~found, "hour_absent",
                 np.where(src["actual_mw"].isna().values, "actual_missing", "ok")))
        out.loc[rows.index, "naive_forecast_mw"] = src["actual_mw"].values
        out.loc[rows.index, "naive_source_utc_period_end"] = src["utc_period_end"].values
        out.loc[rows.index, "naive_status"] = status
    out["naive_forecast_mw"] = out["naive_forecast_mw"].astype(float)
    out["naive_source_utc_period_end"] = pd.to_datetime(out["naive_source_utc_period_end"], utc=True)
    return out


def naive_utc_lag(hourly: pd.DataFrame, lag_hours: int = 168) -> pd.Series:
    """Sensitivity only: actual demand exactly `lag_hours` UTC hours earlier."""
    shifted = hourly[["ba_code", "utc_period_end", "actual_mw"]].copy()
    shifted["utc_period_end"] = shifted["utc_period_end"] + pd.Timedelta(hours=lag_hours)
    merged = hourly[["ba_code", "utc_period_end"]].merge(shifted, on=["ba_code", "utc_period_end"], how="left")
    return pd.Series(merged["actual_mw"].values, index=hourly.index, name=f"naive_{lag_hours}h_mw")


def trailing_bias_correction(hourly: pd.DataFrame, window_days: int = 28, gap_days: int = 2,
                             min_days: int = 14) -> pd.DataFrame:
    """Causal residual adjustment by BA x ref_hour over reference dates [D-gap-window+1, D-gap].

    Residual r = actual - published forecast. For a target on reference date D,
    adjustment_mw = mean(r) over paired hours with the same BA and ref_hour on
    dates D-29 .. D-2 (defaults), and corrected_forecast_mw = forecast + adjustment_mw.
    Null when fewer than `min_days` days carry residuals or the published forecast is
    missing; never filled with the published forecast.
    """
    paired = hourly[hourly["actual_mw"].notna() & hourly["forecast_mw"].notna()]
    resid = (paired["actual_mw"] - paired["forecast_mw"]).rename("r")
    daily = (pd.concat([paired[["ba_code", "ref_date", "ref_hour"]], resid], axis=1)
             .groupby(["ba_code", "ref_hour", "ref_date"])["r"].agg(["sum", "count"]))
    frames = []
    for ba, rows in hourly.groupby("ba_code", sort=False):
        dates = pd.date_range(rows["ref_date"].min(), rows["ref_date"].max(), freq="D")
        d = daily.xs(ba, level="ba_code") if ba in daily.index.get_level_values(0) else daily.iloc[0:0].droplevel(0)
        s = d["sum"].unstack("ref_hour").reindex(index=dates, columns=range(24)).fillna(0.0)
        n = d["count"].unstack("ref_hour").reindex(index=dates, columns=range(24)).fillna(0)
        # Explicit shift: the window ending on D-gap is attached to target date D.
        roll_s = s.rolling(window_days, min_periods=1).sum().shift(gap_days)
        roll_n = n.rolling(window_days, min_periods=1).sum().shift(gap_days)
        roll_d = (n > 0).astype(int).rolling(window_days, min_periods=1).sum().shift(gap_days)
        adj = (roll_s / roll_n.replace(0, np.nan)).where(roll_d >= min_days)
        frames.append(pd.DataFrame({
            "ba_code": ba,
            "ref_date": np.repeat(dates.values, 24),
            "ref_hour": np.tile(np.arange(24), len(dates)),
            "adjustment_mw": adj.values.ravel(),
            "adjustment_days": roll_d.fillna(0).astype(int).values.ravel(),
        }))
    table = pd.concat(frames, ignore_index=True)
    merged = hourly[["ba_code", "ref_date", "ref_hour", "forecast_mw"]].merge(
        table, on=["ba_code", "ref_date", "ref_hour"], how="left")
    merged.index = hourly.index
    merged["corrected_forecast_mw"] = merged["forecast_mw"] + merged["adjustment_mw"]
    return merged[["adjustment_mw", "adjustment_days", "corrected_forecast_mw"]]
