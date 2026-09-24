# Data Contract: Curated Hourly Table

`data/curated/hourly_forecast_performance.parquet` is produced by `python -m dfp.pipeline`.

## Source

| Item | Value |
|---|---|
| Publisher | U.S. Energy Information Administration (EIA) |
| Collection | Form EIA-930, Hourly Electric Grid Monitor |
| Files | Six-month BALANCE files, `https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_BALANCE_{YYYY}_{Jan_Jun\|Jul_Dec}.csv` |
| BA metadata | `https://www.eia.gov/electricity/930-content/EIA930_Reference_Tables.xlsx`, sheet `BAs` |
| Provenance | URL, retrieval time, HTTP `Last-Modified`, byte size, SHA-256 for every file, in `data/curated/run_manifest.json` |
| Licensing | U.S. government public data. Raw files (~290 MB) are not committed; the pipeline re-downloads them. |

Source fields used:

| Source column | Pipeline column | Meaning |
|---|---|---|
| `Balancing Authority` | `ba_code` | EIA BA code |
| `UTC Time at End of Hour` | `utc_period_end` | Hour-ending UTC timestamp (canonical key) |
| `Local Time at End of Hour`, `Data Date` | validation only | EIA's local rendering; used to verify the time-zone mapping |
| `Demand (MW)` | `actual_mw_reported` | BA-reported hourly demand |
| `Demand Forecast (MW)` | `forecast_mw_reported` | BA-reported day-ahead demand forecast |
| `Demand (MW) (Imputed)` | validation only | EIA's replacement value, used only to detect EIA-rejected actuals |

EIA revises historical values, and the six-month files are regenerated. All files used here were last modified 2026-09-24. A rerun on a later date can differ. The published forecast may reflect BA resubmissions; the files do not record forecast vintage.

## Grain and key

One row per **balancing authority × UTC hour** in the evaluation window, including hours with no source row.

Key: `(ba_code, utc_period_end)`. It is enforced unique, and the pipeline fails if a duplicated key carries conflicting values.

## Timestamp rules

1. EIA timestamps are **hour-ending**. The row at `utc_period_end = 14:00Z` covers 13:00–14:00 UTC. `utc_period_start = utc_period_end − 1h`.
2. Local attributes come from `utc_period_start` converted to the BA's reference zone. They are never parsed from EIA's local string, because that string repeats during the fall-back hour.
3. `local_hour` is hour-beginning, 0–23: `local_hour = 17` means 17:00–18:00 local. `local_date` is the local date of the interval start.
4. On a fall-back day `local_hour = 1` occurs twice. The two rows differ in `utc_offset_hours` and `is_dst` and stay unique on the UTC key. A spring-forward day has no `local_hour = 2`.
5. Reference zone per BA: the EIA reference-table label mapped to an IANA zone (`config/pipeline.toml`). One override applies. **MISO and LGEE** are labelled "Eastern", but every source row is at fixed UTC−5 (EST, no DST), which matches MISO's market-time convention. They use `Etc/GMT+5`.
6. The mapping is verified on every source row: the derived local end time and local date must equal EIA's own local columns. Current result: 0 mismatches across all 55 candidate BAs.

## Evaluation window

`[2023-09-01 00:00, 2026-09-01 00:00)` in each BA's reference local calendar, converted to UTC per BA. This gives 36 complete local months for every BA. **Expected hours** are counted on the UTC sequence, not `days × 24`: 26,304 per BA (1,096 days; three spring-forward and three fall-back days cancel out).

August 2026 is the last complete local month available on the retrieval date. September 2026 was partial and is excluded.

## Value rules

| Column | Rule |
|---|---|
| `actual_status` | `missing` if the reported value is blank. `eia_replaced` if EIA published an imputed replacement for a reported value, meaning EIA's anomaly screening rejected it. `nonpositive` if ≤ 0. Otherwise `valid`. |
| `actual_mw` | `actual_mw_reported` when `actual_status = valid`, else null. **EIA-imputed values are never used.** |
| `forecast_status` | `missing`, `nonpositive` or `valid`, as above. EIA does not impute forecasts. |
| `forecast_mw` | `forecast_mw_reported` when valid, else null. **Missing forecasts are never imputed.** A missing forecast means the object being evaluated is absent. |
| `is_paired` | `actual_mw` and `forecast_mw` are both non-null. Metrics use paired hours only; exclusions are reported per BA. |
| `source_row_present` | False when EIA published no row for an expected hour. |

Only a blank cell counts as missing. Any other non-numeric text makes the pipeline fail, rather than silently turning into null.

## Coverage definitions (per BA, over expected UTC hours)

- actual coverage = hours with `actual_mw` non-null ÷ expected hours
- forecast coverage = hours with `forecast_mw` non-null ÷ expected hours
- paired coverage = hours with `is_paired` ÷ expected hours

Gate: a BA passes only if all three are ≥ 95%. Outputs are `data/curated/ba_coverage.csv` (window) and `data/curated/ba_monthly_coverage.csv` (local month).

## Fields

| Field | Type | Notes |
|---|---|---|
| `ba_code` | string | |
| `utc_period_end` | timestamp, UTC | canonical key |
| `utc_period_start` | timestamp, UTC | |
| `local_period_start` | timestamp, naive local | reference-zone wall clock |
| `local_date` | date | local date of interval start |
| `local_hour` | int 0–23 | hour-beginning |
| `utc_offset_hours` | float | e.g. −4.0 |
| `is_dst` | bool | offset differs from the zone's standard offset |
| `reference_time_zone` | string | IANA zone used |
| `source_row_present` | bool | |
| `actual_mw`, `forecast_mw` | float, nullable | usable values |
| `actual_status`, `forecast_status` | string | see value rules |
| `is_paired` | bool | |
| `actual_mw_reported`, `forecast_mw_reported` | float, nullable | as published, for audit |
| `source_file` | string | originating six-month file |
