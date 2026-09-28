# Report Specification: Demand Forecast Performance & Operational Exceptions

Two pages, 16:9 canvas (1280 × 720). Measures: `docs/dax_measures.md`. Model: `docs/semantic_model.md`.

**Display rules:**
1. Any visual comparing published, naive and corrected forecasts uses `… (Common)` measures only. No visual mixes all-paired and common-set measures.
2. Every correction effect is shown as **both** percentage points and relative change (`WAPE Change (pp)` and `WAPE Change (Relative)`, or `WAPE Change Label`).
3. PNM and PSCO carry the visible text **SOURCE SEMANTICS UNCERTAIN** wherever they appear in a table or card, not only in tooltips.
4. Bias sign: positive = overforecast, negative = underforecast. Every bias visual states this in its subtitle.
5. Peak underforecast is reported as an exception only where it survives both peak definitions (currently PNM and PSCO, plus TVA overforecast). PJM and ISNE are never labelled peak underforecast.

Theme:
- Neutral background, one accent colour.
- Bias colours: underforecast `#B45309` (amber), overforecast `#1D4ED8` (blue).
- Published `#6B7280` (grey), corrected `#0F766E` (teal), naive `#D1D5DB` (light grey).
- No gradients or 3-D; data labels to 2 decimals.

---

## Page 1: Forecast Performance Review

**Questions:** How reliable is the incumbent forecast? Where is persistent bias? What requires attention?

| # | Visual | Position (x, y, w, h) | Fields | Settings |
|---|---|---|---|---|
| 1 | Text box: title | 24, 16, 900, 40 | "Demand Forecast Performance & Operational Exceptions" | 20 pt |
| 2 | Text box: headline | 24, 56, 900, 44 | Annotation P1-A (below) | 11 pt |
| 3 | Slicer | 960, 16, 296, 84 | `DimBA[category_label]` | Dropdown, multi-select, "All" default |
| 4 | Card | 24, 112, 236, 88 | `Published WAPE (BA Average)` | Title (dynamic): `KPI Title WAPE`, e.g. "Average WAPE across 8 BAs". Subtitle: "Equal-weighted BA average · not a pooled grid-wide WAPE" |
| 5 | Card | 272, 112, 236, 88 | `Published \|Normalized Bias\| (BA Average)` | Title (dynamic): `KPI Title Bias`, e.g. "Average absolute normalized bias across 8 BAs" |
| 6 | Card | 520, 112, 236, 88 | `Corrected WAPE (BA Average, Common)` | Title (dynamic): `KPI Title Corrected`, e.g. "Average corrected WAPE across 8 BAs". Subtitle: "Trailing 28-day correction · common hours" |
| 7 | Card | 768, 112, 236, 88 | `WAPE Change (pp, BA Average)`; `WAPE Change (Relative, BA Average)` | New card visual with two values, or a multi-row card; label "pp" and "relative" |
| 8 | Card | 1016, 112, 240, 88 | `Paired Hours`; `BAs In View` | Subtitle: "36 months, hourly, EIA-930" |
| 9 | Clustered bar chart | 24, 212, 616, 256 | Y: `DimBA[ba_code]`; X: `Published WAPE (Common)`, `Corrected WAPE (Common)`; Tooltips: `WAPE Change Label`, `Quarter Consistency Label`, `Category` | Title: "Published vs bias-corrected WAPE (common comparison hours)". Sort by `Published WAPE (Common)` descending. Data labels on. |
| 10 | Bar chart | 652, 212, 604, 256 | Y: `DimBA[ba_code]`; X: `Published Normalized Bias (All Paired)` | Title: "Directional bias by BA". Subtitle: "negative = underforecast · positive = overforecast". Bar colour: fx → Field value → `Bias Direction Color`. Constant line at 0. |
| 11 | Table: attention list | 24, 480, 1232, 200 | `DimBA[ba_code]`, `Category`, `Source Semantics Flag`, `Published WAPE (All Paired)`, `Published Normalized Bias (All Paired)`, `Corrected WAPE (Common)`, `WAPE Change (pp)`, `WAPE Change (Relative)`, `Quarter Consistency Label`, `Exception Reasons` | Title: "Operating attention list". Sort by `DimBA[category_code]`, then `WAPE Change (pp)`. `Source Semantics Flag`: background `#FEF3C7` when not blank. Word-wrap `Exception Reasons`. Totals off. |
| 12 | Text box: footer | 24, 684, 1232, 28 | Annotation P1-B | 8 pt, grey |

