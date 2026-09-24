"""Forecast-error metrics. Sign convention: e = forecast - actual; positive = overforecast.

Definitions: docs/metric_catalogue.md.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from statistics import NormalDist

_N = NormalDist()


def gaussian_worst_share(share: float = 0.01) -> float:
    """Share of total |e| carried by the worst `share` of hours when e ~ Normal(0, s)."""
    c = _N.inv_cdf(1 - share / 2)
    return 2 * _N.pdf(c) / math.sqrt(2 / math.pi)


def summarize(actual: pd.Series, forecast: pd.Series) -> dict:
    """Sums and metrics for one group. Rows with either value missing are excluded."""
    ok = actual.notna() & forecast.notna()
    a, f = actual[ok].astype(float), forecast[ok].astype(float)
    e = f - a
    n = int(ok.sum())
    sa, sae, se = a.sum(), e.abs().sum(), e.sum()
    return {
        "n_hours": n,
        "sum_actual_mw_h": sa,
        "sum_abs_error_mw_h": sae,
        "sum_error_mw_h": se,
        **derived(n, sa, sae, se),
    }


def derived(n, sum_actual, sum_abs_error, sum_error) -> dict:
    """Metrics from additive sums, so segment results can be re-aggregated exactly."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return {
            "wape_pct": 100 * np.divide(sum_abs_error, sum_actual),
            "mae_mw": np.divide(sum_abs_error, n),
            "bias_mw": np.divide(sum_error, n),
            "norm_bias_pct": 100 * np.divide(sum_error, sum_actual),
        }


def aggregate(df: pd.DataFrame, keys: list[str], actual_col: str, forecast_col: str) -> pd.DataFrame:
    """Group-level sums and metrics over rows where both columns are present."""
    ok = df[actual_col].notna() & df[forecast_col].notna()
    d = df.loc[ok, keys].copy()
    d["a"] = df.loc[ok, actual_col].astype(float)
    d["e"] = df.loc[ok, forecast_col].astype(float) - d["a"]
    d["ae"] = d["e"].abs()
    g = d.groupby(keys, observed=True, sort=True).agg(
        n_hours=("a", "size"), sum_actual_mw_h=("a", "sum"),
        sum_abs_error_mw_h=("ae", "sum"), sum_error_mw_h=("e", "sum")).reset_index()
    m = derived(g["n_hours"], g["sum_actual_mw_h"], g["sum_abs_error_mw_h"], g["sum_error_mw_h"])
    for k, v in m.items():
        g[k] = v
    return g


def worst_share(abs_error: pd.Series, utc: pd.Series | None = None, share: float = 0.01) -> float:
    """Percent of total |e| contributed by the k = ceil(share * n) largest-|e| hours.

    Ties at the cutoff are broken by earlier UTC timestamp (deterministic).
    """
    x = abs_error.dropna()
    if x.empty or x.sum() == 0:
        return float("nan")
    k = math.ceil(share * len(x))
    order = pd.DataFrame({"ae": x, "t": utc.loc[x.index] if utc is not None else np.arange(len(x))})
    top = order.sort_values(["ae", "t"], ascending=[False, True]).head(k)
    return 100 * top["ae"].sum() / x.sum()

