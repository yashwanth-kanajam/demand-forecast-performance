# Semantic Model

Target environment: Power BI service (web), My workspace, Fabric Free license.

- **Local CSV upload** isn't accepted by the service, so files are read from OneDrive for Business through Power Query Online. That route was tested with synthetic data.
- **Excel** is not used as the handoff format: in testing it produced serial dates and unpromoted headers.

## Tables

| Table | Source file | Grain | Rows | Role |
|---|---|---|--:|---|
| `FactHourlyForecastPerformance` | `data/bi/fact_hourly_performance.csv` | BA × UTC hour | 210,432 | fact |
| `DimDate` | `data/bi/dim_date.csv` | BA reference-time date | 1,096 | dimension |
| `DimBA` | `data/bi/dim_ba.csv` | BA | 8 | dimension, including category and flag display fields |
| `BAMetricSummary` | `data/bi/ba_metric_summary.csv` | BA | 8 | **disconnected** reconciliation reference; not used in visuals |

`exception_candidates.csv` is not loaded. The attention table uses `DimBA[exception_reasons]`, and the CSV stays as documentation.

## Relationships

Both relationships are many-to-one with single-direction filtering (dimension → fact).

```
DimDate[date]      1 ──► * FactHourlyForecastPerformance[ref_date]
DimBA[ba_code]     1 ──► * FactHourlyForecastPerformance[ba_code]
```

- There are no other relationships. `BAMetricSummary` stays disconnected on purpose: it holds Python reference values used only to check measures.
- `ref_date` is the BA reference/reporting-time date, not UTC. DimDate is shared across BAs because every BA's window covers the same 1,096 reference dates.
- DAX time-intelligence functions are not used. Hourly comparisons (seasonal naive, trailing correction) are precomputed columns.

## Import steps (Power Query Online)

1. Upload the four CSVs to one private OneDrive for Business folder, e.g. `Documents/dfp_bi/`. Don't share them.
2. Power BI → My workspace → **New item → Semantic model** → **Get data → Blank query**. Paste the query for each table (below), replacing `<BASE>` with the folder URL, e.g. `https://<tenant>-my.sharepoint.com/personal/<user>/Documents/dfp_bi`.
3. Rename each query to the table name. The reliable way is **F2** in the Queries pane.
4. **Create a semantic model only**. Name it `Demand Forecast Performance`.
5. Open the data model. Create the two relationships (**Manage relationships → New**), add the measures from `docs/dax_measures.md`, and apply the column settings below.

Blank values in the CSVs are empty strings. They're converted to `null` before typing so that number conversion doesn't produce errors.

### FactHourlyForecastPerformance

```m
let
    Source = Csv.Document(Web.Contents("<BASE>/fact_hourly_performance.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Nulls = Table.ReplaceValue(Promoted, "", null, Replacer.ReplaceValue, Table.ColumnNames(Promoted)),
    Utc = Table.TransformColumns(Nulls, {
        {"utc_period_end", each DateTimeZone.RemoveZone(DateTimeZone.FromText(_)), type datetime},
        {"utc_period_start", each DateTimeZone.RemoveZone(DateTimeZone.FromText(_)), type datetime}}),
    Typed = Table.TransformColumnTypes(Utc, {
        {"ba_code", type text}, {"ref_period_start", type datetime}, {"ref_date", type date},
        {"ref_hour", Int64.Type}, {"utc_offset_hours", type number}, {"is_dst", type logical},
        {"actual_mw", type number}, {"forecast_mw", type number}, {"naive_forecast_mw", type number},
        {"corrected_forecast_mw", type number}, {"adjustment_mw", type number},
        {"is_paired", type logical}, {"in_common_set", type logical},
        {"high_demand", type text}, {"high_forecast", type text}, {"demand_band", type text}}, "en-US")
in
    Typed
```

`utc_period_end` is stored as a UTC wall-clock `datetime` (zone removed after parsing the `Z` suffix). It is the canonical key together with `ba_code`.

### DimDate

```m
let
    Source = Csv.Document(Web.Contents("<BASE>/dim_date.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {
        {"date", type date}, {"year", Int64.Type}, {"month", Int64.Type}, {"month_name", type text},
        {"year_month", type text}, {"day_of_week", Int64.Type}, {"day_name", type text}, {"day_type", type text},
        {"season", type text}, {"season_period", type text}, {"eval_year", type text}}, "en-US")
in
    Typed
```

### DimBA

```m
let
    Source = Csv.Document(Web.Contents("<BASE>/dim_ba.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {
        {"ba_code", type text}, {"ba_name", type text}, {"region_name", type text},
        {"eia_time_zone_label", type text}, {"reference_time_zone", type text},
        {"median_actual_mw", type number}, {"paired_coverage_pct", type number},
        {"category_code", type text}, {"category_label", type text},
        {"source_semantic_flag", type logical}, {"source_semantics_display", type text},
        {"project_rule_class", type text}, {"peak_robustness", type text}, {"bias_shape", type text},
        {"hourly_bias_min_pct", type number}, {"hourly_bias_max_pct", type number},
        {"exception_reasons", type text}}, "en-US")
in
    Typed
```

### BAMetricSummary (disconnected reference)

```m
let
    Source = Csv.Document(Web.Contents("<BASE>/ba_metric_summary.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    TextCols = {"ba_code", "project_rule_class", "peak_robustness", "category", "exception_reasons"},
    LogicalCols = {"source_semantic_flag"},
    NumberCols = List.Difference(Table.ColumnNames(Promoted), TextCols & LogicalCols),
    Typed = Table.TransformColumnTypes(Promoted,
        List.Transform(NumberCols, each {_, type number})
        & List.Transform(TextCols, each {_, type text})
        & List.Transform(LogicalCols, each {_, type logical}), "en-US")
in
    Typed
```


## Column settings

| Table[column] | Setting |
|---|---|
| `FactHourlyForecastPerformance[actual_mw, forecast_mw, naive_forecast_mw, corrected_forecast_mw, adjustment_mw]` | Summarize by: **None** (measures only) |
| `FactHourlyForecastPerformance[ref_hour]` | Summarize by: None; used as an axis |
| `FactHourlyForecastPerformance[is_paired, in_common_set, utc_*, ref_period_start, is_dst, utc_offset_hours]` | Hidden from report view |
| `DimDate[month_name]` | Sort by `DimDate[month]` |
| `DimDate[day_name]` | Sort by `DimDate[day_of_week]` |
| `DimBA[category_label]` | Sort by `DimBA[category_code]` |
| `BAMetricSummary` | Hide the whole table from report view |

## Model rules

- **Incumbent KPIs** use all paired hours (`is_paired = TRUE`).
- **Benchmark comparisons** (published vs naive vs corrected) use `in_common_set = TRUE` for all three, so they're scored on identical hours. This is built into each `… Common` measure; no page-level filter is needed.
- **Pooling across BAs:** a WAPE over several BAs is weighted by MW and dominated by PJM. Page 1 KPI cards therefore use the equal-weight BA-average measures in `docs/dax_measures.md`, labelled as such.
