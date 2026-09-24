# Metric and Benchmark Catalogue

All definitions and thresholds below were fixed in `config/pipeline.toml` (`[analysis]`, `[exceptions]`) **before any forecast-error result was computed**. Changing a value is a sensitivity analysis. It is not a re-selection.

## Conventions

- **Error:** `e = forecast − actual`, in MW, for every forecast type (published, seasonal naive, bias-corrected).
- **Residual (correction only):** `r = actual − forecast`. The trailing adjustment is the mean residual, **added** to the published forecast. This is the same correction as subtracting the mean error, stated in the residual convention.
- **Sign:** **positive = overforecast, negative = underforecast.** This applies to every bias figure in the project.
- **Evaluation hour:** a BA hour with a usable actual and a usable forecast of the type being evaluated (see `docs/data_contract.md`). Nothing is imputed.
- **Evaluation sets:**
  - *Paired set:* hours with actual and published forecast. Used for descriptive metrics of the published forecast.
  - *Common set:* paired hours where the seasonal-naive and bias-corrected forecasts also exist. **All three-way comparisons use the common set only,** so every forecast is scored on identical hours.
- **Units:** demand values are hourly MW. A sum of hourly MW over one-hour intervals is reported as **MW·h (sum of hourly MW values)**. It is not called MWh, because the files do not state whether each value is an hourly average or an instantaneous reading.
- **Actual demand as a segmenting variable:** demand bands and high-demand hours are defined from actual demand. This is retrospective segmentation, not forecasting. Conditioning on the realized actual pulls signed error toward underforecast in the top bands, because an unexpectedly high actual is by definition an underforecast. So every high-demand bias result is also checked on hours defined by the published forecast, which is known in advance.

## Metrics

For a group G of evaluation hours with n hours:

| Metric | Formula | Numerator | Denominator | Grain | Interpretation | Limitation |
|---|---|---|---|---|---|---|
| **WAPE** (%) | 100 · Σ\|e\| / Σ actual | total absolute error, MW·h | total actual, MW·h | any group | primary normalized error; comparable across BAs | still partly scale-dependent: larger, more diverse systems average out idiosyncratic load |
| **MAE** (MW) | Σ\|e\| / n | total absolute error | hour count | any group | typical miss size within a BA | not comparable across BAs of different size |
| **Bias MW** | Σe / n | total signed error | hour count | any group | average over/underforecast in MW | offsetting errors cancel |
| **Normalized bias** (%) | 100 · Σe / Σ actual | total signed error | total actual | any group | directional error relative to demand; cross-BA comparable | cancels within the group; read with the persistence checks |
| **Absolute error** (MW) | \|e\| | – | – | hour | hourly analytical field | – |
| **High-demand WAPE / bias** | WAPE / normalized bias over high-demand hours | | | BA × high-demand flag | performance when load is highest | conditioning bias (see above) |
| **Worst-1% contribution** (%) | 100 · Σ\|e\| over the k = ⌈0.01·n⌉ largest-\|e\| hours / Σ\|e\| | error in worst hours | total absolute error | BA, BA × year | tells a normally stable forecast with rare extreme misses apart from a chronically mediocre one | depends on n; ties broken by earlier UTC |
| **Skill vs naive** | 1 − WAPE_published / WAPE_naive | | | BA (common set) | share of naive error removed by the published forecast | only as strong as the naive floor |
| **Relative WAPE change** (%) | 100 · (WAPE_corrected / WAPE_published − 1) | | | BA, segment (common set) | negative = correction improves | on a common set this equals the relative MAE change |

**Gaussian reference value:** for normally distributed errors, the worst 1% of hours carries about 3.62% of total absolute error. Values well above that mean heavy tails.

### High-demand definition (primary)

High-demand hours are hours whose actual demand is at or above the BA's **whole-window 90th percentile** of actual demand, over paired hours.

- **Why whole-window rather than season-aware:** the operational question is how the forecast performs when load is highest for that system, and those hours genuinely cluster in the BA's peak season. A season-aware decile would label mild-season hours "peak" even when the system is far from its highest load.
- **Consequence:** high-demand results partly reflect the peak season. The season segmentation is reported separately so the two can be read side by side.
- **Demand-level bands:** quintiles of actual demand, per BA, over the whole window. Q1 is the lowest 20% and Q5 the highest. Boundaries are BA-relative, with no MW cutoffs. Quintiles were fixed before any result was computed. A Low/Medium/High banding considered later was not adopted, because re-banding after results were seen would be a post-hoc change. Coarser bands can be formed by merging quintiles (e.g. Q1–Q2, Q3, Q4–Q5).
- **Sensitivity:** the forecast-defined flag uses the top decile of the published forecast.

