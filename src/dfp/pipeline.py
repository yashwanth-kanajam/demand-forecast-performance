"""Rerunnable pipeline: acquire -> validate -> normalize timestamps -> coverage -> curated outputs.

Usage:
    python -m dfp.pipeline                       # config window, config BA selection
    python -m dfp.pipeline --start 2023-09-01 --end 2026-09-01 --bas PJM,ERCO
    python -m dfp.pipeline --refresh             # re-download source files
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone


from .config import PROJECT_ROOT, load_config
from .curate import build_hourly, candidate_bas, coverage_table, monthly_coverage
from .source import acquire, read_balance_files, read_reference_table

CURATED_DIR = PROJECT_ROOT / "data" / "curated"


def run(start: date | None = None, end: date | None = None, bas: list[str] | None = None,
        refresh: bool = False) -> dict:
    cfg = load_config(start_local_date=start, end_local_date=end, selected_bas=bas)
    CURATED_DIR.mkdir(parents=True, exist_ok=True)

    provenance = acquire(cfg, refresh=refresh)
    raw = read_balance_files(cfg)
    ref = read_reference_table(cfg)
    candidates, excluded = candidate_bas(raw, ref)

    hourly, audit = build_hourly(raw, candidates, cfg)
    coverage = coverage_table(hourly, candidates, cfg)
    tz_check = audit.pop("timezone_check")
    coverage = coverage.merge(tz_check, on="ba_code")

    coverage.to_csv(CURATED_DIR / "ba_coverage.csv", index=False)
    monthly_coverage(hourly).to_csv(CURATED_DIR / "ba_monthly_coverage.csv", index=False)

    selected = cfg.selected_bas
    failing = sorted(set(selected) - set(coverage.loc[coverage["passes_gate"], "ba_code"]))
    if failing:
        raise SystemExit(f"Selected BAs fail the coverage gate: {failing}")
    tz_bad = tz_check[tz_check["ba_code"].isin(selected)
                      & (tz_check[["local_end_mismatch", "local_date_mismatch"]].sum(axis=1) > 0)]
    if not tz_bad.empty:
        raise SystemExit(f"Selected BAs fail the local-time reproduction check: {tz_bad['ba_code'].tolist()}")
    if selected:
        curated = hourly[hourly["ba_code"].isin(selected)]
        curated.to_parquet(CURATED_DIR / "hourly_forecast_performance.parquet", index=False)

    manifest = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window_local": {"start": cfg.start_local_date.isoformat(), "end_exclusive": cfg.end_local_date.isoformat()},
        "gate": {"actual": cfg.min_actual_coverage, "forecast": cfg.min_forecast_coverage, "paired": cfg.min_paired_coverage},
        "source_files": provenance,
        "counts": {
            **{k: v for k, v in audit.items()},
            "candidate_bas": int(len(candidates)),
            "excluded_bas": excluded[["ba_code", "exclusion_reason"]].to_dict("records"),
            "bas_passing_gate": coverage.loc[coverage["passes_gate"], "ba_code"].tolist(),
            "missing_actual_hours_all_candidates": int(hourly["actual_mw"].isna().sum()),
            "missing_forecast_hours_all_candidates": int(hourly["forecast_mw"].isna().sum()),
            "timezone_mismatch_rows": int(tz_check[["local_end_mismatch", "local_date_mismatch"]].sum().sum()),
        },
        "selected_bas": selected,
        "curated_rows": int(hourly["ba_code"].isin(selected).sum()),
    }
    (CURATED_DIR / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    return manifest


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", type=date.fromisoformat, help="local start date (inclusive)")
    p.add_argument("--end", type=date.fromisoformat, help="local end date (exclusive)")
    p.add_argument("--bas", type=lambda s: [b.strip().upper() for b in s.split(",") if b.strip()],
                   help="comma-separated BA codes to curate (default: config selection)")
    p.add_argument("--refresh", action="store_true", help="re-download source files")
    a = p.parse_args()
    m = run(a.start, a.end, a.bas, a.refresh)
    print(json.dumps({k: m[k] for k in ("window_local", "selected_bas", "curated_rows")}, indent=2))
    print("BAs passing gate:", ", ".join(m["counts"]["bas_passing_gate"]))


if __name__ == "__main__":
    main()
