"""Checks on the generated curated table. Skipped until the pipeline has run."""
from pathlib import Path

import pandas as pd
import pytest

from dfp.config import load_config
from dfp.validate import assert_curated_contract

CURATED = Path(__file__).resolve().parents[1] / "data" / "curated" / "fact_hourly_performance.parquet"
pytestmark = pytest.mark.skipif(not CURATED.exists(), reason="run `python -m dfp.pipeline` first")


@pytest.fixture(scope="module")
def hourly():
    return pd.read_parquet(CURATED)


def test_contract_holds(hourly):
    assert_curated_contract(hourly)


def test_every_selected_ba_has_the_full_utc_grid(hourly):
    cfg = load_config()
    assert sorted(hourly["ba_code"].unique()) == sorted(cfg.selected_bas)
    assert (hourly.groupby("ba_code").size() == 1096 * 24).all()
    steps = hourly.groupby("ba_code")["utc_period_end"].diff().dropna()
    assert (steps == pd.Timedelta(hours=1)).all()


def test_local_days_have_23_24_or_25_hours(hourly):
    per_day = hourly.groupby(["ba_code", "ref_date"]).size()
    assert set(per_day.unique()) <= {23, 24, 25}
    for ba, tz in hourly.groupby("ba_code")["reference_time_zone"].first().items():
        counts = per_day.loc[ba].value_counts()
        if tz in ("America/Phoenix", "Etc/GMT+5"):
            assert set(counts.index) == {24}
        else:  # three spring-forward and three fall-back days in the window
            assert counts.get(23) == 3 and counts.get(25) == 3
