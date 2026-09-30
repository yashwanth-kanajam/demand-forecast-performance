# Demand Forecast Performance & Operational Exceptions

Organizations routinely rely on forecasts they did not build. This case study evaluates whether an existing operational forecast is reliable, where its errors are systematic, and whether simple historical post-processing can improve performance without replacing the incumbent forecasting process.

The setting is U.S. electricity demand. Balancing authorities (BAs) publish an hourly day-ahead demand forecast alongside the demand that followed, through the U.S. Energy Information Administration's Form EIA-930. The same evaluation applies to sales forecasts, demand plans, staffing and capacity models, and budget-versus-plan variance.

## Headline finding

**Forecast error was not equally correctable across systems.**
- **ISNE, PJM and SOCO** showed persistent directional bias. A simple, strictly causal historical adjustment reduced it in all 12 quarters.
- **AECI and BPAT** were already effectively unbiased, and the same adjustment gave little or no benefit (BPAT) or slightly worsened performance (AECI).
- **TVA** is a third case: persistent directional bias can exist without the correction reducing overall error enough to be worth applying.

| BA | Published → corrected WAPE | Change (pp) | Change (relative) | Quarters improved |
|---|---|--:|--:|--:|
| PJM | 3.49% → 2.11% | −1.37 | −39.4% | 12 / 12 |
| SOCO | 1.46% → 0.66% | −0.81 | −55.2% | 12 / 12 |
| ISNE | 2.49% → 1.79% | −0.70 | −28.0% | 12 / 12 |
| TVA | 2.32% → 2.27% | −0.05 | −2.2% | 10 / 12 |
| BPAT | 1.96% → 1.95% | −0.01 | −0.6% | 7 / 12 |
| AECI | 2.45% → 2.52% | +0.07 | +2.8% | 1 / 12 |

