# Power BI Reconciliation

**Status: Power BI values PENDING.** The report has not been assembled: browser automation cannot operate the Power BI web modeling surface, and nothing in this file claims a Power BI result.

What is verified:
- **Python reference:** `data/bi/ba_metric_summary.csv`, produced by the Phase 2.5 pipeline.
- **DAX-logic replica:** `src/dfp/bi_replica.py`. It recomputes every **[R]** measure in `docs/dax_measures.md` from the handoff CSVs (`data/bi/*.csv`), using the same filters, populations, tie-breaking and quarter iteration as the DAX. This checks the handoff files and the measure logic, not Power BI itself.
- **Test:** `tests/test_analysis_outputs.py::test_dax_logic_replica_reproduces_reference_values` (tolerance 1e-9 relative). It passed; the largest absolute difference across all measures and BAs was 5.7e-14.

## Procedure once the report is assembled

1. Build a table visual with `DimBA[ba_code]` plus every measure listed below. No slicers or page filters.
2. Copy each value into the *Power BI result* column. Use the displayed precision (set 4 decimals on the measures for this check).
3. **PASS** if |Power BI − reference| ≤ 0.0001 for percentages, MW and pp; exact for counts. Anything else is a **FAIL** and must be explained before publishing.

Tolerance rationale: values are shown at 4 decimals, and double-precision summation order in VertiPaq can differ from pandas by far less than that.

Units: WAPE, bias and change values are in percent (the DAX returns fractions formatted as %). pp values are percentage points. MAE is in MW.

### AECI

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,304 | 26,304 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Common Hours | 25,941 | 25,941 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (All Paired) % | 2.4811 | 2.4811 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (All Paired) | 62.7344 | 62.7344 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (All Paired) % | -0.0202 | -0.0202 | 6.6e-17 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (Common) % | 2.4546 | 2.4546 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (Common) | 62.0586 | 62.0586 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (Common) % | -0.0527 | -0.0527 | 6.2e-17 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive WAPE (Common) % | 17.5632 | 17.5632 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive MAE MW (Common) | 444.0487 | 444.0487 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected WAPE (Common) % | 2.5229 | 2.5229 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected MAE MW (Common) | 63.7853 | 63.7853 | 7.1e-15 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected Normalized Bias (Common) % | -0.0071 | -0.0071 | 2.9e-17 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (pp) | 0.0683 | 0.0683 | 8.3e-17 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (Relative) % | 2.7824 | 2.7824 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Peak WAPE (Actual-Defined) % | 1.9493 | 1.9493 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Worst 1% Error Contribution % | 6.2171 | 6.2171 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Quarters Improved | 1 | 1 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Years Improved | 0 | 0 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |

### BPAT

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,304 | 26,304 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Common Hours | 25,941 | 25,941 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (All Paired) % | 1.9598 | 1.9598 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (All Paired) | 135.5679 | 135.5679 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (All Paired) % | -0.0618 | -0.0618 | 4.9e-17 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (Common) % | 1.9636 | 1.9636 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (Common) | 136.1365 | 136.1365 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (Common) % | -0.0610 | -0.0610 | 9.0e-17 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive WAPE (Common) % | 6.5013 | 6.5013 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive MAE MW (Common) | 450.7425 | 450.7425 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected WAPE (Common) % | 1.9520 | 1.9520 | 2.2e-16 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected MAE MW (Common) | 135.3320 | 135.3320 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected Normalized Bias (Common) % | 0.0068 | 0.0068 | 3.9e-17 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (pp) | -0.0116 | -0.0116 | 2.8e-17 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (Relative) % | -0.5910 | -0.5910 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Peak WAPE (Actual-Defined) % | 2.0983 | 2.0983 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Worst 1% Error Contribution % | 4.8312 | 4.8312 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Quarters Improved | 7 | 7 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Years Improved | 1 | 1 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |

### ISNE

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,302 | 26,302 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Common Hours | 25,937 | 25,937 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (All Paired) % | 2.4934 | 2.4934 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (All Paired) | 328.2638 | 328.2638 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (All Paired) % | -1.7692 | -1.7692 | 2.2e-16 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (Common) % | 2.4911 | 2.4911 | 4.4e-16 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (Common) | 327.3832 | 327.3832 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (Common) % | -1.7743 | -1.7743 | 2.2e-16 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive WAPE (Common) % | 11.0799 | 11.0799 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive MAE MW (Common) | 1456.1300 | 1456.1300 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected WAPE (Common) % | 1.7934 | 1.7934 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected MAE MW (Common) | 235.6851 | 235.6851 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected Normalized Bias (Common) % | -0.0134 | -0.0134 | 5.6e-17 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (pp) | -0.6977 | -0.6977 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (Relative) % | -28.0094 | -28.0094 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Peak WAPE (Actual-Defined) % | 1.5374 | 1.5374 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Worst 1% Error Contribution % | 4.7586 | 4.7586 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Quarters Improved | 12 | 12 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Years Improved | 3 | 3 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |

### PJM

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,183 | 26,183 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Common Hours | 25,704 | 25,704 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (All Paired) % | 3.4920 | 3.4920 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (All Paired) | 3323.5097 | 3323.5097 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (All Paired) % | -1.4731 | -1.4731 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (Common) % | 3.4864 | 3.4864 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (Common) | 3318.8786 | 3318.8786 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (Common) % | -1.4754 | -1.4754 | 2.2e-16 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive WAPE (Common) % | 8.9804 | 8.9804 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive MAE MW (Common) | 8548.9160 | 8548.9160 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected WAPE (Common) % | 2.1115 | 2.1115 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected MAE MW (Common) | 2010.0067 | 2010.0067 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected Normalized Bias (Common) % | -0.0034 | -0.0034 | 5.1e-17 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (pp) | -1.3749 | -1.3749 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (Relative) % | -39.4372 | -39.4372 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Peak WAPE (Actual-Defined) % | 3.3313 | 3.3313 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Worst 1% Error Contribution % | 3.8617 | 3.8617 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Quarters Improved | 12 | 12 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Years Improved | 3 | 3 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |

