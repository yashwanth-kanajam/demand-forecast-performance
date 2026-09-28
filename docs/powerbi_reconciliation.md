# Power BI Reconciliation

**Status: Power BI reconciliation PASS for all 8 BAs** (evaluated in the Power BI Service semantic model, 2026-09-25). The two report pages were built on this model and checked visually against these values on 2026-09-26 (see "Report page check" at the end).

Three independent columns, not to be confused:
- **Python reference:** `data/bi/ba_metric_summary.csv`, produced by the pipeline.
- **DAX-logic replica:** `src/dfp/bi_replica.py`. It recomputes every **[R]** measure in `docs/dax_measures.md` from the handoff CSVs (`data/bi/*.csv`), using the same filters, populations, tie-breaking and quarter iteration as the DAX. This checks the handoff files and the measure logic, not Power BI itself. Test: `tests/test_analysis_outputs.py::test_dax_logic_replica_reproduces_reference_values` (tolerance 1e-9 relative); largest absolute difference 5.7e-14.
- **Power BI result:** the model measures evaluated by the Power BI Service engine in DAX query view, one BA per row (`ADDCOLUMNS ( VALUES ( DimBA[ba_code] ), … )`, no slicers or filters). Percent measures were multiplied by 100 and formatted to 6 decimals in the query so the results grid did not round them.

## Procedure and result

Two DAX queries were run in the service against the model:
1. **BA-level check.** For each BA, compares every **[R]** measure with the matching `BAMetricSummary` column (the Python reference loaded into the model, disconnected). It returns PASS only if every metric difference is ≤ 0.0001 and the counts (paired hours, common hours, quarters improved, years improved) match exactly. **All 8 BAs returned PASS.**
2. **Value capture.** Returns the individual measure values shown in the *Power BI result* column below, for every measure in the table.

**PASS** if |Power BI − reference| ≤ 0.0001 for percentages, MW and pp, and exact for counts. The largest captured difference is 4.9e-07, which is the 6-decimal display precision of the capture. Every row below passes.

