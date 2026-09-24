"""Build the curated hourly table and the per-BA coverage/quality tables."""
from __future__ import annotations

import pandas as pd

from .config import Config
from .timestamps import derive_reference_attributes, expected_period_ends
from .validate import (
    assert_curated_contract,
    check_reference_time_consistency,
    classify_actual,
    classify_forecast,
    range_profile,
    resolve_duplicates,
)

CURATED_COLUMNS = [
    "ba_code", "utc_period_end", "utc_period_start", "ref_period_start", "ref_date",
    "ref_hour", "utc_offset_hours", "is_dst", "reference_time_zone",
    "source_row_present", "actual_mw", "actual_status", "forecast_mw", "forecast_status",
    "is_paired", "actual_mw_reported", "forecast_mw_reported", "source_file",
]


def candidate_bas(raw: pd.DataFrame, ref: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """U.S., demand-serving BAs present in the source. Returns (candidates, excluded)."""
    present = pd.DataFrame({"ba_code": sorted(raw["ba_code"].unique())})
    merged = present.merge(ref, on="ba_code", how="left")
    reason = pd.Series(pd.NA, index=merged.index, dtype=object)
    reason[merged["ba_name"].isna()] = "not in EIA reference table"
    reason[reason.isna() & (merged["us_ba"] != "Yes")] = "non-U.S. BA"
    reason[reason.isna() & (merged["generation_only"] == "Yes")] = "generation-only BA (no demand)"
    merged["exclusion_reason"] = reason
    return merged[reason.isna()].drop(columns="exclusion_reason"), merged[reason.notna()]


def build_hourly(raw: pd.DataFrame, candidates: pd.DataFrame, cfg: Config) -> tuple[pd.DataFrame, dict]:
    """Return one row per candidate BA per expected UTC hour, plus audit counts."""
    audit: dict = {"raw_rows_all_bas": int(len(raw))}
    df = raw[raw["ba_code"].isin(candidates["ba_code"])].copy()
    audit["raw_rows_candidate_bas"] = int(len(df))
    df["utc_period_end"] = pd.to_datetime(df["eia_utc_end"], format="%m/%d/%Y %I:%M:%S %p").dt.tz_localize("UTC")

    df, audit["duplicates"] = resolve_duplicates(
        df, ["ba_code", "utc_period_end"],
        ["forecast_mw_reported", "actual_mw_reported", "actual_mw_eia_imputed"],
    )

    zones = candidates.set_index("ba_code")["eia_time_zone"].map(cfg.timezones)
    for ba, tz in cfg.timezone_overrides.items():
        if ba in zones.index:
            zones[ba] = tz
    if zones.isna().any():
        raise ValueError(f"No IANA zone mapping for: {zones[zones.isna()].index.tolist()}")

    frames, tz_checks = [], []
    for ba, tz in zones.items():
        rows = df[df["ba_code"] == ba]
        # Zone check runs on every source row for the BA, inside and outside the window.
        local = derive_reference_attributes(rows["utc_period_end"], tz)
        tz_checks.append(check_reference_time_consistency(pd.concat([rows[["ba_code", "eia_local_end", "eia_data_date"]], local], axis=1)))

        grid = pd.DataFrame({"utc_period_end": expected_period_ends(cfg.start_ref_date, cfg.end_ref_date, tz)})
        grid = grid.merge(rows, on="utc_period_end", how="left", indicator=True)
        grid["source_row_present"] = grid.pop("_merge") == "both"
        grid["ba_code"] = ba
        grid["reference_time_zone"] = tz
        grid = pd.concat([grid, derive_reference_attributes(grid["utc_period_end"], tz)], axis=1)
        frames.append(grid)

    hourly = pd.concat(frames, ignore_index=True)
    hourly["actual_status"] = classify_actual(hourly["actual_mw_reported"], hourly["actual_mw_eia_imputed"])
    hourly["forecast_status"] = classify_forecast(hourly["forecast_mw_reported"])
    hourly["actual_mw"] = hourly["actual_mw_reported"].where(hourly["actual_status"] == "valid")
    hourly["forecast_mw"] = hourly["forecast_mw_reported"].where(hourly["forecast_status"] == "valid")
    hourly["is_paired"] = hourly["actual_mw"].notna() & hourly["forecast_mw"].notna()
    hourly = hourly[CURATED_COLUMNS].sort_values(["ba_code", "utc_period_end"], ignore_index=True)
    assert_curated_contract(hourly)

    audit["rows_in_window_from_source"] = int(hourly["source_row_present"].sum())
    audit["timezone_check"] = pd.concat(tz_checks, ignore_index=True)
    return hourly, audit


def coverage_table(hourly: pd.DataFrame, candidates: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    g = hourly.groupby("ba_code")
    cov = pd.DataFrame({
        "expected_hours": g.size(),
        "source_rows": g["source_row_present"].sum(),
        "actual_reported_hours": g["actual_mw_reported"].count(),
        "actual_eia_replaced_hours": g["actual_status"].apply(lambda s: (s == "eia_replaced").sum()),
        "actual_nonpositive_hours": g["actual_status"].apply(lambda s: (s == "nonpositive").sum()),
        "actual_hours": g["actual_mw"].count(),
        "forecast_nonpositive_hours": g["forecast_status"].apply(lambda s: (s == "nonpositive").sum()),
        "forecast_hours": g["forecast_mw"].count(),
        "paired_hours": g["is_paired"].sum(),
    }).reset_index()
    for name in ("actual", "forecast", "paired"):
        cov[f"{name}_coverage_pct"] = (100 * cov[f"{name}_hours"] / cov["expected_hours"]).round(2)
    cov["passes_gate"] = (
        (cov["actual_hours"] / cov["expected_hours"] >= cfg.min_actual_coverage)
        & (cov["forecast_hours"] / cov["expected_hours"] >= cfg.min_forecast_coverage)
        & (cov["paired_hours"] / cov["expected_hours"] >= cfg.min_paired_coverage)
    )
    monthly = monthly_coverage(hourly)
    stab = monthly.groupby("ba_code").agg(
        min_monthly_paired_pct=("paired_coverage_pct", "min"),
        months_below_95_paired=("paired_coverage_pct", lambda s: int((s < 95).sum())),
        months=("paired_coverage_pct", "size"),
    ).reset_index()
    cov = cov.merge(stab, on="ba_code").merge(range_profile(hourly), on="ba_code")
    meta = candidates[["ba_code", "ba_name", "eia_time_zone", "region_name"]]
    cov = meta.merge(cov, on="ba_code")
    peak = hourly.groupby("ba_code")["actual_mw"].median().rename("median_actual_mw").round(0).reset_index()
    return cov.merge(peak, on="ba_code").sort_values("ba_code", ignore_index=True)


def monthly_coverage(hourly: pd.DataFrame) -> pd.DataFrame:
    h = hourly.assign(ref_month=hourly["ref_date"].dt.to_period("M").astype(str))
    g = h.groupby(["ba_code", "ref_month"])
    out = pd.DataFrame({
        "expected_hours": g.size(),
        "actual_hours": g["actual_mw"].count(),
        "forecast_hours": g["forecast_mw"].count(),
        "paired_hours": g["is_paired"].sum(),
    }).reset_index()
    out["paired_coverage_pct"] = (100 * out["paired_hours"] / out["expected_hours"]).round(2)
    return out
