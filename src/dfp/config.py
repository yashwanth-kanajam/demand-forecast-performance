"""Load pipeline configuration from config/pipeline.toml."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "pipeline.toml"


@dataclass(frozen=True)
class Config:
    balance_file_url: str
    reference_table_url: str
    raw_dir: Path
    start_local_date: date
    end_local_date: date
    min_actual_coverage: float
    min_forecast_coverage: float
    min_paired_coverage: float
    timezones: dict[str, str]
    timezone_overrides: dict[str, str] = field(default_factory=dict)
    selected_bas: list[str] = field(default_factory=list)


def load_config(path: Path = DEFAULT_CONFIG, **overrides) -> Config:
    raw = tomllib.loads(Path(path).read_text())
    values = dict(
        balance_file_url=raw["source"]["balance_file_url"],
        reference_table_url=raw["source"]["reference_table_url"],
        raw_dir=PROJECT_ROOT / raw["source"]["raw_dir"],
        start_local_date=date.fromisoformat(raw["window"]["start_local_date"]),
        end_local_date=date.fromisoformat(raw["window"]["end_local_date"]),
        min_actual_coverage=raw["gate"]["min_actual_coverage"],
        min_forecast_coverage=raw["gate"]["min_forecast_coverage"],
        min_paired_coverage=raw["gate"]["min_paired_coverage"],
        timezones=dict(raw["timezones"]),
        timezone_overrides=dict(raw.get("timezone_overrides", {})),
        selected_bas=list(raw["selection"]["selected_bas"]),
    )
    values.update({k: v for k, v in overrides.items() if v is not None})
    if values["start_local_date"] >= values["end_local_date"]:
        raise ValueError("start_local_date must precede end_local_date")
    return Config(**values)
