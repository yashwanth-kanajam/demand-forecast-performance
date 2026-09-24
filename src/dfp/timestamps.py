"""Timestamp rules.

The canonical fact key is (ba_code, utc_period_end). EIA-930 timestamps are
hour-ending: the row stamped 14:00 UTC covers 13:00-14:00 UTC. Local
attributes are derived from the UTC interval start converted to the BA's
reference zone, never parsed from the source's local-time string (that
string repeats during the fall-back hour).
"""
from __future__ import annotations

from datetime import date

import pandas as pd

EIA_TS_FORMAT = "%m/%d/%Y %I:%M:%S %p"
ONE_HOUR = pd.Timedelta(hours=1)


def parse_eia_timestamp(values: pd.Series) -> pd.Series:
    """Parse EIA 'MM/DD/YYYY h:mm:ss AM' strings. Raises on any unparseable value."""
    return pd.to_datetime(values, format=EIA_TS_FORMAT, errors="raise")


def window_bounds_utc(start_local: date, end_local: date, tz: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """UTC instants of local midnight at start and end (end exclusive)."""
    start = pd.Timestamp(start_local).tz_localize(tz).tz_convert("UTC")
    end = pd.Timestamp(end_local).tz_localize(tz).tz_convert("UTC")
    return start, end


def expected_period_ends(start_local: date, end_local: date, tz: str) -> pd.DatetimeIndex:
    """Every hour-ending UTC timestamp whose interval falls inside the local window.

    Counted on the UTC sequence, so a spring-forward day contributes 23 hours and
    a fall-back day 25; never days * 24.
    """
    start, end = window_bounds_utc(start_local, end_local, tz)
    return pd.date_range(start + ONE_HOUR, end, freq="h", tz="UTC")


def derive_local_attributes(utc_period_end: pd.Series, tz: str) -> pd.DataFrame:
    """Local calendar attributes for hour-ending UTC timestamps in one zone.

    local_hour is hour-beginning (0-23): local_hour 17 is 17:00-18:00 local.
    On a fall-back day local_hour 1 occurs twice; the two rows differ in
    utc_offset_hours and is_dst, and remain unique on the UTC key.
    """
    utc_end = pd.DatetimeIndex(utc_period_end)
    if utc_end.tz is None:
        raise ValueError("utc_period_end must be timezone-aware UTC")
    utc_start = utc_end - ONE_HOUR
    local_start = utc_start.tz_convert(tz)
    local_end = utc_end.tz_convert(tz)
    offsets = (local_start.tz_localize(None) - utc_start.tz_localize(None)) / pd.Timedelta(hours=1)
    # US zones: the standard (non-DST) offset is the January offset.
    standard = (pd.Timestamp("2000-01-15", tz=tz).utcoffset() / pd.Timedelta(hours=1))
    dst = offsets > standard
    return pd.DataFrame(
        {
            "utc_period_start": utc_start,
            "local_period_start": local_start.tz_localize(None),
            "local_period_end": local_end.tz_localize(None),
            "local_date": local_start.tz_localize(None).normalize(),
            "local_hour": local_start.hour,
            "utc_offset_hours": offsets,
            "is_dst": dst,
        },
        index=utc_period_end.index if isinstance(utc_period_end, pd.Series) else None,
    )
