# DAX Measure Catalogue

Model: `docs/semantic_model.md`. Put all measures on a measures home table, or on `FactHourlyForecastPerformance`, in the display folders shown.

Conventions:
- **Error** = forecast − actual (positive = overforecast).
- **Ratios** return fractions and use a percentage format.
- **Percentage-point measures** return numbers labelled "pp".
- **Populations:** `… All Paired` uses `is_paired = TRUE` (incumbent KPIs). `… Common` uses `in_common_set = TRUE` (benchmark comparisons on identical hours).
- **Reconciliation:** each measure marked **[R]** is reconciled in `docs/powerbi_reconciliation.md` in a single-BA filter context.

`F` below stands for `FactHourlyForecastPerformance`; paste the full table name when creating the measures.

## 1. Base counts and sums (folder: `0 Base`)

```dax
Paired Hours =                                             -- [R]
CALCULATE ( COUNTROWS ( FactHourlyForecastPerformance ), FactHourlyForecastPerformance[is_paired] = TRUE () )

Common Hours =                                             -- [R]
CALCULATE ( COUNTROWS ( FactHourlyForecastPerformance ), FactHourlyForecastPerformance[in_common_set] = TRUE () )

Actual MW-h Equivalent (All Paired) =
-- Sum of hourly MW values over one-hour intervals. Not labelled MWh: EIA does not
-- state whether each hourly value is an average or an instantaneous reading.
CALCULATE ( SUM ( FactHourlyForecastPerformance[actual_mw] ), FactHourlyForecastPerformance[is_paired] = TRUE () )

Actual MW-h Equivalent (Common) =
CALCULATE ( SUM ( FactHourlyForecastPerformance[actual_mw] ), FactHourlyForecastPerformance[in_common_set] = TRUE () )
```

## 2. Published forecast, all paired hours: incumbent KPIs (folder: `1 Incumbent`)

```dax
Published Abs Error MW-h (All Paired) =
SUMX (
    FILTER ( FactHourlyForecastPerformance, FactHourlyForecastPerformance[is_paired] = TRUE () ),
    ABS ( FactHourlyForecastPerformance[forecast_mw] - FactHourlyForecastPerformance[actual_mw] )
)

Published Signed Error MW-h (All Paired) =
SUMX (
    FILTER ( FactHourlyForecastPerformance, FactHourlyForecastPerformance[is_paired] = TRUE () ),
    FactHourlyForecastPerformance[forecast_mw] - FactHourlyForecastPerformance[actual_mw]
)

Published WAPE (All Paired) =                              -- [R]  format 0.00%
DIVIDE ( [Published Abs Error MW-h (All Paired)], [Actual MW-h Equivalent (All Paired)] )

Published MAE MW (All Paired) =                            -- [R]  format #,0.0
DIVIDE ( [Published Abs Error MW-h (All Paired)], [Paired Hours] )

Published Normalized Bias (All Paired) =                   -- [R]  format +0.00%;-0.00%;0.00%
-- positive = overforecast, negative = underforecast
DIVIDE ( [Published Signed Error MW-h (All Paired)], [Actual MW-h Equivalent (All Paired)] )

Peak WAPE (Actual-Defined, Retrospective) =                -- [R]  format 0.00%
-- top decile of ACTUAL demand per BA: retrospective diagnostic only
CALCULATE ( [Published WAPE (All Paired)], FactHourlyForecastPerformance[high_demand] = "high" )

Peak Normalized Bias (Actual-Defined) =
CALCULATE ( [Published Normalized Bias (All Paired)], FactHourlyForecastPerformance[high_demand] = "high" )

Peak Normalized Bias (Forecast-Defined) =
-- top decile of the PUBLISHED forecast per BA: robustness check
CALCULATE ( [Published Normalized Bias (All Paired)], FactHourlyForecastPerformance[high_forecast] = "high" )

Worst 1% Error Contribution =                              -- [R]  format 0.00%
-- Share of total |error| from the ceil(1% x n) largest-error paired hours.
-- Ties are broken by earlier UTC. Meaningful per BA only; returns BLANK when several BAs are in context.
IF (
    HASONEVALUE ( DimBA[ba_code] ),
    VAR T = FILTER ( FactHourlyForecastPerformance, FactHourlyForecastPerformance[is_paired] = TRUE () )
    VAR K = ROUNDUP ( 0.01 * COUNTROWS ( T ), 0 )
    VAR TopRows =
        TOPN (
            K, T,
            ABS ( FactHourlyForecastPerformance[forecast_mw] - FactHourlyForecastPerformance[actual_mw] ), DESC,
            FactHourlyForecastPerformance[utc_period_end], ASC
        )
    RETURN
        DIVIDE (
            SUMX ( TopRows, ABS ( FactHourlyForecastPerformance[forecast_mw] - FactHourlyForecastPerformance[actual_mw] ) ),
            SUMX ( T, ABS ( FactHourlyForecastPerformance[forecast_mw] - FactHourlyForecastPerformance[actual_mw] ) )
        )
)
```

