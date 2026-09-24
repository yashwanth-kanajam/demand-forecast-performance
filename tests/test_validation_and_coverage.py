from dataclasses import replace
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from dfp.config import load_config
from dfp.curate import build_hourly, coverage_table
from dfp.source import read_balance_files
from dfp.validate import (
    ValidationError,
    assert_curated_contract,
    classify_actual,
    classify_forecast,
    resolve_duplicates,
)

HEADER = ('"Balancing Authority","Data Date","Hour Number","Local Time at End of Hour",'
          '"UTC Time at End of Hour","Demand Forecast (MW)","Demand (MW)","Demand (MW) (Imputed)"')


def one_day_cfg(tmp_path: Path, day=date(2025, 7, 1)):
    cfg = load_config()
    return replace(cfg, raw_dir=tmp_path, start_local_date=day,
                   end_local_date=date.fromordinal(day.toordinal() + 1))


def synthetic_raw(hours=24, drop=(), forecast_missing=(), actual_missing=(), eia_replaced=()):
    """One Central-time BA day (2025-07-01 CDT = UTC-5), hour-ending rows."""
    utc_end = pd.date_range("2025-07-01 06:00", periods=hours, freq="h")
    rows = pd.DataFrame({
        "ba_code": "TST",
        "eia_data_date": "07/01/2025",
        "eia_hour_number": [str(i + 1) for i in range(hours)],
        "eia_local_end": (utc_end - pd.Timedelta(hours=5)).strftime("%m/%d/%Y %I:%M:%S %p"),
        "eia_utc_end": utc_end.strftime("%m/%d/%Y %I:%M:%S %p"),
        "forecast_mw_reported": 1000.0,
        "actual_mw_reported": 1010.0,
        "actual_mw_eia_imputed": np.nan,
        "source_file": "synthetic",
    })
    rows.loc[list(forecast_missing), "forecast_mw_reported"] = np.nan
    rows.loc[list(actual_missing), "actual_mw_reported"] = np.nan
    rows.loc[list(eia_replaced), "actual_mw_eia_imputed"] = 1005.0
    return rows.drop(index=list(drop)).reset_index(drop=True)


CANDIDATES = pd.DataFrame({"ba_code": ["TST"], "ba_name": ["Test BA"], "eia_time_zone": ["Central"],
                           "region_name": ["Test"]})


# --- duplicates / uniqueness -------------------------------------------------

def test_exact_duplicate_rows_are_dropped_and_counted():
    df = pd.DataFrame({"ba_code": ["A", "A", "A"], "t": [1, 1, 2], "v": [5.0, 5.0, 6.0]})
    out, audit = resolve_duplicates(df, ["ba_code", "t"], ["v"])
    assert len(out) == 2 and audit == {"duplicate_rows": 2, "rows_dropped": 1, "conflicting_keys": 0}


def test_conflicting_duplicate_ba_utc_raises():
    df = pd.DataFrame({"ba_code": ["A", "A"], "t": [1, 1], "v": [5.0, 7.0]})
    with pytest.raises(ValidationError, match="conflicting"):
        resolve_duplicates(df, ["ba_code", "t"], ["v"])


def test_build_hourly_rejects_conflicting_duplicate_source_rows(tmp_path):
    raw = synthetic_raw()
    dup = raw.iloc[[3]].assign(actual_mw_reported=999.0)
    with pytest.raises(ValidationError):
        build_hourly(pd.concat([raw, dup], ignore_index=True), CANDIDATES, one_day_cfg(tmp_path))


def test_curated_contract_rejects_duplicate_utc_key(tmp_path):
    hourly, _ = build_hourly(synthetic_raw(), CANDIDATES, one_day_cfg(tmp_path))
    with pytest.raises(ValidationError, match="not unique"):
        assert_curated_contract(pd.concat([hourly, hourly.iloc[[0]]], ignore_index=True))


# --- type / range ------------------------------------------------------------

def test_actual_classification_never_uses_eia_imputed_values():
    reported = pd.Series([100.0, np.nan, 11359.0, 0.0, -5.0])
    imputed = pd.Series([np.nan, 900.0, 1466.0, np.nan, np.nan])
    assert classify_actual(reported, imputed).tolist() == [
        "valid", "missing", "eia_replaced", "nonpositive", "nonpositive"]


