# Forecast Performance Analysis: Metrics, Benchmarks and Correctability

Run 2026-09-24 on the source files pinned in `data/curated/run_manifest.json`. Definitions and thresholds are in `docs/metric_catalogue.md` and were fixed before any result was computed.

**Sign conventions:** error e = forecast − actual (positive = overforecast, negative = underforecast). The correction adds the trailing mean residual (actual − forecast) to the published forecast.

Sample sizes: 26,183–26,304 paired hours per BA, and 25,704–25,944 common-set hours per BA. The common set excludes the first 15 days of September 2023 (correction warm-up) and hours where any of the three forecasts is missing.

## 1. BA overall (published forecast, paired set)

| BA | Median demand MW | Paired N | WAPE % | MAE MW | Norm. bias % | High-demand WAPE % | Worst-1% share % |
|---|--:|--:|--:|--:|--:|--:|--:|
| PNM | 1,627 | 26,304 | 6.09 | 102.5 | −5.84 | 5.66 | 2.93 |
| AECI | 2,337 | 26,304 | 2.48 | 62.7 | −0.02 | 1.95 | 6.22 |
| PSCO | 5,070 | 26,283 | 10.36 | 541.5 | −9.43 | 16.34 | 5.91 |
| BPAT | 6,830 | 26,304 | 1.96 | 135.6 | −0.06 | 2.10 | 4.83 |
| ISNE | 12,866 | 26,302 | 2.49 | 328.3 | −1.77 | 1.54 | 4.76 |
| TVA | 18,136 | 26,300 | 2.32 | 444.7 | +1.11 | 2.46 | 6.27 |
| SOCO | 26,058 | 26,298 | 1.47 | 404.1 | −1.29 | 1.20 | 5.19 |
| PJM | 91,870 | 26,183 | 3.49 | 3,323.5 | −1.47 | 3.33 | 3.86 |

Gaussian reference: worst-1% share 3.62%. The large-miss metric was evaluated and omitted; see `docs/metric_catalogue.md`.

## 2. Three-way comparison (common set)

| BA | Common N | Seasonal-naive WAPE % | Published WAPE % | Corrected WAPE % | Change vs published (pp / relative) | Y1 / Y2 / Y3 change | Quarters improved | Hours improved | Class |
|---|--:|--:|--:|--:|--:|---|--:|--:|---|
| AECI | 25,941 | 17.56 | 2.45 | 2.52 | +0.07 pp / +2.8% | +3.6 / +3.1 / +0.7 | 1/12 | 0/24 | below project rule |
| BPAT | 25,941 | 6.50 | 1.96 | 1.95 | −0.01 pp / −0.6% | +0.6 / +0.3 / −2.7 | 7/12 | 14/24 | below project rule |
| ISNE | 25,937 | 11.08 | 2.49 | 1.79 | −0.70 pp / −28.0% | −24.4 / −25.6 / −32.8 | 12/12 | 19/24 | improvement: project rule met |
| PJM | 25,704 | 8.98 | 3.49 | 2.11 | −1.37 pp / −39.4% | −43.8 / −38.3 / −36.6 | 12/12 | 23/24 | improvement: project rule met |
| PNM | 25,944 | 6.39 | 6.09 | 2.49 | −3.61 pp / −59.2% | −54.9 / −65.3 / −55.2 | 12/12 | 24/24 | improvement: project rule met |
| PSCO | 25,905 | 9.10 | 10.43 | 4.61 | −5.82 pp / −55.8% | −33.8 / −42.9 / −68.4 | 12/12 | 24/24 | improvement: project rule met |
| SOCO | 25,932 | 10.74 | 1.46 | 0.66 | −0.81 pp / −55.2% | −50.5 / −48.6 / −67.8 | 12/12 | 24/24 | improvement: project rule met |
| TVA | 25,933 | 12.22 | 2.32 | 2.27 | −0.05 pp / −2.2% | −1.4 / −2.8 / −2.3 | 10/12 | 19/24 | below project rule |

