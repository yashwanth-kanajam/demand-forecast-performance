# Demand Forecast Performance & Operational Exceptions

For six of eight U.S. balancing authorities (BAs), the published day-ahead demand forecast had 61–86% less error than a seasonal-naive benchmark, the same hour one week earlier. PNM and PSCO did not beat that benchmark. PNM's forecast was only 5% better overall, PSCO's was 15% worse, and each lost to it in one of the three years.

Some of the remaining error can be fixed. ISNE, PJM and SOCO underforecast by 1.3–1.8% of demand in every year. Adding back each BA's recent average miss for the same hour cut their WAPE by 28–55% and helped in all 12 quarters. AECI and BPAT were already close to unbiased (normalized bias −0.02% and −0.06%), so the same correction did little for BPAT and made AECI slightly worse. TVA's bias was persistent, but correcting it reduced error by only 2.2%.

Overall accuracy also hides bias by hour. ISNE underforecasts by 3–6% between 00:00 and 05:00. PJM underforecasts late in the evening and overnight, then overforecasts around 05:00–06:00. Both patterns hold in every year while overall WAPE sits at 2.5–3.5%.

In practice, that means keeping the published forecast for AECI, BPAT and TVA, and trialling a bias recalibration for ISNE, PJM and SOCO by running both versions side by side for a further period. Data are hourly actual demand and published forecasts from the U.S. Energy Information Administration's Form EIA-930, September 2023 to August 2026.

| BA | Published → corrected WAPE | Change (pp) | Change (relative) | Quarters improved |
|---|---|--:|--:|--:|
| PJM | 3.49% → 2.11% | −1.37 | −39.4% | 12 / 12 |
| SOCO | 1.46% → 0.66% | −0.81 | −55.2% | 12 / 12 |
| ISNE | 2.49% → 1.79% | −0.70 | −28.0% | 12 / 12 |
| TVA | 2.32% → 2.27% | −0.05 | −2.2% | 10 / 12 |
| BPAT | 1.96% → 1.95% | −0.01 | −0.6% | 7 / 12 |
| AECI | 2.45% → 2.52% | +0.07 | +2.8% | 1 / 12 |

WAPE is weighted absolute percentage error. Both forecasts are scored on the same hours. PNM and PSCO are left out of this table because EIA metadata does not make clear whether their gap is forecast bias or a difference in how the two series are reported ([source-semantics audit](docs/source_semantics_audit.md)). The full results are in [reports/forecast_performance_analysis.md](reports/forecast_performance_analysis.md), with a [figure](reports/figures/wape_published_vs_corrected.png) and a [one-page summary](reports/executive_brief.md).

## Run it

Requires Python 3.11+.

```bash
python3.11 -m venv .venv && .venv/bin/pip install -e ".[test,figures]"
.venv/bin/python -m dfp.pipeline      # downloads EIA files (~290 MB) and regenerates all outputs
.venv/bin/python -m pytest
.venv/bin/python -m dfp.figures
```

The test suite has 88 tests. 22 of them check the curated and analysis outputs and are skipped unless the pipeline has run. Those 22 need the ~290 MB download and were not run for this release. The other 66 pass without it.

To change the window or the BA list, use `--start`, `--end` and `--bas` ([docs/workflow.md](docs/workflow.md)).

## Limitations

EIA revises values in place, and forecast vintages and resubmissions are not visible, so this is a retrospective evaluation. The correction assumes forecasts are issued the day before.

BAs were chosen on reporting quality, which may favour operationally mature systems. Texas and California are not represented. PJM's daylight-saving transition days are blank in the source.

Seasonal statements rest on three annual cycles. No cost, reliability or operational impact is estimated.

## Reference

| Item | Detail |
|---|---|
| Source | U.S. EIA Form EIA-930 six-month BALANCE files and BA reference tables, retrieved 2026-09-24 |
| Series | Hourly actual demand; published day-ahead demand forecast |
| Window | 36 complete months, 2023-09-01 to 2026-08-31: 26,304 hourly observations per BA |
| Population | 8 BAs chosen from the 50 with at least 95% of hours carrying both an actual and a forecast value, for reporting stability, scale and geographic spread. The selection was made before any error metric was computed ([reports/ba_selection.md](reports/ba_selection.md)) |

**Method.** The published forecast is compared with a seasonal-naive benchmark and a bias-corrected version on the same hours. The correction adds the average error for the same BA and hour over the previous four weeks, leaving out the day immediately before, so it uses only earlier data. Automated tests check that later values cannot change it. Error is forecast minus actual, so positive values mean overforecasting. An improvement counts as practical only if WAPE falls by at least 5% overall and falls in every year. An apparent PJM underforecast at peak hours was not reported because it disappears when peaks are defined by forecast rather than actual demand. Definitions are in the [metric catalogue](docs/metric_catalogue.md).

**Data quality.** Before scoring, the pipeline checks timestamps, duplicates, coverage and missing values. Missing actuals or forecasts are not filled. Time-zone and daylight-saving handling are in the [data contract](docs/data_contract.md).

**PNM and PSCO.** Both are in the data and the Power BI report but not in the headline finding. Their reported forecasts run 5.8% and 9.4% below actual demand, and the source metadata cannot separate forecast bias from reporting differences.

**Power BI report.** Two pages built in the Power BI Service with a semantic model and DAX measures. Forecast Performance Review has KPI cards, published vs bias-corrected WAPE, directional bias by BA and an attention list that flags PNM and PSCO ([screenshot](docs/evidence/page1_forecast_performance_review.png)). Error Patterns & Correctability shows one BA at a time: bias by hour, quarterly stability of the correction, the three forecasts side by side and bias by demand level ([screenshot](docs/evidence/page2_error_patterns_ISNE.png)). The measures match the Python outputs for all 8 BAs ([reconciliation](docs/powerbi_reconciliation.md)), and both pages are in [reports/demand_forecast_performance.pdf](reports/demand_forecast_performance.pdf). The .pbix file is not included because its data connection points to private storage. The [DAX measures](docs/dax_measures.md), [semantic model](docs/semantic_model.md) and [report specification](docs/report_spec.md) describe it instead.

```
config/pipeline.toml     window, coverage gate, BA selection, analysis and exception parameters
src/dfp/                 acquisition, validation, timestamps, curation, benchmarks, metrics, analysis, BI extracts
tests/                   time handling, correction, reconciliation and BI extract tests
data/curated/            coverage tables and run manifest (hourly fact regenerated, not committed)
data/analysis/           segment metrics, correctability, stability, exceptions, reconciliation reference
data/bi/                 Power BI extracts (hourly fact regenerated, not committed)
docs/                    data contract, metric catalogue, source audit, workflow, Power BI model/DAX/report spec
docs/evidence/           Power BI model and report page screenshots
reports/                 BA selection, full analysis, executive brief, figure, Power BI PDF export
```

Python (pandas, pyarrow), pytest and matplotlib; Power BI (semantic model, DAX, Power Query) for the reporting layer.
