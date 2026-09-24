"""Validation checks and value rules applied to raw EIA-930 rows.

Value rules (documented in docs/data_contract.md):
- actual: the BA-reported 'Demand (MW)'. EIA's imputed value is never used.
  If EIA supplied an imputed replacement for a reported value, EIA's own
  anomaly screening rejected that value, so it is treated as not usable.
- forecast: the BA-reported 'Demand Forecast (MW)'. Never imputed.
- Non-positive values are not usable for either series.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .timestamps import parse_eia_timestamp


class ValidationError(Exception):
    pass


def classify_actual(reported: pd.Series, eia_imputed: pd.Series) -> pd.Series:
    status = pd.Series("valid", index=reported.index, dtype=object)
    status[reported.notna() & (reported <= 0)] = "nonpositive"
    status[reported.notna() & eia_imputed.notna()] = "eia_replaced"
    status[reported.isna()] = "missing"
    return status


def classify_forecast(reported: pd.Series) -> pd.Series:
    status = pd.Series("valid", index=reported.index, dtype=object)
    status[reported.notna() & (reported <= 0)] = "nonpositive"
    status[reported.isna()] = "missing"
    return status


def resolve_duplicates(df: pd.DataFrame, key: list[str], value_cols: list[str]) -> tuple[pd.DataFrame, dict]:
    """Drop exact duplicate keys; raise if any duplicated key carries conflicting values."""
    dup_mask = df.duplicated(key, keep=False)
    dups = df[dup_mask]
    conflicting = 0
    if not dups.empty:
        distinct = dups.drop_duplicates(key + value_cols)
        conflicting_keys = distinct[distinct.duplicated(key, keep=False)][key].drop_duplicates()
        conflicting = len(conflicting_keys)
        if conflicting:
            raise ValidationError(
                f"{conflicting} {key} keys have conflicting values, e.g. "
                f"{conflicting_keys.head(3).to_dict('records')}"
            )
    out = df.drop_duplicates(key, keep="first")
    return out, {"duplicate_rows": int(dup_mask.sum()), "rows_dropped": int(len(df) - len(out)),
                 "conflicting_keys": conflicting}


def check_local_time_consistency(df: pd.DataFrame) -> pd.DataFrame:
    """Compare derived local attributes with EIA's own local columns, per BA.

    Expects columns eia_local_end, eia_data_date, local_period_end, local_date.
    A mismatch means the assigned reference zone does not reproduce EIA's local
    time for that row.
    """
    eia_local = parse_eia_timestamp(df["eia_local_end"])
    eia_date = pd.to_datetime(df["eia_data_date"], format="%m/%d/%Y")
    res = pd.DataFrame({
        "ba_code": df["ba_code"],
        "local_end_mismatch": (eia_local.values != df["local_period_end"].values),
        "local_date_mismatch": (eia_date.values != df["local_date"].values),
    })
    return res.groupby("ba_code").sum().astype(int).reset_index()


def range_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Informational: hours where the usable forecast is < 0.5x or > 2x the usable actual.

    Not an exclusion rule. Reported so implausible values are visible before
    any metric is computed.
    """
    ratio = df["forecast_mw"] / df["actual_mw"]
    suspect = ratio.notna() & ((ratio < 0.5) | (ratio > 2.0))
    return (pd.DataFrame({"ba_code": df["ba_code"], "suspect_ratio_hours": suspect})
            .groupby("ba_code").sum().astype(int).reset_index())


def assert_unique_utc(df: pd.DataFrame) -> None:
    if df.duplicated(["ba_code", "utc_period_end"]).any():
        raise ValidationError("ba_code + utc_period_end is not unique")


def assert_curated_contract(df: pd.DataFrame) -> None:
    """Invariants the curated hourly table must satisfy."""
    assert_unique_utc(df)
    if str(df["utc_period_end"].dt.tz) != "UTC":
        raise ValidationError("utc_period_end must be UTC-aware")
    for col, status_col in (("actual_mw", "actual_status"), ("forecast_mw", "forecast_status")):
        valid = df[status_col] == "valid"
        if df.loc[valid, col].isna().any() or df.loc[~valid, col].notna().any():
            raise ValidationError(f"{col} must be populated exactly when {status_col} == 'valid'")
        if (df.loc[valid, col] <= 0).any():
            raise ValidationError(f"{col} contains non-positive usable values")
    expected_pair = df["actual_mw"].notna() & df["forecast_mw"].notna()
    if not np.array_equal(df["is_paired"].values, expected_pair.values):
        raise ValidationError("is_paired must equal (actual usable AND forecast usable)")
