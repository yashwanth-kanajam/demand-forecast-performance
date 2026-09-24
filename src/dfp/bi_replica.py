"""Replica of the docs/dax_measures.md measure logic, computed from the data/bi CSVs.

Purpose: prove, before the report is assembled, that the handoff files plus the DAX
filter logic reproduce the Python reference values (ba_metric_summary.csv). It is
NOT a Power BI result; docs/powerbi_reconciliation.md keeps a separate column for
values read from the built report.

Each function mirrors one DAX measure, evaluated in a single-BA filter context.
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

BI = Path(__file__).resolve().parents[2] / "data" / "bi"


def load_fact(path: Path = BI / "fact_hourly_performance.csv") -> pd.DataFrame:
    """Load as Power Query would with the documented types."""
    f = pd.read_csv(path, dtype={"ba_code": str, "high_demand": str, "high_forecast": str, "demand_band": str})
    f["utc_period_end"] = pd.to_datetime(f["utc_period_end"], format="%Y-%m-%dT%H:%M:%SZ")
    for col in ("is_dst", "is_paired", "in_common_set"):
        f[col] = f[col].astype(bool)
    return f


def _abs_err(t, col):
    return (t[col] - t["actual_mw"]).abs()


def measures(f: pd.DataFrame, dim_date: pd.DataFrame) -> dict:
    """All reconciled measures for one BA's rows (the BA filter context)."""
    p = f[f["is_paired"]]
    c = f[f["in_common_set"]]
    act_p, act_c = p["actual_mw"].sum(), c["actual_mw"].sum()

    def wape(t, col, denom):
        return _abs_err(t, col).sum() / denom

    out = {
        "paired_n_hours": len(p),
        "common_n_hours": len(c),
        "published_wape_pct_all_paired": 100 * wape(p, "forecast_mw", act_p),
        "published_mae_mw_all_paired": _abs_err(p, "forecast_mw").sum() / len(p),
        "published_norm_bias_pct_all_paired": 100 * (p["forecast_mw"] - p["actual_mw"]).sum() / act_p,
        "published_wape_pct_common": 100 * wape(c, "forecast_mw", act_c),
        "published_mae_mw_common": _abs_err(c, "forecast_mw").sum() / len(c),
        "published_norm_bias_pct_common": 100 * (c["forecast_mw"] - c["actual_mw"]).sum() / act_c,
        "naive_wape_pct_common": 100 * wape(c, "naive_forecast_mw", act_c),
        "naive_mae_mw_common": _abs_err(c, "naive_forecast_mw").sum() / len(c),
        "corrected_wape_pct_common": 100 * wape(c, "corrected_forecast_mw", act_c),
        "corrected_mae_mw_common": _abs_err(c, "corrected_forecast_mw").sum() / len(c),
        "corrected_norm_bias_pct_common": 100 * (c["corrected_forecast_mw"] - c["actual_mw"]).sum() / act_c,
    }
    out["corrected_vs_published_common_delta_pp"] = out["corrected_wape_pct_common"] - out["published_wape_pct_common"]
    out["corrected_vs_published_common_relative_delta_pct"] = 100 * (
        out["corrected_wape_pct_common"] / out["published_wape_pct_common"] - 1)
    hd = p[p["high_demand"] == "high"]
    out["peak_actual_defined_wape_pct_all_paired"] = 100 * wape(hd, "forecast_mw", hd["actual_mw"].sum())

    # Worst 1%: TOPN(k, paired rows, |error| DESC, utc_period_end ASC); k = ROUNDUP(0.01 * n, 0)
    ae = _abs_err(p, "forecast_mw")
    k = math.ceil(0.01 * len(p))
    top = pd.DataFrame({"ae": ae, "t": p["utc_period_end"]}).sort_values(["ae", "t"], ascending=[False, True]).head(k)
    out["worst1_contribution_pct_all_paired"] = 100 * top["ae"].sum() / ae.sum()

    # Quarters / years improved: iterate DimDate values, compare common-set WAPE per period.
    dd = dim_date.set_index("date")
    cc = c.assign(season_period=c["ref_date"].map(dd["season_period"]), eval_year=c["ref_date"].map(dd["eval_year"]))
    for col, key in (("season_period", "quarters_improved"), ("eval_year", "years_improved_of_3")):
        n = 0
        for _, g in cc.groupby(col):
            if wape(g, "corrected_forecast_mw", g["actual_mw"].sum()) < wape(g, "forecast_mw", g["actual_mw"].sum()):
                n += 1
        out[key] = n
    return out


def replicate(bi_dir: Path = BI) -> pd.DataFrame:
    f = load_fact(bi_dir / "fact_hourly_performance.csv")
    d = pd.read_csv(bi_dir / "dim_date.csv", dtype=str)
    return pd.DataFrame([{"ba_code": ba, **measures(g, d)} for ba, g in f.groupby("ba_code")]).set_index("ba_code")


RECONCILED = [
    "paired_n_hours", "common_n_hours",
    "published_wape_pct_all_paired", "published_mae_mw_all_paired", "published_norm_bias_pct_all_paired",
    "published_wape_pct_common", "published_mae_mw_common", "published_norm_bias_pct_common",
    "naive_wape_pct_common", "naive_mae_mw_common",
    "corrected_wape_pct_common", "corrected_mae_mw_common", "corrected_norm_bias_pct_common",
    "corrected_vs_published_common_delta_pp", "corrected_vs_published_common_relative_delta_pct",
    "peak_actual_defined_wape_pct_all_paired", "worst1_contribution_pct_all_paired",
    "quarters_improved", "years_improved_of_3",
]
