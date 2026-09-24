from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from dfp.config import load_config
from dfp.source import SOURCE_COLUMNS
from dfp.timestamps import derive_reference_attributes, expected_period_ends, parse_eia_timestamp
from dfp.validate import check_reference_time_consistency

FIXTURE = Path(__file__).parent / "fixtures" / "eia930_dst_days.csv"
NY, CHI, PHX, EST = "America/New_York", "America/Chicago", "America/Phoenix", "Etc/GMT+5"


def day_hours(day: date, tz: str) -> pd.DataFrame:
    ends = expected_period_ends(day, date.fromordinal(day.toordinal() + 1), tz)
    return derive_reference_attributes(pd.Series(ends), tz)


def test_spring_forward_day_has_23_hours_and_skips_local_2am():
    local = day_hours(date(2025, 3, 9), NY)
    assert len(local) == 23
    assert 2 not in set(local["ref_hour"])
    assert local["utc_offset_hours"].iloc[0] == -5 and local["utc_offset_hours"].iloc[-1] == -4
    assert not local["is_dst"].iloc[0] and local["is_dst"].iloc[-1]


def test_fall_back_day_has_25_hours_with_repeated_local_1am_unique_in_utc():
    local = day_hours(date(2024, 11, 3), NY)
    assert len(local) == 25
    one_am = local[local["ref_hour"] == 1]
    assert len(one_am) == 2
    assert sorted(one_am["utc_offset_hours"]) == [-5, -4]
    assert one_am["is_dst"].tolist() == [True, False]
    assert local["utc_period_start"].is_unique


@pytest.mark.parametrize("tz", [PHX, EST])
def test_fixed_offset_zones_have_24_hours_on_us_transition_days(tz):
    for day in (date(2025, 3, 9), date(2024, 11, 3)):
        local = day_hours(day, tz)
        assert len(local) == 24 and not local["is_dst"].any()


def test_expected_hours_count_utc_sequence_not_days_times_24():
    cfg = load_config()
    assert len(expected_period_ends(cfg.start_ref_date, cfg.end_ref_date, NY)) == 1096 * 24
    # A window spanning only the spring-forward transition loses one hour.
    assert len(expected_period_ends(date(2025, 3, 1), date(2025, 4, 1), NY)) == 31 * 24 - 1
    assert len(expected_period_ends(date(2025, 3, 1), date(2025, 4, 1), PHX)) == 31 * 24


def test_hour_ending_convention_maps_to_local_hour_beginning():
    utc_end = pd.Series(pd.to_datetime(["2025-07-01 22:00"]).tz_localize("UTC"))
    local = derive_reference_attributes(utc_end, NY)
    # 21:00-22:00 UTC is 17:00-18:00 EDT.
    assert local["ref_hour"].iloc[0] == 17
    assert local["ref_date"].iloc[0] == pd.Timestamp("2025-07-01")


def test_naive_timestamps_rejected():
    with pytest.raises(ValueError):
        derive_reference_attributes(pd.Series(pd.to_datetime(["2025-07-01 22:00"])), NY)


@pytest.mark.parametrize("ba,tz", [("PJM", NY), ("AECI", CHI), ("PNM", PHX), ("MISO", EST)])
def test_reference_zone_reproduces_eia_local_time_on_real_dst_rows(ba, tz):
    raw = pd.read_csv(FIXTURE, dtype=str).rename(columns=SOURCE_COLUMNS)
    rows = raw[raw["ba_code"] == ba].reset_index(drop=True)
    utc_end = parse_eia_timestamp(rows["eia_utc_end"]).dt.tz_localize("UTC")
    assert utc_end.is_unique
    local = derive_reference_attributes(utc_end, tz)
    check = check_reference_time_consistency(pd.concat([rows[["ba_code", "eia_local_end", "eia_data_date"]], local], axis=1))
    assert check[["ref_end_mismatch", "ref_date_mismatch"]].sum().sum() == 0


def test_wrong_zone_is_detected_on_real_rows():
    raw = pd.read_csv(FIXTURE, dtype=str).rename(columns=SOURCE_COLUMNS)
    rows = raw[raw["ba_code"] == "MISO"].reset_index(drop=True)
    utc_end = parse_eia_timestamp(rows["eia_utc_end"]).dt.tz_localize("UTC")
    local = derive_reference_attributes(utc_end, NY)  # MISO's reference-table label, which is wrong
    check = check_reference_time_consistency(pd.concat([rows[["ba_code", "eia_local_end", "eia_data_date"]], local], axis=1))
    assert check["ref_end_mismatch"].sum() > 0