- On the common set the relative MAE change equals the relative WAPE change by construction.
- Skill vs naive (1 − published/naive): AECI 0.86, SOCO 0.86, TVA 0.81, ISNE 0.78, BPAT 0.70, PJM 0.61, **PNM 0.05, PSCO −0.15**.
- The published forecast beats seasonal naive under the project rule (skill ≥ 0.20 and better in all years) for 6 of 8 BAs. PNM and PSCO fail: each is worse than naive in 1 of 3 years.

**Naive DST sensitivity.** The primary reference-clock naive and a strict 168-hour UTC lag select different source hours in 886–1,007 hours per DST-observing BA, and in 0 for PNM. The effect on naive WAPE is at most 0.014 percentage points (ISNE: 11.080% vs 11.094%). No conclusion depends on the naive definition.

## 2a. Temporal stability: corrected vs published WAPE by quarter

Relative WAPE change (%) on the common set; negative means the correction helped. Each cell covers 1,776–2,208 hours. The first quarter excludes the 15-day warm-up.

| Quarter | AECI | BPAT | ISNE | PJM | PNM | PSCO | SOCO | TVA |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 2023-09 Autumn | +2.9 | -1.3 | -13.4 | -39.7 | -54.9 | -45.9 | -43.6 | +2.4 |
| 2023-12 Winter | +3.4 | +1.3 | -23.0 | -36.6 | -70.6 | -14.8 | -45.8 | -1.3 |
| 2024-03 Spring | +3.6 | -0.1 | -21.1 | -40.3 | -62.8 | -32.3 | -46.6 | -2.3 |
| 2024-06 Summer | +4.4 | +2.0 | -32.7 | -52.5 | -23.9 | -35.7 | -62.3 | -3.3 |
| 2024-09 Autumn | +3.9 | +1.5 | -34.8 | -36.7 | -65.1 | -44.3 | -58.7 | -0.4 |
| 2024-12 Winter | +3.4 | +0.4 | -18.7 | -30.0 | -73.1 | -35.8 | -39.9 | +1.0 |
| 2025-03 Spring | +2.0 | -0.0 | -21.3 | -36.9 | -69.5 | -46.7 | -16.4 | -2.8 |
| 2025-06 Summer | +2.1 | -0.5 | -25.9 | -46.1 | -51.0 | -43.9 | -70.7 | -8.8 |
| 2025-09 Autumn | +0.5 | +2.6 | -32.0 | -40.5 | -52.4 | -47.4 | -74.8 | -5.4 |
| 2025-12 Winter | +2.8 | -2.1 | -28.0 | -26.0 | -56.8 | -61.9 | -48.5 | -0.3 |
| 2026-03 Spring | +3.4 | -3.6 | -35.8 | -33.3 | -59.6 | -66.1 | -73.9 | -5.1 |
| 2026-06 Summer | -3.1 | -7.9 | -34.2 | -44.4 | -53.2 | -77.1 | -76.3 | -0.1 |

- **Consistent improvement, not driven by one period:** ISNE, PJM, PNM, PSCO and SOCO improve in all 12 quarters. The smallest quarterly gains are −13.4% (ISNE), −26.0% (PJM), −23.9% (PNM), −14.8% (PSCO) and −16.4% (SOCO).
- **PSCO's gain grows over time**, from −14.8% to −47.4% in 2023–25 quarters to −61.9% to −77.1% in the last three quarters, tracking its widening bias.
- **TVA:** better in 10 of 12 quarters, but the size is −0.1% to −8.8%.
- **BPAT:** mixed (7 of 12 quarters).
- **AECI:** worse in 11 of 12 quarters (+0.5% to +4.4%).

## 3. Segment patterns (published forecast, paired set)

Hour-of-day groups have about 1,090 hours each. Weekday/weekend groups have about 18,760 / 7,530 hours. Season results rest on 3 cycles.

