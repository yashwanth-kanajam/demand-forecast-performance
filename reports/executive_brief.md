# Executive Brief: Demand Forecast Performance & Operational Exceptions

*Independent analysis of public data. No client, stakeholder or operational use is implied.*

## Management question

How reliable are the day-ahead demand forecasts that balancing authorities (BAs) already publish, where do their errors follow a stable pattern, and which of those errors would a simple historical correction reduce without replacing the incumbent forecast?

## Scope

- **Data:** U.S. EIA Form EIA-930: hourly actual demand and the published day-ahead demand forecast, retrieved 2026-09-24.
- **Period:** 36 complete months (September 2023 – August 2026), 26,304 hourly observations per BA.
- **Population:** 8 BAs: AECI, BPAT, ISNE, PJM, PNM, PSCO, SOCO, TVA. They were drawn from 50 BAs that passed a ≥95% actual, forecast and paired-coverage gate, and chosen on reporting stability and diversity before any error metric was computed.
- **Benchmarks:** a seasonal naive forecast (same reporting-clock hour one week earlier) and a strictly causal trailing correction (mean residual by BA × hour over days D−29 to D−2). All three forecasts are scored on identical hours.

## Findings

1. **The incumbent forecasts carry real skill.** For 6 of 8 BAs the published forecast removes 61–86% of seasonal-naive error.
2. **Error is not equally correctable.** ISNE, PJM and SOCO show persistent underforecast bias of 1.3–1.8% of demand, and the causal correction reduced WAPE in all 12 quarters (published → corrected WAPE on common hours):
   - PJM 3.49% → 2.11% (−1.37 pp; −39.4%);
   - SOCO 1.46% → 0.66% (−0.81 pp; −55.2%);
   - ISNE 2.49% → 1.79% (−0.70 pp; −28.0%).
3. **Aggregate accuracy hides hour-level bias.** ISNE underforecasts by 3–6% overnight (00:00–05:00). PJM underforecasts late evening and overnight and overforecasts around 05:00–06:00. Both patterns hold in every year. SOCO's bias is broadly uniform across hours.
4. **Correction adds little where bias is absent or small.**
   - AECI and BPAT are effectively unbiased (−0.02%, −0.06%). The correction moves WAPE 2.45% → 2.52% (+0.07 pp; +2.8%, worse in all three years) and 1.96% → 1.95% (−0.01 pp; −0.6%).
   - TVA has persistent +1.1% overforecast, but correcting it moves WAPE only 2.32% → 2.27% (−0.05 pp; −2.2%).

## Category interpretation

| Category | BAs | Reading |
|---|---|---|
| Systematic and correctable | ISNE, PJM, SOCO | Stable directional error; the causal correction helped in every quarter |
| Apparently correctable — **SOURCE SEMANTICS UNCERTAIN** | PNM, PSCO | Large level offset in the reported series (−5.8%, −9.4%); not used as evidence |
| Persistent bias — low correction benefit | TVA | Bias is real but small relative to total error |
| Little/no correctable bias | AECI, BPAT | Keep the incumbent as is |

PNM and PSCO: the reported forecast series contains a persistent level discrepancy, but available EIA metadata does not resolve whether this reflects forecast-process bias, reporting-scope differences, resubmission behaviour, or another source-definition effect. EIA notes that for some BAs the actual-vs-forecast comparison "is not very meaningful". Mathematical correctability in the reported series does not establish forecast-process failure.

## Recommended analytical response

- Retain the incumbent forecast where correction is small or unstable (AECI, BPAT, TVA).
- Consider targeted bias recalibration where improvement is persistent (ISNE, PJM, SOCO). Report corrected and incumbent performance side by side over a further out-of-sample period before any operational use.
- Monitor recurring hour-specific bias separately from aggregate WAPE.
- Keep source-semantic anomalies (PNM, PSCO) out of forecast-performance conclusions until series definitions are confirmed.

## Limitations

- EIA revises data in place, and forecast vintage and resubmissions are not observable.
- The 8 BAs were selected on reporting quality; Texas and California are not represented.
- PJM's DST transition days are blank in the source.
- Seasonal statements rest on three annual cycles.
- The 5% practical-improvement rule is project-defined, not an industry standard.
- No cost, reliability or operational impact is estimated.
