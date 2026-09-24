# Pipeline Workflow

A single rerunnable command regenerates every analytical output from the official EIA source files. The pipeline runs when invoked; no scheduled refresh is configured.

## Stages

```
EIA-930 six-month BALANCE files + BA reference table        (source.py)
  → acquisition with provenance: URL, retrieval time, HTTP Last-Modified, SHA-256
  → validation: strict numeric parsing, duplicate BA+UTC keys, EIA-rejected actuals   (validate.py)
  → UTC key + BA reference-time attributes, verified against EIA local time  (timestamps.py)
  → full UTC grid per BA and coverage gate (actual / forecast / paired ≥ 95%) (curate.py)
  → seasonal-naive benchmark and causal trailing correction                  (benchmarks.py)
  → metrics, segments, stability, peak robustness, exceptions, categories    (metrics.py, analysis.py)
  → BI-ready CSV extracts                                                    (bi.py)
```

## Commands

```bash
python3.11 -m venv .venv
.venv/bin/pip install -e ".[test,figures]"

# Full run with config/pipeline.toml (window 2023-09-01 .. 2026-09-01, 8 BAs)
.venv/bin/python -m dfp.pipeline

# Parameterised rerun: different window and/or BA list
.venv/bin/python -m dfp.pipeline --start 2024-01-01 --end 2026-01-01 --bas PJM,ISNE,SOCO

# Re-download the source files (EIA revises values in place)
.venv/bin/python -m dfp.pipeline --refresh

# Tests and the README figure
.venv/bin/python -m pytest
.venv/bin/python -m dfp.figures
```

- `--start` / `--end` are BA reference-time dates (end exclusive).
- `--bas` must name BAs that pass the coverage gate for the chosen window; otherwise the run stops and lists them.
- Analysis parameters are in `config/pipeline.toml` (`[analysis]`, `[exceptions]`). They were fixed before results were computed; changing them is a sensitivity analysis.

## Outputs regenerated on every run

| Output | Content |
|---|---|
| `data/curated/fact_hourly_performance.parquet` | Curated hourly fact with benchmarks and segments (not committed) |
| `data/curated/ba_coverage.csv`, `ba_monthly_coverage.csv` | Coverage gate and monthly stability for every candidate BA |
| `data/curated/run_manifest.json` | Source provenance, row counts, exclusions, parameters |
| `data/analysis/*.csv` | Segment metrics, correctability, quarterly stability, benchmark coverage, peak robustness, exceptions, reconciliation reference |
| `data/bi/*.csv` | Power BI extracts (`docs/bi_handoff.md`); the hourly fact CSV is not committed |

Raw source files (about 290 MB) are downloaded to `data/raw/` and are not committed.
