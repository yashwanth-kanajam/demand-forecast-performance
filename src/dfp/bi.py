"""Power BI handoff: explicit-schema CSVs with ISO dates. Schema: docs/bi_handoff.md."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

FACT_COLUMNS = [
    "ba_code", "utc_period_end", "utc_period_start", "ref_period_start", "ref_date", "ref_hour",
    "utc_offset_hours", "is_dst", "actual_mw", "forecast_mw", "naive_forecast_mw", "corrected_forecast_mw",
    "adjustment_mw", "is_paired", "in_common_set", "high_demand", "high_forecast", "demand_band",
]


def _iso_utc(s: pd.Series) -> pd.Series:
    return s.dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _bool(s: pd.Series) -> pd.Series:
    return s.map({True: "true", False: "false"})


def fact_table(h: pd.DataFrame) -> pd.DataFrame:
    f = h[FACT_COLUMNS].copy()
    f["utc_period_end"] = _iso_utc(f["utc_period_end"])
    f["utc_period_start"] = _iso_utc(f["utc_period_start"])
    f["ref_period_start"] = f["ref_period_start"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    f["ref_date"] = f["ref_date"].dt.strftime("%Y-%m-%d")
    for col in ("is_dst", "is_paired", "in_common_set"):
        f[col] = _bool(f[col].astype(bool))
    return f


def dim_date(h: pd.DataFrame) -> pd.DataFrame:
    """One row per reference date, with the calendar segments used in the analysis."""
    d = (h[["ref_date", "eval_year", "season", "season_period", "day_type"]]
         .drop_duplicates("ref_date").sort_values("ref_date"))
    return pd.DataFrame({
        "date": d["ref_date"].dt.strftime("%Y-%m-%d"),
        "year": d["ref_date"].dt.year,
        "month": d["ref_date"].dt.month,
        "month_name": d["ref_date"].dt.strftime("%b"),
        "year_month": d["ref_date"].dt.strftime("%Y-%m"),
        "day_of_week": d["ref_date"].dt.dayofweek + 1,
        "day_name": d["ref_date"].dt.strftime("%a"),
        "day_type": d["day_type"],
        "season": d["season"],
        "season_period": d["season_period"],
        "eval_year": d["eval_year"],
    })


def dim_ba(coverage: pd.DataFrame, h: pd.DataFrame, selected: list[str]) -> pd.DataFrame:
    tz = h.groupby("ba_code")["reference_time_zone"].first()
    c = coverage[coverage["ba_code"].isin(selected)]
    return pd.DataFrame({
        "ba_code": c["ba_code"],
        "ba_name": c["ba_name"],
        "region_name": c["region_name"],
        "eia_time_zone_label": c["eia_time_zone"],
        "reference_time_zone": c["ba_code"].map(tz),
        "median_actual_mw": c["median_actual_mw"],
        "paired_coverage_pct": c["paired_coverage_pct"],
    }).sort_values("ba_code", ignore_index=True)


def write(out_dir: Path, h: pd.DataFrame, coverage: pd.DataFrame, selected: list[str],
          summary: pd.DataFrame, exceptions: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fact_table(h).to_csv(out_dir / "fact_hourly_performance.csv", index=False)
    dim_date(h).to_csv(out_dir / "dim_date.csv", index=False)
    dim_ba(coverage, h, selected).to_csv(out_dir / "dim_ba.csv", index=False)
    summary.to_csv(out_dir / "ba_metric_summary.csv", index=False)
    exceptions.to_csv(out_dir / "exception_candidates.csv", index=False)