- **Hour of day, the strongest structure.**
  - **ISNE:** normalized bias −3.1% to −5.9% in reference hours 00–05, same sign in all 3 years. Hours 10–13 run −2.2% to −2.7% pooled, but are not ≥ 2% in every year, so they are not flagged. Hours 15–21 are within −0.6% to +0.5%. Hour WAPE ranges from 1.13% (h20) to 5.97% (h03).
  - **PJM:** −3.0% to −6.1% in hours 20–03 and +2.4% to +2.8% in hours 05–06, all stable across years. Hour WAPE ranges from 1.80% (h07) to 6.17% (h23).
  - **PNM:** −4.5% to −7.6% in *every* hour, deepest at 08–12.
  - **PSCO:** −5.6% to −14.7% in every hour, deepest at 08–15.
  - **SOCO:** −0.9% to −2.5% in every hour.
  - **TVA:** +0.8% to +1.6% in every hour.
  - **AECI, BPAT:** within ±0.5% in every hour.
- **Weekday vs weekend:** WAPE differs by at most 0.32 percentage points (PNM, 6.00% vs 6.32%). There is no day-type pattern for any BA.
- **Season:** PJM summer WAPE is 4.15% against 3.15–3.37% in other seasons, higher in each of the 3 summers (4.32 / 4.06 / 4.08). The ratio to overall WAPE is 1.19, below the locked 1.25 exception threshold. No BA meets the season-deterioration rule.
- **High-demand hours and the conditioning check.** For PJM and ISNE, the underforecast seen on actual-defined high-demand hours (−1.23%, −0.43%) disappears on forecast-defined high-demand hours (+0.11%, +0.02%). The apparent peak underforecast there is a product of selecting hours by realized demand. PNM, PSCO (underforecast) and TVA (overforecast) keep the same direction under both definitions.
- **Demand level.**
  - ISNE's bias is concentrated in its lowest quintile: −4.02% in Q1 vs −0.59% in Q5, consistent with the overnight pattern.
  - PSCO's bias deepens with demand, from −3.9% in Q1 to −14.0% in Q5.
- **Time trend.**
  - PSCO's quarterly WAPE rises from 4.5–8.6% (2023-09 to 2025-11) to 11.6%, 19.7% and 27.2% in the last three quarters. The mean monthly forecast falls to 1,200–2,000 MW below the mean actual by mid-2026.
  - AECI's WAPE falls from 3.5–4.0% in Y1 quarters to 1.3–1.9% in every quarter from spring 2025 onward.

## 4. Scale control

Spearman rank correlations with median demand (n = 8, indicative only):

| Measure | ρ |
|---|--:|
| Published WAPE | −0.40 |
| \|Normalized bias\| | −0.12 |
| Relative correction gain | +0.07 |
| Corrected WAPE | −0.64 |

Correctability is not a size effect. Correction gains meeting the project rule occur at 1.6 GW (PNM), 26 GW (SOCO) and 92 GW (PJM). No correction gain appears at 2.3 GW (AECI) or 18 GW (TVA). Once bias is removed, the error that remains lines up more with size (ρ −0.64), as expected if larger systems have smoother aggregate load. So cross-BA WAPE rankings should not be read as forecast-quality rankings without the bias decomposition.

## 5. Tail behaviour

- Worst-1% contributions of 2.9–6.3% are all below 2× the Gaussian reference (7.25%). No BA's total error is dominated by a small set of extreme hours.
- The pre-declared large-miss share (|e| > 3 × median|e|) turned out to be confounded by stable bias. PNM's −5.8% offset inflates its median |e|, so only 0.5% of its hours count as large misses. The metric was therefore omitted from all outputs.

## 6. Exception candidates

Evidence strings are in `data/analysis/exception_candidates.csv`.

| BA | Exceptions |
|---|---|
| ISNE | PERSISTENT_DIRECTIONAL_BIAS, HOUR_SPECIFIC_BIAS (h00–h05), PRACTICAL_GAIN_FROM_CORRECTION |
| PJM | PERSISTENT_DIRECTIONAL_BIAS, HOUR_SPECIFIC_BIAS (10 hours), PRACTICAL_GAIN_FROM_CORRECTION |
| PNM | PERSISTENT_DIRECTIONAL_BIAS, HOUR_SPECIFIC_BIAS (24 hours), HIGH_DEMAND_UNDERFORECAST, PRACTICAL_GAIN_FROM_CORRECTION, WEAK_SKILL_VS_NAIVE |
| PSCO | PERSISTENT_DIRECTIONAL_BIAS, HOUR_SPECIFIC_BIAS (16 hours), HIGH_DEMAND_UNDERFORECAST, PRACTICAL_GAIN_FROM_CORRECTION, WEAK_SKILL_VS_NAIVE |
| SOCO | PERSISTENT_DIRECTIONAL_BIAS, PRACTICAL_GAIN_FROM_CORRECTION |
| TVA | PERSISTENT_DIRECTIONAL_BIAS, HIGH_DEMAND_OVERFORECAST |
| AECI | ERROR_NOT_BIAS_CORRECTABLE |
| BPAT | ERROR_NOT_BIAS_CORRECTABLE |