Default values for cards 4–8 (all 8 BAs; confirmed in the built report):

| Card | Value |
|---|--:|
| Average WAPE across 8 BAs | 3.83% |
| Average absolute normalized bias across 8 BAs | 2.62% |
| Average corrected WAPE across 8 BAs (common hours) | 2.30% |
| WAPE Change (pp / relative) | −1.54 pp / −40.1% |
| Paired Hours | 210,278 |
| BAs In View | 8 |

These are equal-weighted averages of per-BA values, not pooled grid-wide metrics; a pooled WAPE would be dominated by PJM's volume. They include the two source-flagged BAs. Selecting category **A** in slicer 3 shows the unflagged correctable group.

---

## Page 2: Error Patterns & Correctability

**Questions:** When does performance deteriorate? Which errors are systematic enough to correct?

| # | Visual | Position | Fields | Settings |
|---|---|---|---|---|
| 1 | Text box: title | 24, 16, 700, 36 | "Error patterns & correctability" | 18 pt |
| 2 | Slicer | 24, 56, 240, 60 | `DimBA[ba_code]` | Dropdown, **single select**, default ISNE |
| 3 | Multi-row card | 276, 56, 980, 60 | `Category`, `Source Semantics Flag`, `Peak Robustness`, `DimBA[bias_shape]` | Source flag in amber text. `bias_shape` is a descriptive display field only (not a category, exception or finding). |
| 4 | Line chart | 24, 128, 616, 250 | X: `FactHourlyForecastPerformance[ref_hour]` (continuous 0–23); Y: `Published Normalized Bias (Common)`, `Corrected Normalized Bias (Common)` | Title: "Directional bias by BA reference hour". Subtitle: "Reference/reporting clock · negative = underforecast". Constant line at 0. |
| 5 | Line chart | 652, 128, 604, 250 | X: `DimDate[season_period]` (categorical, sorted ascending); Y: `Published WAPE (Common)`, `Corrected WAPE (Common)`; Tooltip: `WAPE Change Label` | Title: "Quarterly stability of the correction". Subtitle: "12 quarters · common comparison hours". Markers on. |
| 6 | Clustered column chart | 24, 390, 400, 250 | Values: `Naive WAPE (Common)`, `Published WAPE (Common)`, `Corrected WAPE (Common)` (no axis field) | Title: "Seasonal naive vs published vs corrected". Data labels on. Colours per theme. |
| 7 | Clustered column chart | 436, 390, 400, 250 | X: `FactHourlyForecastPerformance[demand_band]` (Q1–Q5); Y: `Published Normalized Bias (All Paired)` | Title: "Directional bias by demand quintile". Subtitle: "Quintiles of actual demand within BA · retrospective segmentation". |
| 8 | Text box: callout | 848, 390, 408, 150 | Annotation P2-A | 10 pt |
| 9 | Card | 848, 548, 408, 92 | `Source Semantics Note` | Word wrap. Blank for unflagged BAs. |
| 10 | Text box: footer | 24, 684, 1232, 28 | Annotation P2-B | 8 pt, grey |

Additional measure for visual 9 (also in `docs/dax_measures.md`, section 6):

```dax
Source Semantics Note =
IF (
    SELECTEDVALUE ( DimBA[source_semantic_flag] ) = TRUE (),
    "The reported forecast series shows a persistent level offset, but available EIA metadata does not resolve whether this reflects forecast-process bias, reporting-scope differences, resubmission behavior, or another source-definition effect."
)
```

The demand-band view (7) is kept because it adds information not visible elsewhere: ISNE's bias concentrates in its lowest quintile, and PSCO's deepens with demand. A peak/non-peak visual is omitted because peak robustness is already shown in card 3.

---

## Annotations

**P1-A (headline):**
> Forecast error is not equally correctable across systems. ISNE, PJM and SOCO show persistent directional bias that a simple causal historical correction reduced in all 12 quarters (−0.70 to −1.37 pp WAPE; −28% to −55% relative). AECI and BPAT are already effectively unbiased and gain nothing from the same adjustment (+0.07 pp and −0.01 pp). TVA shows persistent bias, but correcting it changes WAPE by only −0.05 pp (−2.2%).

**P1-B (footer):**
> Source: U.S. EIA Form EIA-930 (hourly demand and day-ahead demand forecast), Sep 2023 – Aug 2026, retrieved 2026-09-24. Independent analysis of public data. PNM and PSCO: the reported forecast series shows a persistent level offset whose cause (forecast process, reporting scope, resubmission or definition) is not resolved by EIA metadata. WAPE change = corrected − published on identical hours.

