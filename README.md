# Demand Forecast Performance & Operational Exceptions

Evaluation of published day-ahead electricity-demand forecasts across selected U.S. balancing authorities.

Organizations rely on forecasts they often did not build themselves. This project asks how reliable an existing operational forecast is, where its errors are systematic, and whether simple post-processing improves it.

The setting is U.S. electricity demand. Each balancing authority publishes an hourly day-ahead demand forecast and the demand that followed, through the EIA-930 Hourly Electric Grid Monitor. The same questions apply to sales forecasts, demand plans, staffing models and budget-versus-plan variance.

> **Status:** foundation only. The data gate, BA selection and the validated hourly table are complete. Metrics, benchmarks and conclusions come in later phases.

## Scope

- **Window:** 36 complete local months, 2023-09-01 to 2026-08-31, which is 26,304 hourly observations per BA.
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
| `data/curated/hourly_forecast_performance.parquet` | One row per BA × UTC hour for selected BAs |
| `data/curated/ba_coverage.csv` | Coverage, gate result and stability for every candidate BA |
| `data/curated/ba_monthly_coverage.csv` | Coverage by BA × local month |
| `data/curated/run_manifest.json` | Source URLs, retrieval times, file hashes, row counts, exclusions |

Definitions for grain, timestamps and missing values are in [docs/data_contract.md](docs/data_contract.md).
