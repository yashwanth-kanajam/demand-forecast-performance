# Power BI Handoff Files

Written by `python -m dfp.pipeline` to `data/bi/`.

- **Format:** UTF-8 CSV, comma-separated, header row, no index column.
- **Timestamps:** UTC timestamps are ISO 8601 with a `Z` suffix. Reference-clock timestamps are ISO 8601 without an offset. Dates are `YYYY-MM-DD`. Booleans are `true`/`false`.
- **Why CSV and not Excel:** Excel serial dates and header promotion caused typing problems in the smoke test.
- **Git:** `fact_hourly_performance.csv` (about 36 MB) is git-ignored and regenerated. The other files are committed.

**Sign conventions:** error = forecast − actual (positive = overforecast). Adjustment = mean residual (actual − forecast), added to the published forecast.

## Model

```
dim_ba[ba_code] 1 ──< fact_hourly_performance[ba_code]
dim_date[date]  1 ──< fact_hourly_performance[ref_date]   (BA reference-time date)
```

`ba_metric_summary` and `exception_candidates` are standalone reference tables keyed by `ba_code`. They can relate to `dim_ba` as many-to-one.

Hourly comparisons such as the seasonal naive are precomputed in Python. Standard DAX date intelligence is not used at hourly grain.

## fact_hourly_performance.csv

Grain: BA × UTC hour. 210,432 rows (8 BAs × 26,304 hours).

| Column | Type | Notes |
|---|---|---|
| `ba_code` | text | key to `dim_ba` |
| `utc_period_end` | datetime (UTC) | canonical key with `ba_code`; hour-ending |
| `utc_period_start` | datetime (UTC) | |
| `ref_period_start` | datetime (no offset) | BA reference/reporting clock |
| `ref_date` | date | key to `dim_date` |
| `ref_hour` | whole number 0–23 | hour-beginning, reference clock |
| `utc_offset_hours` | decimal | |
| `is_dst` | true/false | |
| `actual_mw` | decimal, nullable | usable reported demand |
| `forecast_mw` | decimal, nullable | published day-ahead forecast |
| `naive_forecast_mw` | decimal, nullable | seasonal naive, same reference-clock hour 7 days earlier |
| `corrected_forecast_mw` | decimal, nullable | published + trailing adjustment |
| `adjustment_mw` | decimal, nullable | trailing mean residual (actual − forecast) |
| `is_paired` | true/false | actual and published forecast both usable |
| `in_common_set` | true/false | paired, naive and corrected all present; used for every three-way comparison |
| `high_demand` | high/other/blank | top decile of actual (per BA, whole window) |
| `high_forecast` | high/other/blank | top decile of published forecast (sensitivity) |
| `demand_band` | Q1–Q5/blank | quintile of actual, per BA |

## dim_date.csv

One row per reference date (1,096 rows). Columns:
- `date`, `year`, `month`, `month_name`, `year_month`;
- `day_of_week` (1 = Monday), `day_name`, `day_type`;
- `season` and `season_period` (e.g. `2024-12 Winter`);
- `eval_year` (Y1–Y3).

## dim_ba.csv

`ba_code`, `ba_name`, `region_name`, `eia_time_zone_label`, `reference_time_zone`, `median_actual_mw`, `paired_coverage_pct`.

## ba_metric_summary.csv (reconciliation reference)

This is identical to `data/analysis/ba_reconciliation.csv`, one row per BA, and Power BI measures must reproduce it. It uses two populations:

- **`*_all_paired`: incumbent KPIs.** Every hour with actual and published forecast. Fields: `paired_n_hours`, `sum_actual_mw_h_all_paired`, `published_wape_pct_all_paired`, `published_mae_mw_all_paired`, `published_bias_mw_all_paired`, `published_norm_bias_pct_all_paired`, `peak_actual_defined_wape_pct_all_paired`, `worst1_contribution_pct_all_paired`.
- **`*_common`: benchmark comparison.** Identical hours for all three forecasts (`in_common_set = true`). Fields: `common_n_hours`, `sum_actual_mw_h_common`, `published_/naive_/corrected_` × `wape_pct_common` / `mae_mw_common` / `norm_bias_pct_common`, `corrected_vs_published_common_delta_pp`, `corrected_vs_published_common_relative_delta_pct`, `published_skill_vs_naive_common`.
- **Classification:** `years_improved_of_3`, `quarters_improved`, `quarters_evaluated`, `project_rule_class` (project-defined practical-improvement rule), `peak_robustness`, `source_semantic_flag`, `category` (A–D), `exception_reasons` (`;`-separated codes).

**Rule for the report:** any published-vs-naive-vs-corrected visual must filter the fact table to `in_common_set = true`.

`sum_*_mw_h` is the sum of hourly MW values over one-hour intervals; it is not labelled MWh.

## exception_candidates.csv

`ba_code`, `exception`, `evidence`, `n_hours` (sample size behind the flag), `rule` (the fixed rule that fired).
