# Demand Forecast Performance & Operational Exceptions

Evaluation of published day-ahead electricity-demand forecasts across selected U.S. balancing authorities.

Organizations rely on forecasts they often did not build themselves. This project asks how reliable an existing operational forecast is, where its errors are systematic, and whether simple post-processing improves it.

The setting is U.S. electricity demand. Each balancing authority publishes an hourly day-ahead demand forecast and the demand that followed, through the EIA-930 Hourly Electric Grid Monitor. The same questions apply to sales forecasts, demand plans, staffing models and budget-versus-plan variance.

> **Status:** the analytical layer is built (metrics, benchmarks, segments, exception candidates) and under review. Reporting and conclusions come later.

## Scope

- **Window:** 36 complete months (BA reference time), 2023-09-01 to 2026-08-31, which is 26,304 hourly observations per BA.
- **Population:** 8 BAs (PJM, SOCO, TVA, ISNE, BPAT, PSCO, AECI, PNM), chosen on data coverage and reporting stability before any error metric was computed. See [reports/phase0_gate.md](reports/phase0_gate.md).
- **Independent case study on public data.** No client, stakeholder or operational use is implied.

## Run

```bash
python3.11 -m venv .venv && .venv/bin/pip install -e ".[test]"
.venv/bin/python -m dfp.pipeline                        # uses config/pipeline.toml
.venv/bin/python -m dfp.pipeline --start 2023-09-01 --end 2026-09-01 --bas PJM,ISNE
.venv/bin/python -m dfp.pipeline --refresh              # re-download EIA files
.venv/bin/python -m pytest
```

The pipeline downloads the EIA source files (about 290 MB, not committed) and validates keys, values and time zones. It computes coverage and writes:

| Output | Content |
|---|---|
| `data/curated/fact_hourly_performance.parquet` | One row per BA × UTC hour for selected BAs |
| `data/curated/ba_coverage.csv` | Coverage, gate result and stability for every candidate BA |
| `data/curated/ba_monthly_coverage.csv` | Coverage by BA × reference-time month |
| `data/curated/run_manifest.json` | Source URLs, retrieval times, file hashes, row counts, exclusions, analysis parameters |
| `data/analysis/ba_reconciliation.csv` | Per-BA reference values that downstream reporting must reproduce |
| `data/analysis/segment_metrics.csv` | Additive sums and metrics by BA × segment × evaluation set × forecast type |
| `data/analysis/correctability.csv` | Naive vs published vs bias-corrected, with stability by year, quarter and hour |
| `data/analysis/exception_candidates.csv` | Rule-based exception flags with evidence |
| `data/analysis/tail_metrics.csv`, `naive_dst_sensitivity.csv`, `reference_values.csv` | Tail metrics, naive-definition sensitivity, Gaussian reference values |

Definitions for grain, timestamps and missing values are in [docs/data_contract.md](docs/data_contract.md). Metric and benchmark definitions are in [docs/metric_catalogue.md](docs/metric_catalogue.md).