### PNM

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,304 | 26,304 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Common Hours | 25,944 | 25,944 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (All Paired) % | 6.0897 | 6.0897 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (All Paired) | 102.4970 | 102.4970 | 1.4e-14 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (All Paired) % | -5.8416 | -5.8416 | 8.9e-16 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (Common) % | 6.0940 | 6.0940 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (Common) | 102.5033 | 102.5033 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (Common) % | -5.8437 | -5.8437 | 8.9e-16 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive WAPE (Common) % | 6.3924 | 6.3924 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive MAE MW (Common) | 107.5212 | 107.5212 | 1.4e-14 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected WAPE (Common) % | 2.4877 | 2.4877 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected MAE MW (Common) | 41.8432 | 41.8432 | 7.1e-15 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected Normalized Bias (Common) % | 0.0045 | 0.0045 | 3.5e-18 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (pp) | -3.6064 | -3.6064 | 4.4e-16 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (Relative) % | -59.1787 | -59.1787 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Peak WAPE (Actual-Defined) % | 5.6642 | 5.6642 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Worst 1% Error Contribution % | 2.9323 | 2.9323 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Quarters Improved | 12 | 12 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Years Improved | 3 | 3 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |

### PSCO

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,283 | 26,283 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Common Hours | 25,905 | 25,905 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (All Paired) % | 10.3647 | 10.3647 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (All Paired) | 541.5454 | 541.5454 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (All Paired) % | -9.4313 | -9.4313 | 1.8e-15 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (Common) % | 10.4287 | 10.4287 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (Common) | 545.0286 | 545.0286 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (Common) % | -9.5304 | -9.5304 | 1.8e-15 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive WAPE (Common) % | 9.0966 | 9.0966 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive MAE MW (Common) | 475.4071 | 475.4071 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected WAPE (Common) % | 4.6088 | 4.6088 | 8.9e-16 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected MAE MW (Common) | 240.8668 | 240.8668 | 2.8e-14 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected Normalized Bias (Common) % | -0.3910 | -0.3910 | 1.1e-16 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (pp) | -5.8199 | -5.8199 | 8.9e-16 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (Relative) % | -55.8066 | -55.8066 | 2.8e-14 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Peak WAPE (Actual-Defined) % | 16.3444 | 16.3444 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Worst 1% Error Contribution % | 5.9092 | 5.9092 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Quarters Improved | 12 | 12 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Years Improved | 3 | 3 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |

### SOCO

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,298 | 26,298 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Common Hours | 25,932 | 25,932 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (All Paired) % | 1.4706 | 1.4706 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (All Paired) | 404.0925 | 404.0925 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (All Paired) % | -1.2881 | -1.2881 | 2.2e-16 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (Common) % | 1.4646 | 1.4646 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (Common) | 402.0823 | 402.0823 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (Common) % | -1.2794 | -1.2794 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive WAPE (Common) % | 10.7387 | 10.7387 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive MAE MW (Common) | 2948.2258 | 2948.2258 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected WAPE (Common) % | 0.6567 | 0.6567 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected MAE MW (Common) | 180.2935 | 180.2935 | 2.8e-14 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected Normalized Bias (Common) % | 0.0009 | 0.0009 | 7.3e-17 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (pp) | -0.8078 | -0.8078 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (Relative) % | -55.1601 | -55.1601 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Peak WAPE (Actual-Defined) % | 1.1998 | 1.1998 | 2.2e-16 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Worst 1% Error Contribution % | 5.1914 | 5.1914 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Quarters Improved | 12 | 12 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Years Improved | 3 | 3 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |

### TVA

| Measure | Python reference | DAX-logic replica (from BI CSVs) | Replica diff | Power BI result | PBI diff | Status |
|---|--:|--:|--:|--:|--:|---|
| Paired Hours | 26,300 | 26,300 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Common Hours | 25,933 | 25,933 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (All Paired) % | 2.3179 | 2.3179 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (All Paired) | 444.6771 | 444.6771 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (All Paired) % | 1.1070 | 1.1070 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published WAPE (Common) % | 2.3181 | 2.3181 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published MAE MW (Common) | 444.6937 | 444.6937 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Published Normalized Bias (Common) % | 1.1257 | 1.1257 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive WAPE (Common) % | 12.2168 | 12.2168 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Naive MAE MW (Common) | 2343.6559 | 2343.6559 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected WAPE (Common) % | 2.2664 | 2.2664 | 4.4e-16 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected MAE MW (Common) | 434.7844 | 434.7844 | 5.7e-14 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Corrected Normalized Bias (Common) % | 0.0201 | 0.0201 | 5.2e-17 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (pp) | -0.0517 | -0.0517 | 4.3e-16 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| WAPE Change (Relative) % | -2.2283 | -2.2283 | 2.2e-14 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Peak WAPE (Actual-Defined) % | 2.4585 | 2.4585 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Worst 1% Error Contribution % | 6.2654 | 6.2654 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Quarters Improved | 10 | 10 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
| Years Improved | 3 | 3 | 0.0e+00 | _pending_ | _pending_ | replica PASS; PBI PENDING |