**P2-A (callout):**
> Correction helps only when directional error is stable. The trailing adjustment uses residuals from days D−29 to D−2 only. Where hour-specific bias repeats (ISNE overnight, PJM late evening and overnight) or a uniform offset persists (SOCO), it reduced error in every quarter. Where bias is near zero (AECI, BPAT), it adds nothing (BPAT −0.01 pp) or slightly worsens WAPE (AECI +0.07 pp, +2.8%).

**P2-B (footer):**
> Reference hour = BA reporting clock (PNM reports on fixed MST). Seasonal naive = same reference-clock hour 7 days earlier. Quarter = meteorological season × year. Demand quintiles and peaks use actual demand for retrospective segmentation only.

## As built (Power BI Service, 2026-09-26; presentation pass 2026-09-28)

Both pages were built in the Power BI Service report editor on the reconciled model. Value checks are in `docs/powerbi_reconciliation.md` ("Report page check"). The build differs from the specification above as follows. None of these changes alter a measure or an analytical definition.

**Whole report**
- The canvas is 1920 × 1080, so positions above were scaled by 1.5.
- The default Power BI theme is used. The theme colours above were not applied.
- Model option Auto date/time was left on. Its hidden date tables are not used by any measure.

**Page 1** (revised 2026-09-28)
- The title text box reads "Forecast Performance Review" with a one-line subtitle. Below it, a 12 pt headline states: "Forecast error is not equally correctable across systems: ISNE, PJM and SOCO show persistent bias that simple causal correction reduces consistently, while AECI and BPAT gain little or nothing from the same adjustment." PNM and PSCO are deliberately not in the headline.
- Cards use static titles instead of the dynamic `KPI Title …` measures.
- Card 7 is two cards: "Change in average WAPE (pp)" and "Change in average WAPE (relative)". The relative card is average corrected WAPE ÷ average published WAPE − 1 on common hours. It is not the mean of each BA's relative change, and its subtitle says so.
- Card 8 is two cards (Paired hours in view, BAs in view). The Paired Hours card shows 210K because the card's display units could not be changed in the web editor. The exact value, 210,278, is confirmed in DAX.
- The WAPE bar chart has no data labels. When enabled, the published and corrected labels collided for AECI, TVA and BPAT, where the two values are close. Values are in the tooltip and the attention table. The series key is in the subtitle (light blue = published, dark blue = bias-corrected) instead of a legend, so all eight BAs fit without scrolling.
- The bias bar chart uses one neutral colour, not `Bias Direction Color`, and has a dashed constant line at 0 on the value axis.
- The attention table sorts by `ba_code`. Text wraps in every column, and column widths are set so all ten columns and all eight rows are visible without scrolling or hover. `Source Semantics Flag` shows SOURCE SEMANTICS UNCERTAIN for PNM and PSCO as plain text, without the amber background.

**Page 2**
- The BA slicer is a single-select vertical list, not a dropdown. The default is ISNE.
- The status area (visual 3) is a one-row table instead of a multi-row card. The source flag is plain text.
- The hour and quarterly line charts have no separate constant line or markers.
- The Source Semantics Note (visual 9) is a one-column table so the text wraps. It is blank for unflagged BAs.
- The callout adds the TVA sentence from P1-A and a peak-robustness sentence. The footer adds that bias shape is a descriptive label.

**Evidence captured**

Screenshots are cropped to the report canvas, with no account, workspace or browser details:
- `docs/evidence/model_diagram.png`: model view with the two relationships; BAMetricSummary is disconnected. Captured 2026-09-26; the model has not changed since.
- `docs/evidence/page1_forecast_performance_review.png`: category slicer = All.
- `docs/evidence/page2_error_patterns_ISNE.png`: default BA.
- `docs/evidence/page2_error_patterns_PNM.png`: a source-flagged BA, showing the warning and note.
- `reports/demand_forecast_performance.pdf`: the service's PDF export of both pages (current values = defaults).

**Not committed**
- **PBIX:** the service offers "Download this file" (report and data). The downloaded file's `Connections` part contains the workspace identifier, and its compressed data model embeds the Power Query source. The source points to a private cloud-storage location that cannot be inspected or redacted here.
- **TMDL:** TMDL View (Preview) is available in the web modelling view and was used for the `+ 0` fix. No TMDL export-to-file control was found. The measure definitions are kept in `docs/dax_measures.md` instead.