## 3. Common comparison set: published, seasonal naive, corrected (folder: `2 Benchmarks (Common Set)`)

```dax
Published WAPE (Common) =                                  -- [R]  format 0.00%
DIVIDE (
    SUMX ( FILTER ( FactHourlyForecastPerformance, FactHourlyForecastPerformance[in_common_set] = TRUE () ),
           ABS ( FactHourlyForecastPerformance[forecast_mw] - FactHourlyForecastPerformance[actual_mw] ) ),
    [Actual MW-h Equivalent (Common)]
)

Published MAE MW (Common) =                                -- [R]  format #,0.0
DIVIDE (
    SUMX ( FILTER ( FactHourlyForecastPerformance, FactHourlyForecastPerformance[in_common_set] = TRUE () ),
           ABS ( FactHourlyForecastPerformance[forecast_mw] - FactHourlyForecastPerformance[actual_mw] ) ),
    [Common Hours]
)

Published Normalized Bias (Common) =                       -- [R]  format +0.00%;-0.00%;0.00%
DIVIDE (
    SUMX ( FILTER ( FactHourlyForecastPerformance, FactHourlyForecastPerformance[in_common_set] = TRUE () ),
           FactHourlyForecastPerformance[forecast_mw] - FactHourlyForecastPerformance[actual_mw] ),
    [Actual MW-h Equivalent (Common)]
)

Naive WAPE (Common) =                                      -- [R]  format 0.00%
DIVIDE (
    SUMX ( FILTER ( FactHourlyForecastPerformance, FactHourlyForecastPerformance[in_common_set] = TRUE () ),
           ABS ( FactHourlyForecastPerformance[naive_forecast_mw] - FactHourlyForecastPerformance[actual_mw] ) ),
    [Actual MW-h Equivalent (Common)]
)

Naive MAE MW (Common) =                                    -- [R]  format #,0.0
DIVIDE (
    SUMX ( FILTER ( FactHourlyForecastPerformance, FactHourlyForecastPerformance[in_common_set] = TRUE () ),
           ABS ( FactHourlyForecastPerformance[naive_forecast_mw] - FactHourlyForecastPerformance[actual_mw] ) ),
    [Common Hours]
)

Corrected WAPE (Common) =                                  -- [R]  format 0.00%
DIVIDE (
    SUMX ( FILTER ( FactHourlyForecastPerformance, FactHourlyForecastPerformance[in_common_set] = TRUE () ),
           ABS ( FactHourlyForecastPerformance[corrected_forecast_mw] - FactHourlyForecastPerformance[actual_mw] ) ),
    [Actual MW-h Equivalent (Common)]
)

Corrected MAE MW (Common) =                                -- [R]  format #,0.0
DIVIDE (
    SUMX ( FILTER ( FactHourlyForecastPerformance, FactHourlyForecastPerformance[in_common_set] = TRUE () ),
           ABS ( FactHourlyForecastPerformance[corrected_forecast_mw] - FactHourlyForecastPerformance[actual_mw] ) ),
    [Common Hours]
)

Corrected Normalized Bias (Common) =                       -- [R]  format +0.00%;-0.00%;0.00%
DIVIDE (
    SUMX ( FILTER ( FactHourlyForecastPerformance, FactHourlyForecastPerformance[in_common_set] = TRUE () ),
           FactHourlyForecastPerformance[corrected_forecast_mw] - FactHourlyForecastPerformance[actual_mw] ),
    [Actual MW-h Equivalent (Common)]
)
```

## 4. Correction effect: always shown as both pp and relative (folder: `3 Correction Effect`)