## 7. Limitations found in this phase

- **PSCO:** a widening gap between the forecast and actual levels from late 2025. The files cannot tell forecast deterioration apart from a change in what either series covers. It is recorded as an unconfirmed source-semantic concern. PSCO is retained, because this is outcome evidence, not source evidence.
- **PNM:** a stable level offset in every hour and season. The same ambiguity applies: the data cannot separate forecasting bias from a scope difference between the two series. No root cause is asserted.
- **Correction timing:** the 2-day gap assumes forecast issue on day D − 1. The files do not record issue time.
- **Large-miss metric** omitted because it is confounded by stable bias (Section 5).
- **Season:** 3 cycles per season. Season statements are observations, not established regularities.

## Comparison-set, source-semantics and peak robustness checks

1. **Fair comparison set.** Incumbent KPIs use all paired hours (`*_all_paired`). Every published/naive/corrected comparison uses the identical common-set hours (`*_common`); this is tested. The differences between the two populations are at most 0.064 percentage points of WAPE (PSCO: 10.365 vs 10.429).
2. **Source-semantics audit** (`docs/source_semantics_audit.md`). EIA states that forecasts follow each BA's operating accounting, and that for some BAs "the comparison between actual and forecast demand is not very meaningful". PNM and PSCO are unresolved, retained, and flagged SOURCE-SEMANTIC / FORECAST-LEVEL ANOMALY.
3. **Peak robustness.** PJM's actual-defined peak underforecast is *selection-sensitive*. Robust patterns: PNM and PSCO (under), TVA (over).
4. **Practical-improvement rule.** Improvement labels use a project-defined rule (corrected WAPE at least 5% lower overall and lower in every year), not an industry threshold. The rule is always shown alongside the actual change and year/quarter consistency.

| BA | Published WAPE all paired | Published WAPE common | Naive common | Corrected common | Δ common (pp / relative) | Years / quarters improved | Peak robustness | Category |
|---|--:|--:|--:|--:|--:|---|---|---|
| AECI | 2.48 | 2.45 | 17.56 | 2.52 | +0.07 pp / +2.8% | 0/3, 1/12 | no consistent peak bias | D: little or no correctable bias |
| BPAT | 1.96 | 1.96 | 6.50 | 1.95 | -0.01 pp / -0.6% | 1/3, 7/12 | no consistent peak bias | D: little or no correctable bias |
| ISNE | 2.49 | 2.49 | 11.08 | 1.79 | -0.70 pp / -28.0% | 3/3, 12/12 | no consistent peak bias | A: systematic and correctable |
| PJM | 3.49 | 3.49 | 8.98 | 2.11 | -1.37 pp / -39.4% | 3/3, 12/12 | selection-sensitive (underforecast on actual-defined peaks only) | A: systematic and correctable |
| PNM | 6.09 | 6.09 | 6.39 | 2.49 | -3.61 pp / -59.2% | 3/3, 12/12 | robust underforecast | B: apparently correctable, source semantics uncertain |
| PSCO | 10.36 | 10.43 | 9.10 | 4.61 | -5.82 pp / -55.8% | 3/3, 12/12 | robust underforecast | B: apparently correctable, source semantics uncertain |
| SOCO | 1.47 | 1.46 | 10.74 | 0.66 | -0.81 pp / -55.2% | 3/3, 12/12 | no consistent peak bias | A: systematic and correctable |
| TVA | 2.32 | 2.32 | 12.22 | 2.27 | -0.05 pp / -2.2% | 3/3, 10/12 | robust overforecast | C: persistent bias, low practical benefit from correction |
