# Source-Semantics Audit: PNM and PSCO

Performed 2026-09-24 (Phase 2.5), before final conclusions. Only official EIA material and EIA-published data were used.

## Authoritative EIA statements

1. **EIA Hourly Electric Grid Monitor, "About" page** (https://www.eia.gov/electricity/gridmonitor/about, retrieved 2026-09-24):
   > "Electric systems produce demand forecasts aligned with the way they normally operate and account for electricity on their system. So, the demand forecasts incorporate the effects of commercial arrangements such as dynamic scheduling and pseudo-ties. This approach means that for some BAs, where a significant portion of their demand is outside their system or where other BAs control a significant amount of demand inside their system, the comparison between actual and forecast demand is not very meaningful."

   The same page states: "Daylight saving time transition days are often misreported, with duplicate values reported for the same hour, a missing value for an hour, or incorrect timestamps."

2. **Form EIA-930 Instructions** (https://www.eia.gov/survey/form/eia_930/instructions.pdf, retrieved 2026-09-24), Data Quality section:
   > "Demand forecast: If you do not produce a day-ahead demand forecast in the normal course of business that is directly comparable to actual demand as defined for this collection … you are not required to produce a consistent demand forecast for the purposes of EIA-930 reporting. Please report the day-ahead demand forecast generated in the normal course of business."

   The instructions also say respondents may resubmit corrected data "within 3 days or as soon as the actual data is available".

**Implication for every BA:** EIA does not require the reported forecast to be definitionally comparable to reported actual demand. A persistent level offset can therefore be a definitional difference rather than forecast-process error.

## PNM (Public Service Company of New Mexico)

| Check | Source | Result |
|---|---|---|
| BA activation, retirement or scope change | EIA-930 Reference Tables (BAs) | None listed |
| Time-zone handling | Reference Tables, row-level check | Reported on fixed MST ("Arizona"); 0 mismatches |
| Subregion structure | Reference Tables (BA Subregions) | Demand is reported by subregion: "PNM System Firm Load" (~71% of BA demand) plus 8 other entities, including Tri-State G&T (~17%), Los Alamos County, Kirtland AFB, Freeport, Kit Carson Electric Cooperative, City of Gallup, Jicarilla Apache Nation and Acoma Pueblo (NTUA retired 2021-04-14) |
| Actual demand internal consistency | EIA-930 SUBREGION files | Sum of subregions vs BA demand: normalized bias −0.20% (23,376 hours with all subregions) |
| Forecast = PNM System Firm Load only? | SUBREGION vs BALANCE | **No.** The forecast is +34.4% above that subregion. Against the whole BA it is −5.8%. |
| Forecast = BA minus any single subregion? | SUBREGION vs BALANCE | **No.** All 9 single-subregion exclusions were tested; the best (excluding LAC) still leaves −2.2%. Combinations were not searched, to avoid fitting. |
| Discontinuity in forecast/actual | BALANCE | None. The monthly median ratio stays at 0.92–0.97 across all 36 months. |
| Balance identity (demand vs net generation − interchange) | BALANCE | Within ±0.9% until June 2025, then +1.3% to +3.8% (and −10% to −12% in April–May 2026). This is a separate reporting-consistency signal that post-dates the forecast offset. |

**Status: unresolved.** PNM's BA demand includes substantial load of entities other than PNM, which is the situation EIA says can make actual-vs-forecast comparison "not very meaningful". But no authoritative document confirms what PNM's forecast covers.

## PSCO (Public Service Company of Colorado)

| Check | Source | Result |
|---|---|---|
| BA activation, retirement or scope change | Reference Tables (BAs) | None listed for PSCO; no subregions |
| Neighbour changes | Reference Tables (BA Connections) | WACM connection retired and SWPW connection activated 2026-04-01 (SPP West BA area). This is a neighbour change, not a PSCO scope change, and it post-dates the start of the divergence. |
| Actual demand internal consistency | BALANCE | Demand equals net generation − total interchange to within 0.02% in every month |
| Discontinuity | BALANCE, daily ratio | No step change. The monthly median forecast/actual ratio is 0.93–0.99 (2023–24) and 0.90–0.96 (2025), then declines from January 2026 (0.88) to 0.71–0.75 in June–August 2026. July forecast fell 15% year on year (5,664 → 4,792 MW) while July actual rose 12% (6,030 → 6,772 MW). |

**Status: unresolved.** The actual series is internally consistent, and the divergence sits in the forecast/actual relationship. No EIA metadata explains it.

## Classification

Both BAs are **retained** and flagged:

> **SOURCE-SEMANTIC / FORECAST-LEVEL ANOMALY.** The mathematical correction is real in the reported series, but this analysis cannot determine whether it represents forecast-process bias, a reporting-scope difference, resubmission behaviour, or another source-definition effect.

The flag is set in `config/pipeline.toml` (`[source_semantics]`). It is based on this audit, not on performance.