def test_forecast_classification():
    assert classify_forecast(pd.Series([100.0, np.nan, 0.0])).tolist() == ["valid", "missing", "nonpositive"]


def test_non_numeric_source_value_fails_loudly(tmp_path):
    cfg = replace(load_config(), raw_dir=tmp_path, start_local_date=date(2025, 7, 1),
                  end_local_date=date(2025, 7, 2))
    (tmp_path / "EIA930_BALANCE_2025_Jul_Dec.csv").write_text(
        HEADER + '\n"TST","07/01/2025","1","07/01/2025 1:00:00 AM","07/01/2025 6:00:00 AM","1,000","n/a",""\n')
    with pytest.raises(ValueError):
        read_balance_files(cfg)


def test_thousands_separators_are_parsed(tmp_path):
    cfg = replace(load_config(), raw_dir=tmp_path, start_local_date=date(2025, 7, 1),
                  end_local_date=date(2025, 7, 2))
    (tmp_path / "EIA930_BALANCE_2025_Jul_Dec.csv").write_text(
        HEADER + '\n"TST","07/01/2025","1","07/01/2025 1:00:00 AM","07/01/2025 6:00:00 AM","1,000","1,010",""\n')
    raw = read_balance_files(cfg)
    assert raw.loc[0, "forecast_mw_reported"] == 1000 and raw.loc[0, "actual_mw_reported"] == 1010


# --- coverage and pairing ----------------------------------------------------

def test_missing_source_rows_become_explicit_unpaired_hours(tmp_path):
    hourly, audit = build_hourly(synthetic_raw(drop=[5, 6]), CANDIDATES, one_day_cfg(tmp_path))
    assert len(hourly) == 24
    assert (~hourly["source_row_present"]).sum() == 2
    assert audit["rows_in_window_from_source"] == 22


def test_paired_requires_both_usable_values(tmp_path):
    raw = synthetic_raw(forecast_missing=[1], actual_missing=[2], eia_replaced=[3])
    hourly, _ = build_hourly(raw, CANDIDATES, one_day_cfg(tmp_path))
    assert hourly["is_paired"].tolist() == [True, False, False, False] + [True] * 20
    assert hourly.loc[3, "actual_status"] == "eia_replaced" and np.isnan(hourly.loc[3, "actual_mw"])


def test_coverage_counts_against_expected_utc_hours(tmp_path):
    cfg = one_day_cfg(tmp_path)
    raw = synthetic_raw(drop=[0], forecast_missing=[1, 2], actual_missing=[2, 3])
    hourly, _ = build_hourly(raw, CANDIDATES, cfg)
    cov = coverage_table(hourly, CANDIDATES, cfg).iloc[0]
    assert cov["expected_hours"] == 24
    assert cov["actual_hours"] == 21     # missing: row 0 absent, rows 2 and 3
    assert cov["forecast_hours"] == 21   # missing: row 0 absent, rows 1 and 2
    assert cov["paired_hours"] == 20     # missing: rows 0, 1, 2, 3
    assert cov["paired_coverage_pct"] == round(100 * 20 / 24, 2)
    assert not cov["passes_gate"]


def test_gate_requires_all_three_thresholds(tmp_path):
    cfg = one_day_cfg(tmp_path)
    full = coverage_table(build_hourly(synthetic_raw(), CANDIDATES, cfg)[0], CANDIDATES, cfg).iloc[0]
    assert full["passes_gate"]
    one_forecast_gap = synthetic_raw(forecast_missing=[4, 5])  # 22/24 = 91.7% forecast
    cov = coverage_table(build_hourly(one_forecast_gap, CANDIDATES, cfg)[0], CANDIDATES, cfg).iloc[0]
    assert cov["actual_coverage_pct"] == 100 and not cov["passes_gate"]


def test_rows_outside_window_are_excluded(tmp_path):
    raw = synthetic_raw(hours=30)  # 6 hours spill into 2025-07-02 local
    hourly, _ = build_hourly(raw, CANDIDATES, one_day_cfg(tmp_path))
    assert len(hourly) == 24 and hourly["local_date"].nunique() == 1