Display fix applied in the service (2026-09-26): `Quarters Improved` and `Years Improved` originally returned BLANK rather than 0 when nothing improved (AECI's `Years Improved`), because `COUNTROWS` over an empty table is BLANK in DAX. Both measures now end in `+ 0` (see `docs/dax_measures.md`). The meaning is unchanged, and the re-run returns 0 for AECI.

Relationship audit (`INFO.VIEW.RELATIONSHIPS()`, same session):
- `FactHourlyForecastPerformance[ref_date]` (many) → `DimDate[date]` (one): active, single direction.
- `FactHourlyForecastPerformance[ba_code]` (many) → `DimBA[ba_code]` (one): active, single direction.
- `BAMetricSummary` has no relationships.
- Power BI's Auto date/time option also created hidden `LocalDateTable_*` relationships for the date columns (`DimDate[date]`, `utc_period_end`, `utc_period_start`, `ref_period_start`). No measure uses them.

Units: WAPE, bias and change values are in percent (the DAX returns fractions formatted as %). pp values are percentage points. MAE is in MW.

### AECI

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,304 | 26,304 | 0.0e+00 | 26,304 | 0 | replica PASS; PBI PASS |
| Common Hours | 25,941 | 25,941 | 0.0e+00 | 25,941 | 0 | replica PASS; PBI PASS |
| Published WAPE (All Paired) % | 2.4811 | 2.4811 | 0.0e+00 | 2.481064 | 4.9e-07 | replica PASS; PBI PASS |
| Published MAE MW (All Paired) | 62.7344 | 62.7344 | 0.0e+00 | 62.734375 | 0.0e+00 | replica PASS; PBI PASS |
| Published Normalized Bias (All Paired) % | -0.0202 | -0.0202 | 6.6e-17 | -0.020152 | 2.5e-07 | replica PASS; PBI PASS |
| Published WAPE (Common) % | 2.4546 | 2.4546 | 0.0e+00 | 2.454570 | 1.0e-07 | replica PASS; PBI PASS |
| Published MAE MW (Common) | 62.0586 | 62.0586 | 0.0e+00 | 62.058556 | 4.6e-08 | replica PASS; PBI PASS |
| Published Normalized Bias (Common) % | -0.0527 | -0.0527 | 6.2e-17 | -0.052689 | 3.8e-07 | replica PASS; PBI PASS |
| Naive WAPE (Common) % | 17.5632 | 17.5632 | 0.0e+00 | 17.563231 | 4.3e-07 | replica PASS; PBI PASS |
| Naive MAE MW (Common) | 444.0487 | 444.0487 | 0.0e+00 | 444.048726 | 4.5e-08 | replica PASS; PBI PASS |
| Corrected WAPE (Common) % | 2.5229 | 2.5229 | 0.0e+00 | 2.522867 | 2.2e-07 | replica PASS; PBI PASS |
| Corrected MAE MW (Common) | 63.7853 | 63.7853 | 7.1e-15 | 63.785291 | 2.8e-07 | replica PASS; PBI PASS |
| Corrected Normalized Bias (Common) % | -0.0071 | -0.0071 | 2.9e-17 | -0.007090 | 2.2e-07 | replica PASS; PBI PASS |
| WAPE Change (pp) | 0.0683 | 0.0683 | 8.3e-17 | 0.068297 | 3.3e-07 | replica PASS; PBI PASS |
| WAPE Change (Relative) % | 2.7824 | 2.7824 | 0.0e+00 | 2.782429 | 1.1e-07 | replica PASS; PBI PASS |
| Peak WAPE (Actual-Defined) % | 1.9493 | 1.9493 | 0.0e+00 | 1.949326 | 3.4e-07 | replica PASS; PBI PASS |
| Worst 1% Error Contribution % | 6.2171 | 6.2171 | 0.0e+00 | 6.217136 | 1.4e-07 | replica PASS; PBI PASS |
| Quarters Improved | 1 | 1 | 0.0e+00 | 1 | 0 | replica PASS; PBI PASS |
| Years Improved | 0 | 0 | 0.0e+00 | 0 | 0 | replica PASS; PBI PASS |

### BPAT

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,304 | 26,304 | 0.0e+00 | 26,304 | 0 | replica PASS; PBI PASS |
| Common Hours | 25,941 | 25,941 | 0.0e+00 | 25,941 | 0 | replica PASS; PBI PASS |
| Published WAPE (All Paired) % | 1.9598 | 1.9598 | 0.0e+00 | 1.959794 | 4.9e-07 | replica PASS; PBI PASS |
| Published MAE MW (All Paired) | 135.5679 | 135.5679 | 0.0e+00 | 135.567898 | 4.2e-07 | replica PASS; PBI PASS |
| Published Normalized Bias (All Paired) % | -0.0618 | -0.0618 | 4.9e-17 | -0.061823 | 4.6e-07 | replica PASS; PBI PASS |
| Published WAPE (Common) % | 1.9636 | 1.9636 | 0.0e+00 | 1.963576 | 4.3e-08 | replica PASS; PBI PASS |
| Published MAE MW (Common) | 136.1365 | 136.1365 | 0.0e+00 | 136.136502 | 6.2e-08 | replica PASS; PBI PASS |
| Published Normalized Bias (Common) % | -0.0610 | -0.0610 | 9.0e-17 | -0.061001 | 5.0e-08 | replica PASS; PBI PASS |
| Naive WAPE (Common) % | 6.5013 | 6.5013 | 0.0e+00 | 6.501321 | 4.4e-07 | replica PASS; PBI PASS |
| Naive MAE MW (Common) | 450.7425 | 450.7425 | 0.0e+00 | 450.742493 | 4.2e-07 | replica PASS; PBI PASS |
| Corrected WAPE (Common) % | 1.9520 | 1.9520 | 2.2e-16 | 1.951972 | 1.6e-07 | replica PASS; PBI PASS |
| Corrected MAE MW (Common) | 135.3320 | 135.3320 | 0.0e+00 | 135.331972 | 2.2e-08 | replica PASS; PBI PASS |
| Corrected Normalized Bias (Common) % | 0.0068 | 0.0068 | 3.9e-17 | 0.006766 | 4.8e-07 | replica PASS; PBI PASS |
| WAPE Change (pp) | -0.0116 | -0.0116 | 2.8e-17 | -0.011604 | 2.1e-07 | replica PASS; PBI PASS |
| WAPE Change (Relative) % | -0.5910 | -0.5910 | 0.0e+00 | -0.590973 | 5.1e-08 | replica PASS; PBI PASS |
| Peak WAPE (Actual-Defined) % | 2.0983 | 2.0983 | 0.0e+00 | 2.098304 | 1.8e-07 | replica PASS; PBI PASS |
| Worst 1% Error Contribution % | 4.8312 | 4.8312 | 0.0e+00 | 4.831185 | 1.6e-07 | replica PASS; PBI PASS |
| Quarters Improved | 7 | 7 | 0.0e+00 | 7 | 0 | replica PASS; PBI PASS |
| Years Improved | 1 | 1 | 0.0e+00 | 1 | 0 | replica PASS; PBI PASS |

### ISNE

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,302 | 26,302 | 0.0e+00 | 26,302 | 0 | replica PASS; PBI PASS |
| Common Hours | 25,937 | 25,937 | 0.0e+00 | 25,937 | 0 | replica PASS; PBI PASS |
| Published WAPE (All Paired) % | 2.4934 | 2.4934 | 0.0e+00 | 2.493403 | 4.7e-08 | replica PASS; PBI PASS |
| Published MAE MW (All Paired) | 328.2638 | 328.2638 | 0.0e+00 | 328.263782 | 2.2e-07 | replica PASS; PBI PASS |
| Published Normalized Bias (All Paired) % | -1.7692 | -1.7692 | 2.2e-16 | -1.769237 | 3.2e-07 | replica PASS; PBI PASS |
| Published WAPE (Common) % | 2.4911 | 2.4911 | 4.4e-16 | 2.491102 | 1.8e-07 | replica PASS; PBI PASS |
| Published MAE MW (Common) | 327.3832 | 327.3832 | 0.0e+00 | 327.383159 | 1.9e-07 | replica PASS; PBI PASS |
| Published Normalized Bias (Common) % | -1.7743 | -1.7743 | 2.2e-16 | -1.774282 | 5.8e-08 | replica PASS; PBI PASS |
| Naive WAPE (Common) % | 11.0799 | 11.0799 | 0.0e+00 | 11.079886 | 3.9e-07 | replica PASS; PBI PASS |
| Naive MAE MW (Common) | 1456.1300 | 1456.1300 | 0.0e+00 | 1456.130046 | 1.2e-07 | replica PASS; PBI PASS |
| Corrected WAPE (Common) % | 1.7934 | 1.7934 | 0.0e+00 | 1.793359 | 4.6e-08 | replica PASS; PBI PASS |
| Corrected MAE MW (Common) | 235.6851 | 235.6851 | 0.0e+00 | 235.685075 | 3.1e-08 | replica PASS; PBI PASS |
| Corrected Normalized Bias (Common) % | -0.0134 | -0.0134 | 5.6e-17 | -0.013385 | 4.5e-07 | replica PASS; PBI PASS |
| WAPE Change (pp) | -0.6977 | -0.6977 | 0.0e+00 | -0.697743 | 1.3e-07 | replica PASS; PBI PASS |
| WAPE Change (Relative) % | -28.0094 | -28.0094 | 0.0e+00 | -28.009408 | 1.9e-07 | replica PASS; PBI PASS |
| Peak WAPE (Actual-Defined) % | 1.5374 | 1.5374 | 0.0e+00 | 1.537384 | 4.9e-07 | replica PASS; PBI PASS |
| Worst 1% Error Contribution % | 4.7586 | 4.7586 | 0.0e+00 | 4.758609 | 1.8e-07 | replica PASS; PBI PASS |
| Quarters Improved | 12 | 12 | 0.0e+00 | 12 | 0 | replica PASS; PBI PASS |
| Years Improved | 3 | 3 | 0.0e+00 | 3 | 0 | replica PASS; PBI PASS |

### PJM

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,183 | 26,183 | 0.0e+00 | 26,183 | 0 | replica PASS; PBI PASS |
| Common Hours | 25,704 | 25,704 | 0.0e+00 | 25,704 | 0 | replica PASS; PBI PASS |
| Published WAPE (All Paired) % | 3.4920 | 3.4920 | 0.0e+00 | 3.492002 | 7.2e-08 | replica PASS; PBI PASS |
| Published MAE MW (All Paired) | 3323.5097 | 3323.5097 | 0.0e+00 | 3323.509682 | 1.5e-07 | replica PASS; PBI PASS |
| Published Normalized Bias (All Paired) % | -1.4731 | -1.4731 | 0.0e+00 | -1.473119 | 4.4e-08 | replica PASS; PBI PASS |
| Published WAPE (Common) % | 3.4864 | 3.4864 | 0.0e+00 | 3.486399 | 3.2e-07 | replica PASS; PBI PASS |
| Published MAE MW (Common) | 3318.8786 | 3318.8786 | 0.0e+00 | 3318.878618 | 1.1e-07 | replica PASS; PBI PASS |
| Published Normalized Bias (Common) % | -1.4754 | -1.4754 | 2.2e-16 | -1.475369 | 5.6e-08 | replica PASS; PBI PASS |
| Naive WAPE (Common) % | 8.9804 | 8.9804 | 0.0e+00 | 8.980422 | 2.9e-07 | replica PASS; PBI PASS |
| Naive MAE MW (Common) | 8548.9160 | 8548.9160 | 0.0e+00 | 8548.916044 | 2.0e-07 | replica PASS; PBI PASS |
| Corrected WAPE (Common) % | 2.1115 | 2.1115 | 0.0e+00 | 2.111462 | 4.5e-07 | replica PASS; PBI PASS |
| Corrected MAE MW (Common) | 2010.0067 | 2010.0067 | 0.0e+00 | 2010.006666 | 3.2e-07 | replica PASS; PBI PASS |
| Corrected Normalized Bias (Common) % | -0.0034 | -0.0034 | 5.1e-17 | -0.003368 | 4.7e-07 | replica PASS; PBI PASS |
| WAPE Change (pp) | -1.3749 | -1.3749 | 0.0e+00 | -1.374937 | 1.3e-07 | replica PASS; PBI PASS |
| WAPE Change (Relative) % | -39.4372 | -39.4372 | 0.0e+00 | -39.437174 | 4.9e-07 | replica PASS; PBI PASS |
| Peak WAPE (Actual-Defined) % | 3.3313 | 3.3313 | 0.0e+00 | 3.331274 | 3.2e-07 | replica PASS; PBI PASS |
| Worst 1% Error Contribution % | 3.8617 | 3.8617 | 0.0e+00 | 3.861732 | 1.2e-07 | replica PASS; PBI PASS |
| Quarters Improved | 12 | 12 | 0.0e+00 | 12 | 0 | replica PASS; PBI PASS |
| Years Improved | 3 | 3 | 0.0e+00 | 3 | 0 | replica PASS; PBI PASS |

### PNM

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,304 | 26,304 | 0.0e+00 | 26,304 | 0 | replica PASS; PBI PASS |
| Common Hours | 25,944 | 25,944 | 0.0e+00 | 25,944 | 0 | replica PASS; PBI PASS |
| Published WAPE (All Paired) % | 6.0897 | 6.0897 | 0.0e+00 | 6.089716 | 1.6e-07 | replica PASS; PBI PASS |
| Published MAE MW (All Paired) | 102.4970 | 102.4970 | 1.4e-14 | 102.496959 | 3.6e-07 | replica PASS; PBI PASS |
| Published Normalized Bias (All Paired) % | -5.8416 | -5.8416 | 8.9e-16 | -5.841586 | 3.4e-07 | replica PASS; PBI PASS |
| Published WAPE (Common) % | 6.0940 | 6.0940 | 0.0e+00 | 6.094044 | 2.9e-07 | replica PASS; PBI PASS |
| Published MAE MW (Common) | 102.5033 | 102.5033 | 0.0e+00 | 102.503276 | 2.9e-07 | replica PASS; PBI PASS |
| Published Normalized Bias (Common) % | -5.8437 | -5.8437 | 8.9e-16 | -5.843654 | 3.2e-07 | replica PASS; PBI PASS |
| Naive WAPE (Common) % | 6.3924 | 6.3924 | 0.0e+00 | 6.392370 | 2.1e-07 | replica PASS; PBI PASS |
| Naive MAE MW (Common) | 107.5212 | 107.5212 | 1.4e-14 | 107.521200 | 4.9e-07 | replica PASS; PBI PASS |
| Corrected WAPE (Common) % | 2.4877 | 2.4877 | 0.0e+00 | 2.487670 | 4.7e-07 | replica PASS; PBI PASS |
| Corrected MAE MW (Common) | 41.8432 | 41.8432 | 7.1e-15 | 41.843214 | 2.3e-07 | replica PASS; PBI PASS |
| Corrected Normalized Bias (Common) % | 0.0045 | 0.0045 | 3.5e-18 | 0.004502 | 4.2e-07 | replica PASS; PBI PASS |
| WAPE Change (pp) | -3.6064 | -3.6064 | 4.4e-16 | -3.606373 | 2.4e-07 | replica PASS; PBI PASS |
| WAPE Change (Relative) % | -59.1787 | -59.1787 | 0.0e+00 | -59.178657 | 2.3e-07 | replica PASS; PBI PASS |
| Peak WAPE (Actual-Defined) % | 5.6642 | 5.6642 | 0.0e+00 | 5.664179 | 4.1e-07 | replica PASS; PBI PASS |
| Worst 1% Error Contribution % | 2.9323 | 2.9323 | 0.0e+00 | 2.932294 | 2.9e-07 | replica PASS; PBI PASS |
| Quarters Improved | 12 | 12 | 0.0e+00 | 12 | 0 | replica PASS; PBI PASS |
| Years Improved | 3 | 3 | 0.0e+00 | 3 | 0 | replica PASS; PBI PASS |

### PSCO

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,283 | 26,283 | 0.0e+00 | 26,283 | 0 | replica PASS; PBI PASS |
| Common Hours | 25,905 | 25,905 | 0.0e+00 | 25,905 | 0 | replica PASS; PBI PASS |
| Published WAPE (All Paired) % | 10.3647 | 10.3647 | 0.0e+00 | 10.364680 | 3.6e-07 | replica PASS; PBI PASS |
| Published MAE MW (All Paired) | 541.5454 | 541.5454 | 0.0e+00 | 541.545410 | 4.2e-07 | replica PASS; PBI PASS |
| Published Normalized Bias (All Paired) % | -9.4313 | -9.4313 | 1.8e-15 | -9.431302 | 2.9e-07 | replica PASS; PBI PASS |
| Published WAPE (Common) % | 10.4287 | 10.4287 | 0.0e+00 | 10.428718 | 1.5e-07 | replica PASS; PBI PASS |
| Published MAE MW (Common) | 545.0286 | 545.0286 | 0.0e+00 | 545.028643 | 1.2e-07 | replica PASS; PBI PASS |
| Published Normalized Bias (Common) % | -9.5304 | -9.5304 | 1.8e-15 | -9.530406 | 3.7e-08 | replica PASS; PBI PASS |
| Naive WAPE (Common) % | 9.0966 | 9.0966 | 0.0e+00 | 9.096561 | 3.3e-08 | replica PASS; PBI PASS |
| Naive MAE MW (Common) | 475.4071 | 475.4071 | 0.0e+00 | 475.407064 | 2.7e-07 | replica PASS; PBI PASS |
| Corrected WAPE (Common) % | 4.6088 | 4.6088 | 8.9e-16 | 4.608807 | 4.9e-08 | replica PASS; PBI PASS |
| Corrected MAE MW (Common) | 240.8668 | 240.8668 | 2.8e-14 | 240.866789 | 2.6e-07 | replica PASS; PBI PASS |
| Corrected Normalized Bias (Common) % | -0.3910 | -0.3910 | 1.1e-16 | -0.390955 | 3.1e-07 | replica PASS; PBI PASS |
| WAPE Change (pp) | -5.8199 | -5.8199 | 8.9e-16 | -5.819911 | 1.0e-07 | replica PASS; PBI PASS |
| WAPE Change (Relative) % | -55.8066 | -55.8066 | 2.8e-14 | -55.806582 | 4.2e-07 | replica PASS; PBI PASS |
| Peak WAPE (Actual-Defined) % | 16.3444 | 16.3444 | 0.0e+00 | 16.344415 | 1.6e-07 | replica PASS; PBI PASS |
| Worst 1% Error Contribution % | 5.9092 | 5.9092 | 0.0e+00 | 5.909170 | 3.4e-07 | replica PASS; PBI PASS |
| Quarters Improved | 12 | 12 | 0.0e+00 | 12 | 0 | replica PASS; PBI PASS |
| Years Improved | 3 | 3 | 0.0e+00 | 3 | 0 | replica PASS; PBI PASS |

### SOCO

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,298 | 26,298 | 0.0e+00 | 26,298 | 0 | replica PASS; PBI PASS |
| Common Hours | 25,932 | 25,932 | 0.0e+00 | 25,932 | 0 | replica PASS; PBI PASS |
| Published WAPE (All Paired) % | 1.4706 | 1.4706 | 0.0e+00 | 1.470581 | 2.3e-08 | replica PASS; PBI PASS |
| Published MAE MW (All Paired) | 404.0925 | 404.0925 | 0.0e+00 | 404.092517 | 4.6e-07 | replica PASS; PBI PASS |
| Published Normalized Bias (All Paired) % | -1.2881 | -1.2881 | 2.2e-16 | -1.288098 | 1.7e-07 | replica PASS; PBI PASS |
| Published WAPE (Common) % | 1.4646 | 1.4646 | 0.0e+00 | 1.464550 | 2.2e-07 | replica PASS; PBI PASS |
| Published MAE MW (Common) | 402.0823 | 402.0823 | 0.0e+00 | 402.082331 | 2.9e-07 | replica PASS; PBI PASS |
| Published Normalized Bias (Common) % | -1.2794 | -1.2794 | 0.0e+00 | -1.279373 | 4.5e-07 | replica PASS; PBI PASS |
| Naive WAPE (Common) % | 10.7387 | 10.7387 | 0.0e+00 | 10.738658 | 1.8e-07 | replica PASS; PBI PASS |
| Naive MAE MW (Common) | 2948.2258 | 2948.2258 | 0.0e+00 | 2948.225783 | 1.8e-07 | replica PASS; PBI PASS |
| Corrected WAPE (Common) % | 0.6567 | 0.6567 | 0.0e+00 | 0.656703 | 5.0e-07 | replica PASS; PBI PASS |
| Corrected MAE MW (Common) | 180.2935 | 180.2935 | 2.8e-14 | 180.293492 | 3.0e-08 | replica PASS; PBI PASS |
| Corrected Normalized Bias (Common) % | 0.0009 | 0.0009 | 7.3e-17 | 0.000859 | 1.7e-07 | replica PASS; PBI PASS |
| WAPE Change (pp) | -0.8078 | -0.8078 | 0.0e+00 | -0.807847 | 2.8e-07 | replica PASS; PBI PASS |
| WAPE Change (Relative) % | -55.1601 | -55.1601 | 0.0e+00 | -55.160056 | 1.1e-08 | replica PASS; PBI PASS |
| Peak WAPE (Actual-Defined) % | 1.1998 | 1.1998 | 2.2e-16 | 1.199834 | 2.1e-07 | replica PASS; PBI PASS |
| Worst 1% Error Contribution % | 5.1914 | 5.1914 | 0.0e+00 | 5.191428 | 3.0e-07 | replica PASS; PBI PASS |
| Quarters Improved | 12 | 12 | 0.0e+00 | 12 | 0 | replica PASS; PBI PASS |
| Years Improved | 3 | 3 | 0.0e+00 | 3 | 0 | replica PASS; PBI PASS |

### TVA

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,300 | 26,300 | 0.0e+00 | 26,300 | 0 | replica PASS; PBI PASS |
| Common Hours | 25,933 | 25,933 | 0.0e+00 | 25,933 | 0 | replica PASS; PBI PASS |
| Published WAPE (All Paired) % | 2.3179 | 2.3179 | 0.0e+00 | 2.317869 | 3.0e-07 | replica PASS; PBI PASS |
| Published MAE MW (All Paired) | 444.6771 | 444.6771 | 0.0e+00 | 444.677110 | 2.7e-07 | replica PASS; PBI PASS |
| Published Normalized Bias (All Paired) % | 1.1070 | 1.1070 | 0.0e+00 | 1.106990 | 3.4e-07 | replica PASS; PBI PASS |
| Published WAPE (Common) % | 2.3181 | 2.3181 | 0.0e+00 | 2.318060 | 4.9e-08 | replica PASS; PBI PASS |
| Published MAE MW (Common) | 444.6937 | 444.6937 | 0.0e+00 | 444.693672 | 1.6e-07 | replica PASS; PBI PASS |
| Published Normalized Bias (Common) % | 1.1257 | 1.1257 | 0.0e+00 | 1.125672 | 2.2e-07 | replica PASS; PBI PASS |
| Naive WAPE (Common) % | 12.2168 | 12.2168 | 0.0e+00 | 12.216803 | 3.3e-07 | replica PASS; PBI PASS |
| Naive MAE MW (Common) | 2343.6559 | 2343.6559 | 0.0e+00 | 2343.655882 | 4.7e-07 | replica PASS; PBI PASS |
| Corrected WAPE (Common) % | 2.2664 | 2.2664 | 4.4e-16 | 2.266406 | 4.7e-07 | replica PASS; PBI PASS |
| Corrected MAE MW (Common) | 434.7844 | 434.7844 | 5.7e-14 | 434.784354 | 4.1e-07 | replica PASS; PBI PASS |
| Corrected Normalized Bias (Common) % | 0.0201 | 0.0201 | 5.2e-17 | 0.020074 | 1.3e-07 | replica PASS; PBI PASS |
| WAPE Change (pp) | -0.0517 | -0.0517 | 4.3e-16 | -0.051654 | 4.2e-07 | replica PASS; PBI PASS |
| WAPE Change (Relative) % | -2.2283 | -2.2283 | 2.2e-14 | -2.228347 | 1.0e-07 | replica PASS; PBI PASS |
| Peak WAPE (Actual-Defined) % | 2.4585 | 2.4585 | 0.0e+00 | 2.458493 | 2.9e-07 | replica PASS; PBI PASS |
| Worst 1% Error Contribution % | 6.2654 | 6.2654 | 0.0e+00 | 6.265357 | 2.0e-08 | replica PASS; PBI PASS |
| Quarters Improved | 10 | 10 | 0.0e+00 | 10 | 0 | replica PASS; PBI PASS |
| Years Improved | 3 | 3 | 0.0e+00 | 3 | 0 | replica PASS; PBI PASS |

## Report page check (2026-09-26, re-checked twice on 2026-09-28)

The report "Demand Forecast Performance Review" was built in the Power BI Service on this model, with two pages. Values were read off the rendered visuals and compared with the tables above. No DAX was changed for the report build; one display-only measure was added later (see the end of this section).

| Check | Rendered value | Expected | Result |
|---|---|---|---|
| Page 1 cards, category slicer = All | 3.83% · 2.62% · 2.30% · −1.54 pp · −40.1% · 210K · 8 | 3.83% · 2.62% · 2.30% · −1.54 pp · −40.1% · 210,278 · 8 | match (Paired Hours card uses auto display units; the exact 210,278 comes from DAX) |
| Page 1 cards, category = A (ISNE, PJM, SOCO) | BAs in view 3 · corrected 1.52% · −0.96 pp · −38.7% | mean of the three BAs' values; relative = corrected avg ÷ published avg − 1 | match |
| Page 1 attention table, all 8 rows | per-BA WAPE, bias, corrected WAPE, pp and relative change, quarters improved | per-BA tables above | match; PNM and PSCO show SOURCE SEMANTICS UNCERTAIN in the row |
| Page 1 WAPE bar chart | `… (Common)` measures only | common comparison hours | match |
| Page 2, ISNE | naive 11.08% · published 2.49% · corrected 1.79%; Q1 bias −4.02% | ISNE table above | match |
| Page 2, PNM | naive 6.39% · published 6.09% · corrected 2.49%; status and note show the source-semantics warning | PNM table above | match |
| AECI `Years Improved` | not placed on a page; 0 in DAX query view after the `+ 0` fix | 0 | match |

After the 2026-09-28 presentation changes (headline, zero line, card titles, table layout), the Page 1 cards still show 3.83% · 2.62% · 2.30% · −1.54 pp · −40.1% · 210K · 8. The attention table still shows the per-BA values above, and Page 2 for ISNE still shows 11.08% · 2.49% · 1.79%. No measure was changed.

A second presentation pass on 2026-09-28 changed slicer headers, card subtitles and series colours, and added one display-only measure, `Source Semantics Note Display`, which wraps the existing `Source Semantics Note` (see `docs/dax_measures.md`). No reconciled measure was changed. Re-check after that pass:

| Check | Rendered value | Result |
|---|---|---|
| Page 1 cards, category = All | 3.83% · 2.62% · 2.30% · −1.54 pp · −40.1% · 210K · 8 | match |
| Page 2, ISNE benchmark chart | naive 11.08% · published 2.49% · corrected 1.79% | match |
| Page 2, ISNE note | "No source-semantics exception flagged." | as intended |
| Page 2, PNM note | "SOURCE SEMANTICS UNCERTAIN." + full caution text; status row still shows SOURCE SEMANTICS UNCERTAIN | as intended |
