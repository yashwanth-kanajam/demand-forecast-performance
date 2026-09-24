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


CATEGORY_LABELS = {
    "A": "A. Systematic and correctable",
    "B": "B. Apparently correctable \u2014 source semantics uncertain",
    "C": "C. Persistent bias \u2014 low correction benefit",
    "D": "D. Little/no correctable bias",
}
SOURCE_FLAG_TEXT = "SOURCE SEMANTICS UNCERTAIN"


def bias_shape(summary_row: pd.Series, hour_bias: pd.Series, exception_codes: set[str]) -> str:
    """Descriptive label for how directional error is distributed across reference hours.

    Rule (descriptive only, added after Phase 2.5 review; not used for categories):
    HOUR_SPECIFIC_BIAS fired and the range of hourly normalized bias >= 2 x |overall bias|
    -> 'hour-structured'; HOUR_SPECIFIC_BIAS fired otherwise -> 'level offset across hours';
    PERSISTENT_DIRECTIONAL_BIAS only -> 'uniform directional'; else 'near zero'.
    """
    overall = abs(summary_row["published_norm_bias_pct_all_paired"])
    spread = hour_bias.max() - hour_bias.min()
    if "HOUR_SPECIFIC_BIAS" in exception_codes:
        return "hour-structured" if spread >= 2 * overall else "level offset across hours"
    if "PERSISTENT_DIRECTIONAL_BIAS" in exception_codes:
        return "uniform directional"
    return "near zero"


def dim_ba(coverage: pd.DataFrame, h: pd.DataFrame, selected: list[str], summary: pd.DataFrame,
           seg: pd.DataFrame) -> pd.DataFrame:
    tz = h.groupby("ba_code")["reference_time_zone"].first()
    c = coverage[coverage["ba_code"].isin(selected)].set_index("ba_code")
    s = summary.set_index("ba_code")
    hours = seg[(seg["segment_type"] == "ref_hour") & (seg["eval_set"] == "paired")
                & (seg["forecast_type"] == "published")]
    rows = []
    for ba in sorted(selected):
        r = s.loc[ba]
        codes = set(str(r["exception_reasons"]).split("; ")) if isinstance(r["exception_reasons"], str) else set()
        hb = hours[hours["ba_code"] == ba]["norm_bias_pct"]
        rows.append({
            "ba_code": ba,
            "ba_name": c.loc[ba, "ba_name"],
            "region_name": c.loc[ba, "region_name"],
            "eia_time_zone_label": c.loc[ba, "eia_time_zone"],
            "reference_time_zone": tz[ba],
            "median_actual_mw": c.loc[ba, "median_actual_mw"],
            "paired_coverage_pct": c.loc[ba, "paired_coverage_pct"],
            "category_code": r["category"][0],
            "category_label": CATEGORY_LABELS[r["category"][0]],
            "source_semantic_flag": "true" if bool(r["source_semantic_flag"]) else "false",
            "source_semantics_display": SOURCE_FLAG_TEXT if bool(r["source_semantic_flag"]) else "",
            "project_rule_class": r["project_rule_class"],
            "peak_robustness": r["peak_robustness"],
            "bias_shape": bias_shape(r, hb, codes),
            "hourly_bias_min_pct": hb.min(),
            "hourly_bias_max_pct": hb.max(),
            "exception_reasons": r["exception_reasons"],
        })
    return pd.DataFrame(rows)


def write(out_dir: Path, h: pd.DataFrame, coverage: pd.DataFrame, selected: list[str],
          summary: pd.DataFrame, exceptions: pd.DataFrame, seg: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fact_table(h).to_csv(out_dir / "fact_hourly_performance.csv", index=False)
    dim_date(h).to_csv(out_dir / "dim_date.csv", index=False)
    dim_ba(coverage, h, selected, summary, seg).to_csv(out_dir / "dim_ba.csv", index=False)
    s = summary.copy()
    s["source_semantic_flag"] = _bool(s["source_semantic_flag"].astype(bool))
    s.to_csv(out_dir / "ba_metric_summary.csv", index=False)
    exceptions.to_csv(out_dir / "exception_candidates.csv", index=False)