### Large-miss threshold: evaluated and omitted

| Option | Assessment |
|---|---|
| A. BA percentile of own errors (e.g. > P95) | Rejected. The share is fixed at 5% by construction. |
| B. Robust multiple of the BA's median \|e\| (3×) | Pre-declared and computed, then **omitted** (see below). |
| C. Fixed hourly percentage error (e.g. APE > 10%) | Rejected. No domain standard exists, and it favours large, smooth systems. |

Why option B was dropped: once computed, the share turned out to depend on stable bias as much as on tails. A BA whose errors are dominated by a constant offset has a large median |e|, so hardly any hour exceeds 3× it (PNM: 0.49% of hours, against a Gaussian reference of 4.3%). The metric would therefore report "few large misses" for the BA whose forecast is most consistently off. That meaning is misleading, so the metric is **omitted** from all outputs. Tail behaviour is covered by the worst-1% contribution instead. This was a property of the metric's construction; the threshold itself was not tuned.

## Benchmarks

### 1. Seasonal naive (primary): same BA reporting/reference-clock hour, 7 calendar days earlier

`naive(t) = actual at reference wall-clock time ref_period_start(t) − 7 days, same BA`

The lookup is on the BA reference clock, not a fixed UTC lag, so "17:00 last Tuesday" means 17:00 on the reporting clock even across a DST change. Rules:

- **Spring-forward:** a target whose baseline wall-clock time falls in the skipped hour, i.e. 02:00 one week after the transition, has **no baseline** (`naive_status = hour_absent`).
- **Fall-back:**
  - On the fall-back day, both 01:00 target hours use the single 01:00 hour from 7 days earlier.
  - One week after the fall-back day, the 01:00 target uses the **first** 01:00 occurrence of the fall-back day (the DST instance, earlier UTC). This is deterministic.
- **Fixed-offset BAs (PNM):** the reference clock has no DST, so the lookup equals a 168-hour UTC lag.
- **Missing baseline:** if the baseline hour has no usable actual, the naive value is null (`actual_missing`). The first 7 days of the window have no baseline (`before_window`, 168 hours per BA). **Nothing is filled.** Counts per BA are in `data/analysis/benchmark_coverage.csv`. Excluded DST observations: 3 per DST-observing BA (`hour_absent`, the 02:00 targets one week after each spring-forward) and 0 for PNM.
- **Causality:** the baseline is always ≥ 167 UTC hours before the target. That is known well before a day-ahead forecast is issued.
- **DST sensitivity:** a strict **168-hour UTC lag** is computed as `naive_168h_mw` and reported only as a sensitivity. The two definitions are never mixed.

### 2. Published forecast

The EIA-930 `Demand Forecast (MW)` as reported.

### 3. Trailing bias correction (strictly causal)

`corrected(t) = published(t) + adj(t)`, where `adj(t)` is the mean residual `r = actual − published forecast` over paired hours with:

- the same BA,
- the same **reference hour** (`ref_hour`),
- a reference date in **[D − 29, D − 2]**, where D is the target's reference date.

That is a **28-day window with a 2-day gap**.

- **Why the 2-day gap:** a day-ahead forecast for day D is issued on day D − 1, before D − 1's actuals are complete. Excluding D and D − 1 means no residual could have been unknown at issue time. The files don't record issue time, so the gap is set conservatively.
- **Why 28 days:** the simpler of the two candidates. Four weeks balances each weekday equally and adapts within a season. The 56-day window is not used for any headline result.
- **Minimum history:** at least 14 distinct days with residuals in the window. Otherwise `corrected` is null and **not** replaced by the published forecast; those hours leave the common set. The window's first ~15 days therefore have no correction.
- **Explicit shift:** daily residual sums are rolled over 28 days and shifted by 2 days, so the window ending on D − 2 is attached to target date D.
- **Leakage guard:** the target hour, the target day and the previous day never enter `adj(t)`. No full-window aggregate is used. This is tested by perturbing D, D − 1 and D − 30 (no change) and D − 2 and D − 29 (change).

## Evaluation periods and stability