```dax
WAPE Change (pp) =                                         -- [R]  format +0.00" pp";-0.00" pp";0.00" pp"
-- corrected minus published, both on the common set; negative = correction reduced error
( [Corrected WAPE (Common)] - [Published WAPE (Common)] ) * 100

WAPE Change (Relative) =                                   -- [R]  format +0.0%;-0.0%;0.0%
DIVIDE ( [Corrected WAPE (Common)], [Published WAPE (Common)] ) - 1

WAPE Change Label =
-- display text: always pp and relative together
FORMAT ( [WAPE Change (pp)], "+0.00;-0.00" ) & " pp (" & FORMAT ( [WAPE Change (Relative)], "+0.0%;-0.0%" ) & ")"

Published Skill vs Naive (Common) =                        -- format 0.00
1 - DIVIDE ( [Published WAPE (Common)], [Naive WAPE (Common)] )

Quarters Improved =                                        -- [R]  format 0
-- 12 season-quarters; common-set corrected WAPE below published WAPE
COUNTROWS (
    FILTER ( VALUES ( DimDate[season_period] ), [Corrected WAPE (Common)] < [Published WAPE (Common)] )
)

Quarters Evaluated =
COUNTROWS ( FILTER ( VALUES ( DimDate[season_period] ), NOT ISBLANK ( [Published WAPE (Common)] ) ) )

Quarter Consistency Label =
[Quarters Improved] & " / " & [Quarters Evaluated]

Years Improved =                                           -- [R]  format 0
COUNTROWS (
    FILTER ( VALUES ( DimDate[eval_year] ), [Corrected WAPE (Common)] < [Published WAPE (Common)] )
)
```

## 5. Multi-BA display (folder: `4 Cross-BA view`)

```dax
Published WAPE (BA Average) =
-- equal weight per BA; a pooled WAPE would be dominated by PJM's volume
AVERAGEX ( VALUES ( DimBA[ba_code] ), [Published WAPE (All Paired)] )

Published |Normalized Bias| (BA Average) =
AVERAGEX ( VALUES ( DimBA[ba_code] ), ABS ( [Published Normalized Bias (All Paired)] ) )

Corrected WAPE (BA Average, Common) =
AVERAGEX ( VALUES ( DimBA[ba_code] ), [Corrected WAPE (Common)] )

Published WAPE (BA Average, Common) =
AVERAGEX ( VALUES ( DimBA[ba_code] ), [Published WAPE (Common)] )

WAPE Change (pp, BA Average) =
( [Corrected WAPE (BA Average, Common)] - [Published WAPE (BA Average, Common)] ) * 100

WAPE Change (Relative, BA Average) =
DIVIDE ( [Corrected WAPE (BA Average, Common)], [Published WAPE (BA Average, Common)] ) - 1

BAs In View =
DISTINCTCOUNT ( DimBA[ba_code] )

KPI Title WAPE =
"Average WAPE across " & [BAs In View] & " BAs"

KPI Title Bias =
"Average absolute normalized bias across " & [BAs In View] & " BAs"

KPI Title Corrected =
"Average corrected WAPE across " & [BAs In View] & " BAs"
```

## 6. Labels and flags (folder: `5 Labels`)

```dax
Category =
SELECTEDVALUE ( DimBA[category_label] )

Source Semantics Flag =
-- visible text, not tooltip-only
IF ( SELECTEDVALUE ( DimBA[source_semantic_flag] ) = TRUE (), "SOURCE SEMANTICS UNCERTAIN", "" )

Exception Reasons =
SELECTEDVALUE ( DimBA[exception_reasons] )

Peak Robustness =
SELECTEDVALUE ( DimBA[peak_robustness] )

Source Semantics Note =
IF (
    SELECTEDVALUE ( DimBA[source_semantic_flag] ) = TRUE (),
    "The reported forecast series shows a persistent level offset, but available EIA metadata does not resolve whether this reflects forecast-process bias, reporting-scope differences, resubmission behavior, or another source-definition effect."
)

Bias Direction Color =
-- conditional-format helper: negative bias (underforecast) vs positive (overforecast)
IF ( [Published Normalized Bias (All Paired)] < 0, "#B45309", "#1D4ED8" )
```

## Notes

- `Quarters Improved` iterates `DimDate[season_period]`. It must be evaluated in a single-BA context, and DimDate must not be filtered by a date slicer.
- `Worst 1% Error Contribution` uses `TOPN` with a second sort key (`utc_period_end`), so exactly *k* rows are returned; the key is unique per BA.
- None of these measures is a forecast. The seasonal-naive and corrected values are precomputed benchmark columns (`docs/metric_catalogue.md`).
