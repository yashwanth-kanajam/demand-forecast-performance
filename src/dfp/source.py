"""Acquire and read EIA-930 six-month BALANCE files and the BA reference table."""
from __future__ import annotations

import hashlib
import shutil
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from .config import Config

# Source column -> pipeline column. Only these are read.
SOURCE_COLUMNS = {
    "Balancing Authority": "ba_code",
    "Data Date": "eia_data_date",
    "Hour Number": "eia_hour_number",
    "Local Time at End of Hour": "eia_local_end",
    "UTC Time at End of Hour": "eia_utc_end",
    "Demand Forecast (MW)": "forecast_mw_reported",
    "Demand (MW)": "actual_mw_reported",
    "Demand (MW) (Imputed)": "actual_mw_eia_imputed",
}
NUMERIC_COLUMNS = ["forecast_mw_reported", "actual_mw_reported", "actual_mw_eia_imputed"]


def balance_file_names(start_local: date, end_local: date) -> list[tuple[int, str]]:
    """(year, half) pairs of the six-month files covering [start_local, end_local).

    Files are partitioned by the BA-local 'Data Date'.
    """
    last = pd.Timestamp(end_local) - pd.Timedelta(days=1)
    pairs = []
    for year in range(start_local.year, last.year + 1):
        for half, (m0, m1) in (("Jan_Jun", (1, 6)), ("Jul_Dec", (7, 12))):
            h_start, h_end = date(year, m0, 1), date(year, m1, 28)
            if h_end >= start_local and h_start <= last.date():
                pairs.append((year, half))
    return pairs


def download(url: str, dest: Path) -> dict:
    """Download url to dest; return a provenance record."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=600) as resp, open(tmp, "wb") as out:
        last_modified = resp.headers.get("Last-Modified")
        shutil.copyfileobj(resp, out)
    tmp.replace(dest)
    return {
        "url": url,
        "file": dest.name,
        "retrieved_at_utc": retrieved_at,
        "http_last_modified": last_modified,
        **file_fingerprint(dest),
    }


def _saved_headers(path: Path) -> dict:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        name, sep, value = line.partition(":")
        if sep:
            out[name.strip().lower()] = value.strip()
    return out


def file_fingerprint(path: Path) -> dict:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def acquire(cfg: Config, refresh: bool = False) -> list[dict]:
    """Ensure the BALANCE files and reference table exist locally; return provenance."""
    records = []
    targets = [
        (cfg.balance_file_url.format(year=y, half=h), cfg.raw_dir / f"EIA930_BALANCE_{y}_{h}.csv")
        for y, h in balance_file_names(cfg.start_ref_date, cfg.end_ref_date)
    ]
    targets.append((cfg.reference_table_url, cfg.raw_dir / "EIA930_Reference_Tables.xlsx"))
    for url, dest in targets:
        if refresh or not dest.exists():
            records.append(download(url, dest))
        else:
            # Reused local copy: prefer saved HTTP response headers, else file mtime.
            headers = _saved_headers(dest.with_suffix(".headers"))
            mtime = datetime.fromtimestamp(dest.stat().st_mtime, timezone.utc)
            records.append({
                "url": url,
                "file": dest.name,
                "retrieved_at_utc": headers.get("date") or mtime.isoformat(timespec="seconds"),
                "http_last_modified": headers.get("last-modified"),
                **file_fingerprint(dest),
            })
    return records


def read_balance_files(cfg: Config) -> pd.DataFrame:
    """Read the needed columns of every BALANCE file as text, then parse numerics.

    Numeric parsing is strict: only a blank cell is missing; any other
    non-numeric text (including 'n/a', 'NULL') raises.
    """
    frames = []
    for year, half in balance_file_names(cfg.start_ref_date, cfg.end_ref_date):
        name = f"EIA930_BALANCE_{year}_{half}.csv"
        df = pd.read_csv(cfg.raw_dir / name, usecols=list(SOURCE_COLUMNS), dtype=str,
                         keep_default_na=False, na_values=[""])
        df = df.rename(columns=SOURCE_COLUMNS)
        df["source_file"] = name
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True)
    for col in NUMERIC_COLUMNS:
        raw[col] = pd.to_numeric(raw[col].str.replace(",", "", regex=False), errors="raise")
    return raw


def read_reference_table(cfg: Config) -> pd.DataFrame:
    ref = pd.read_excel(cfg.raw_dir / "EIA930_Reference_Tables.xlsx", sheet_name="BAs")
    ref = ref.rename(columns={
        "BA Code": "ba_code",
        "BA Name": "ba_name",
        "Time Zone": "eia_time_zone",
        "Region/Country Code": "region_code",
        "Region/Country Name": "region_name",
        "Generation Only BA": "generation_only",
        "U.S. BA": "us_ba",
        "Active BA": "active",
        "Activation Date": "activation_date",
        "Retirement Date": "retirement_date",
    })
    return ref[["ba_code", "ba_name", "eia_time_zone", "region_code", "region_name",
                "generation_only", "us_ba", "active", "activation_date", "retirement_date"]]
