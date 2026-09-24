# Executive Brief (Draft): Demand Forecast Performance & Operational Exceptions

*Independent analysis of public data. No client, stakeholder or operational use is implied.*

## 1. Management question

How reliable are the day-ahead demand forecasts that balancing authorities already publish, where do they fail systematically, and which errors are stable enough that a simple historical correction would reduce them?

## 2. Scope

- **Data:** U.S. EIA Form EIA-930: hourly actual demand and the published day-ahead demand forecast, retrieved 2026-09-24.
- **Period:** 36 complete months (Sep 2023 – Aug 2026) in each BA's reporting clock, anchored on UTC hours.
- **Population:** 8 balancing authorities (AECI, BPAT, ISNE, PJM, PNM, PSCO, SOCO, TVA). They were chosen *before* any error metric was computed, from 50 BAs passing a ≥95% actual/forecast/paired coverage gate, on reporting stability and diversity.
- **Benchmarks:** seasonal naive (same reporting-clock hour, 7 days earlier) and a strictly causal trailing correction (mean residual by BA × hour over days D−29 to D−2). All three are compared on identical hours.

## 3. Findings

1. **The incumbent forecasts are informative.** For 6 of 8 BAs the published forecast removes 61–86% of seasonal-naive error. The exceptions are PNM (5%) and PSCO (−15%; worse than naive in the final year).
2. **Error is not equally correctable.** ISNE, PJM and SOCO carry persistent directional underforecast bias (−1.3% to −1.8% of demand). The causal correction reduced WAPE in all 12 quarters:
   - ISNE −0.70 pp (−28%);
   - PJM −1.37 pp (−39%);
   - SOCO −0.81 pp (−55%).
3. **The shape of the bias differs.** ISNE and PJM are hour-structured: ISNE underforecasts by 3–6% overnight (h00–05), and PJM underforecasts at h20–03 while overforecasting at h05–06. SOCO's bias is close to uniform across hours. An aggregate WAPE of 1.5–3.5% hides these hour-level patterns.
4. **Little benefit where bias is absent or small.** AECI and BPAT are effectively unbiased (−0.02%, −0.06%); the correction changes WAPE by +0.07 pp (+2.8%, worse in all three years) and −0.01 pp (−0.6%). TVA has persistent +1.1% overforecast, but correcting it moves WAPE only −0.05 pp (−2.2%).

Extreme hours do not dominate error for any BA: the worst 1% of hours carry 2.9–6.3% of absolute error.

## 4. Correctable vs non-correctable

| Group | BAs | Pattern | Correction effect (common hours) |
|---|---|---|---|
| A. Systematic and correctable | ISNE, PJM, SOCO | stable directional bias (hour-structured for ISNE and PJM; near-uniform for SOCO) | −0.70 to −1.37 pp; 12/12 quarters |
| B. Apparently correctable, source semantics uncertain | PNM, PSCO | large level offset in the reported series | −3.61 pp (PNM), −5.82 pp (PSCO); 12/12 quarters |
| C. Persistent bias, low correction benefit | TVA | small uniform overforecast | −0.05 pp; 10/12 quarters |
| D. Little/no correctable bias | AECI, BPAT | near-zero bias | +0.07 pp / −0.01 pp |

## 5. Source-semantic caution (PNM, PSCO)

The reported forecast series for PNM (−5.8%) and PSCO (−9.4%, widening since January 2026) shows a persistent level offset. Available EIA metadata does not resolve whether this reflects forecast-process bias, reporting-scope differences, resubmission behavior, or another source-definition effect.

EIA itself notes that forecasts follow each BA's operating accounting and that for some BAs the actual-vs-forecast comparison "is not very meaningful". These two BAs are therefore not used as evidence for the main finding. See `docs/source_semantics_audit.md`.

## 6. Recommended monitoring response

- Retain the incumbent forecast where correction does not help consistently (AECI, BPAT, TVA).
- Consider targeted bias recalibration where improvement is persistent (ISNE, PJM, SOCO), after comparing corrected and incumbent performance side by side over a further out-of-sample period.
- Monitor recurring hour-specific bias (ISNE overnight; PJM late evening and overnight) separately from aggregate WAPE.
- Keep source-semantic anomalies (PNM, PSCO) separate from forecast-performance conclusions until the series definitions are confirmed.

## 7. Limitations

- EIA revises data in place, and forecast vintage and resubmissions are not observable. The correction assumes the forecast is issued on the prior day.
- The 8 BAs were selected on data quality, which may favour well-run reporting. Texas and California are not represented.
- PJM's DST transition days are blank in the source. EIA notes DST days are often misreported.
- Seasonal statements rest on three annual cycles.
- The 5% practical-improvement rule is project-defined, not an industry standard.
- No cost, reliability or operational impact is estimated.