WAPE is the weighted absolute percentage error. Both forecasts are scored on identical hours (September 2023 – August 2026). PNM and PSCO are covered separately [below](#pnm-and-psco).

![Published vs bias-corrected WAPE by balancing authority](reports/figures/wape_published_vs_corrected.png)

## Key findings

1. **The incumbent forecasts carry real skill.** For 6 of 8 BAs the published forecast removes 61–86% of the error of a seasonal-naive benchmark.
2. **Correctable error is directional and stable.** ISNE, PJM and SOCO underforecast by 1.3–1.8% of demand in every year, which is what a trailing correction can exploit.
3. **Aggregate accuracy hides hour-level bias.** ISNE underforecasts by 3–6% overnight (00:00–05:00). PJM underforecasts late evening and overnight, and overforecasts around 05:00–06:00. Both patterns hold in every year while overall WAPE sits at 2.5–3.5%. SOCO's bias is broadly uniform across hours.
4. **Where bias is absent, correction adds nothing.** AECI and BPAT show normalized bias of −0.02% and −0.06%.
5. **No BA's error is dominated by a handful of extreme hours.** The worst 1% of hours carry 2.9–6.3% of absolute error, close to the 3.6% expected for normally distributed error.

## Final categories

| BA | Category |
|---|---|
| ISNE | Systematic and correctable |
| PJM | Systematic and correctable |
| SOCO | Systematic and correctable |
| PNM | Apparently correctable — **SOURCE SEMANTICS UNCERTAIN** |
| PSCO | Apparently correctable — **SOURCE SEMANTICS UNCERTAIN** |
| TVA | Persistent bias — low correction benefit |
| AECI | Little/no correctable bias |
| BPAT | Little/no correctable bias |

## Management implications

- Retain the incumbent forecast where correction is small or unstable (AECI, BPAT, TVA).
- Consider targeted bias recalibration where improvement is persistent (ISNE, PJM, SOCO), after comparing corrected and incumbent performance side by side over a further out-of-sample period.
- Monitor recurring hour-specific bias separately from aggregate WAPE; a single KPI hides it.
- Keep source-semantic anomalies separate from forecast-performance conclusions.

A one-page summary is in [reports/executive_brief.md](reports/executive_brief.md).

## Scope and data

| Item | Detail |
|---|---|
| Source | U.S. EIA Form EIA-930 six-month BALANCE files and BA reference tables, retrieved 2026-09-24 (SHA-256 recorded) |
| Series | Hourly actual demand; published day-ahead demand forecast |
| Window | 36 complete months, 2023-09-01 to 2026-08-31, in each BA's reporting clock: 26,304 hourly observations per BA |
| Population | 8 BAs chosen from 50 that passed a ≥95% actual, forecast and paired coverage gate, on reporting stability and scale/geographic diversity, **before** any error metric was computed ([reports/ba_selection.md](reports/ba_selection.md)) |

## Approach

The incumbent forecast is the thing being evaluated, so there is no machine learning. Error is forecast − actual (positive means overforecast). **WAPE** (Σ|error| / Σactual) is the primary cross-BA measure, supported by MAE in MW, **normalized bias** (Σerror / Σactual), peak WAPE on the top decile of actual demand, and the share of absolute error carried by the worst 1% of hours. A large-miss threshold metric was tested and dropped because stable bias confounded it. Formulas are in [docs/metric_catalogue.md](docs/metric_catalogue.md).

Three forecasts are compared on an identical set of hours:
- **Seasonal naive:** the same reporting-clock hour seven days earlier, with deterministic daylight-saving handling. A strict 168-hour lag moves naive WAPE by at most 0.014 pp.
- **Published:** the incumbent, as reported. Its KPIs are also reported on all paired hours.
- **Bias-corrected:** the published forecast plus the mean residual (actual − forecast) for the same BA and reporting hour over days D−29 to D−2. It needs at least 14 days of history and is never filled.

Every corrected value uses prior data only; tests confirm that perturbing the target day, the previous day or day D−30 leaves the correction unchanged. Improvement is judged by year and by quarter. The practical-improvement rule is project-defined: corrected WAPE at least 5% lower overall and lower in every year. Peak-bias findings must hold under both actual-defined and forecast-defined peaks; PJM's apparent peak underforecast disappears under the forecast-defined selection, so it is not reported as a finding. Full results are in [reports/forecast_performance_analysis.md](reports/forecast_performance_analysis.md).

## Data quality

Records are keyed on BA + UTC hour with a complete UTC grid per BA, and each BA's reporting clock is checked against EIA's local timestamps on every source row (0 mismatches; MISO and LGEE report fixed EST, PNM fixed MST). Parsing is strict and conflicting duplicate keys fail the run. Actuals replaced by EIA's anomaly screening are treated as missing, EIA-imputed values are never used, and missing forecasts are never imputed. Each BA must clear ≥95% actual, forecast and paired coverage, plus monthly stability. The 88 automated tests include DST transition days drawn from real EIA rows. See [docs/data_contract.md](docs/data_contract.md).

## PNM and PSCO

PNM and PSCO appear in the data and the Power BI report but are excluded from the headline finding. Their reported forecasts show a persistent level discrepancy (−5.8% and −9.4%; PSCO's gap has widened since January 2026), and available EIA metadata does not resolve whether that reflects forecast-process bias, reporting-scope differences, resubmission behaviour or another source-definition effect. EIA itself notes that for some BAs the actual-vs-forecast comparison "is not very meaningful". The audit is in [docs/source_semantics_audit.md](docs/source_semantics_audit.md).

## Power BI report

A two-page report built in the Power BI Service on a semantic model with two star-schema relationships and the full DAX measure catalogue:
- **Forecast Performance Review:** equal-weighted BA KPI cards, published vs bias-corrected WAPE on common comparison hours, directional bias by BA, and an operating attention list that flags PNM and PSCO as SOURCE SEMANTICS UNCERTAIN.
- **Error Patterns & Correctability:** single-BA view of bias by reference hour, quarterly stability of the correction, seasonal naive vs published vs corrected, and bias by demand quintile.

![Forecast Performance Review](docs/evidence/page1_forecast_performance_review.png)

![Error Patterns & Correctability, ISNE](docs/evidence/page2_error_patterns_ISNE.png)

The Power BI measures were reconciled against the Python outputs for all 8 BAs (largest difference 4.9e-07); see [docs/powerbi_reconciliation.md](docs/powerbi_reconciliation.md). A PDF export of both pages is at [reports/demand_forecast_performance.pdf](reports/demand_forecast_performance.pdf).

The .pbix file is not included because its embedded data source points to private storage. The [DAX measures](docs/dax_measures.md), [semantic model](docs/semantic_model.md) and [report specification](docs/report_spec.md) document it instead.

## Repository structure

```
config/pipeline.toml     window, coverage gate, BA selection, analysis and exception parameters
src/dfp/                 acquisition, validation, timestamps, curation, benchmarks, metrics, analysis, BI extracts
tests/                   88 tests (DST, causality, reconciliation, BI extracts)
data/curated/            coverage tables and run manifest (hourly fact regenerated, not committed)
data/analysis/           segment metrics, correctability, stability, exceptions, reconciliation reference
data/bi/                 Power BI extracts (hourly fact regenerated, not committed)
docs/                    data contract, metric catalogue, source audit, workflow, Power BI model/DAX/report spec
docs/evidence/           Power BI model and report page screenshots
reports/                 BA selection, full analysis, executive brief, figure, Power BI PDF export
```

## Limitations

- **Revisions and vintage:** EIA revises values in place, and forecast vintage and resubmissions are not observable. The correction assumes forecasts are issued the day before and excludes the previous day's residuals.
- **Selection:** BAs were selected on reporting quality, which may favour operationally mature systems. Texas and California are not represented.
- **DST gaps:** PJM's daylight-saving transition days are blank in the source.
- **Seasons:** seasonal statements rest on three annual cycles.
- **Impact:** no cost, reliability or operational impact is estimated. This is an independent analysis of public data.

## Reproduce locally

Requires Python 3.11+.

```bash
python3.11 -m venv .venv && .venv/bin/pip install -e ".[test,figures]"
.venv/bin/python -m dfp.pipeline      # downloads EIA files (~290 MB) and regenerates all outputs
.venv/bin/python -m pytest
.venv/bin/python -m dfp.figures
```

The pipeline runs from the official EIA files through validation, benchmarks and correction to the BI extracts. The window and BA list are parameters (`--start 2023-09-01 --end 2026-09-01 --bas PJM,ISNE,SOCO,TVA,AECI,BPAT,PNM,PSCO`); options and outputs are in [docs/workflow.md](docs/workflow.md).

## Technology

Python (pandas, pyarrow), pytest, matplotlib for the static figure, and Power BI (semantic model, DAX, Power Query) for the reporting layer.