- **Evaluation years:** Y1 = 2023-09 to 2024-08, Y2 = 2024-09 to 2025-08, Y3 = 2025-09 to 2026-08, on reference-time dates.
- **Seasons:** meteorological. Autumn is Sep–Nov, Winter Dec–Feb, Spring Mar–May, Summer Jun–Aug. Each season appears exactly 3 times, so season claims rest on 3 cycles and are stated cautiously.
- **Quarter periods:** season × season-year, 12 contiguous periods, used to track correction benefit over time.
- **Day type:** weekday / weekend (Saturday, Sunday) on the reference date. Holidays are not separated.
- **Out-of-sample structure:** the correction is recomputed causally at every timestamp, so every corrected value is out-of-sample. Y1 serves as the establishment period. Persistence means the benefit holds separately in Y1, Y2 and Y3, and is reported quarter by quarter.

## Project-defined practical-improvement rule and classification

The rule below is a **project-defined practical-improvement rule**, not an industry materiality threshold; no authoritative external threshold was found. Outputs always show the actual relative change and its year/quarter consistency next to the label, so the label is never the only evidence.

| Label (`project_rule_class`) | Rule |
|---|---|
| `improvement: project rule met` | common-set relative WAPE change ≤ −5% overall **and** corrected WAPE lower in all 3 evaluation years |
| `degradation: project rule met` | relative change ≥ +5% overall **and** corrected WAPE higher in all 3 years |
| `mixed across years` | \|relative change\| ≥ 5% overall but the direction differs across years |
| `below project rule (|change| < 5%)` | \|relative change\| < 5% |
| `published_beats_naive_project_rule` | skill ≥ 0.20 overall **and** published WAPE < naive WAPE in all 3 years |

## Comparison populations

- **Incumbent KPIs (`*_all_paired`):** every hour with a usable actual and a usable published forecast.
- **Benchmark comparisons (`*_common`):** the published, seasonal-naive and corrected forecasts are scored on the **identical** set of (BA, UTC) hours, where all three exist. Every delta, skill score or "correction improves" statement uses only `*_common` values. This is tested.

## Peak robustness

Peak bias is evaluated on two selections: the top decile of **actual** demand (retrospective diagnostic) and the top decile of the **published forecast** (known in advance).
- **Robust:** the same direction with |normalized bias| ≥ 1.0% in all 3 years on both selections.
- **Selection-sensitive:** the pattern appears on actual-defined peaks only. Such results are never exceptions or conclusions.

## Final analytical categories (automated; `category`)

| Category | Rule |
|---|---|
| **A. Systematic and correctable** | project improvement rule met; no source-semantic flag |
| **B. Apparently correctable, source semantics uncertain** | project improvement rule met; BA flagged by `docs/source_semantics_audit.md` |
| **C. Persistent bias, low practical benefit** | `PERSISTENT_DIRECTIONAL_BIAS` fired; improvement rule not met |
| **D. Little or no correctable bias** | \|normalized bias\| < 1.0%; improvement rule not met |
| unclassified | none of the above |

## Exception candidates

No composite score. Each flag states its rule and its evidence.

| Code | Rule |
|---|---|
| `PERSISTENT_DIRECTIONAL_BIAS` | \|normalized bias\| ≥ 1.0% (paired set) and the same sign in Y1, Y2 and Y3 |
| `HOUR_SPECIFIC_BIAS` | ≥ 3 reference hours with \|normalized bias\| ≥ 2.0% and the same sign in all 3 years |
| `HIGH_DEMAND_UNDERFORECAST` / `HIGH_DEMAND_OVERFORECAST` | **robust** peak pattern only: ≤ −1.0% (or ≥ +1.0%) in all 3 years on **both** actual-defined and forecast-defined top-decile hours; selection-sensitive patterns never fire |
| `EXTREME_HOUR_CONCENTRATION` | worst-1% contribution ≥ 2 × Gaussian reference (≥ 7.24%) |
| `SEASON_SPECIFIC_DETERIORATION` | a season's WAPE ≥ 1.25 × the BA's overall WAPE in each of its 3 season-years |
| `PRACTICAL_GAIN_FROM_CORRECTION` | `improvement: project rule met` |
| `CORRECTION_DEGRADES_FORECAST` | `degradation: project rule met` |
| `ERROR_NOT_BIAS_CORRECTABLE` | below the project rule or degradation, and \|normalized bias\| < 1.0% |
| `WEAK_SKILL_VS_NAIVE` | `published_beats_naive_project_rule` is false |
| `SOURCE_SEMANTIC_FORECAST_LEVEL_ANOMALY` | BA flagged by the source-semantics audit |
