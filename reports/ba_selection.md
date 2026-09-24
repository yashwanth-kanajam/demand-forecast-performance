# Coverage Gate and BA Selection

Run: 2026-09-24. Source files retrieved 2026-09-24 19:06–19:08 UTC; all were last modified by EIA on 2026-09-24. Full provenance, including SHA-256 hashes, is in `data/curated/run_manifest.json`.

## Verdict: PASS

50 of 55 candidate BAs pass all three thresholds (actual, forecast and paired coverage ≥ 95%). The requirement was at least 5.

## Window

`[2023-09-01 00:00, 2026-09-01 00:00)` in each BA's reference-time calendar (the clock EIA reports the BA in; see docs/data_contract.md): 36 complete months and 26,304 expected UTC hours per BA. August 2026 is the last complete month on the retrieval date.

## Candidate population

55 U.S. demand-serving BAs appear in the files. Excluded before the gate were 10 generation-only BAs (AVRN, DEAA, GRID, GRIF, GWA, HGMA, SEPA, SIKE, WWA, YAD), which report no demand. Canadian and Mexican BAs are not in the BALANCE files.

Five BAs fail the gate: BHBA and SWPW (activated April 2026), WACM and WAUW (retired April 2026), and SPA (forecast coverage 92.16%).

## Selection

The criteria were applied in this order. **No forecast-error metric had been computed when the selection was made.**

1. **Gate PASS**: 50 BAs.
2. **Reporting stability**: every one of the 36 reference-time months has ≥ 95% paired coverage, which is the same gate applied at monthly grain. 29 BAs qualify. This excludes ERCO (one month at 90.32%), CISO (4 months), MISO (1 month) and SWPP (2 months).
3. **Pre-analysis quality-anomaly screen**, applied uniformly to all 29 BAs: exclude a BA if its reported forecast falls outside 0.5–2× its reported actual in more than 5% of hours. The initial screen excluded PSEI on this count without a stated cutoff. The 5% cutoff was formalized afterwards, still before any error metric was computed, and it does not change the selection. Applied to all 29 BAs it excludes one: **PSEI**, at 5,001 hours (19.0%). The next highest eligible BA is WALC at 248 hours (0.9%). This is recorded as a *pre-analysis quality anomaly / source-semantic concern requiring confirmation*. It is **not** confirmed bad data. Forecast-vs-actual divergence is partly the outcome this project studies, and PSEI's reported values may be correct. Confirming the cause would need information from EIA or PSEI that the files do not contain.
4. **Diversity** among the rest: one BA per EIA region where possible, a spread of time zones including one fixed-offset BA, scale from about 1.6 GW to 92 GW median demand, and a mix of organization types.

| BA | Region | Reference zone | Median demand (MW) | Paired % | Min monthly % | Why |
|---|---|---|--:|--:|--:|---|
| PJM | Mid-Atlantic | America/New_York | 91,870 | 99.54 | 96.53 | Largest RTO; Eastern DST |
| ISNE | New England | America/New_York | 12,866 | 99.99 | 99.85 | Northeast RTO; chosen over NYIS for higher, steadier coverage |
| SOCO | Southeast | America/Chicago | 26,058 | 99.98 | 99.55 | Large vertically integrated utility |
| TVA | Tennessee | America/Chicago | 18,136 | 99.98 | 99.73 | Federal utility |
| AECI | Midwest | America/Chicago | 2,337 | 100.00 | 100.00 | Small cooperative; complete record |
| PSCO | Northwest (Mountain) | America/Denver | 5,070 | 99.92 | 99.17 | Mountain time zone |
| BPAT | Northwest (Pacific) | America/Los_Angeles | 6,830 | 100.00 | 100.00 | Federal; Pacific time zone |
| PNM | Southwest | America/Phoenix (fixed MST) | 1,627 | 100.00 | 100.00 | Fixed-offset reporting (no DST) |

Eligible alternates: NYIS, DUK, TEC, IPCO.

Not represented: Texas and California. No large BA from either passes the monthly stability criterion. The only stable California BA is TIDC, at about 300 MW.

**Selection-bias disclosure:** selecting on reporting completeness may favour operationally mature BAs, and those may also forecast better. Results describe this population, not all U.S. BAs.

## Source audit

| Item | Value |
|---|---|
| Raw rows, all BAs, 7 files | 1,724,616 |
| Raw rows, 55 candidate BAs | 1,503,504 |
| Rows inside window (candidates) | 1,394,112 (every expected hour for the 50 passing BAs has a source row) |
| Duplicate BA + UTC keys | 0 |
| Conflicting duplicates | 0 |
| Missing usable actual hours (candidates) | 57,326 |
| Missing usable forecast hours (candidates) | 62,046 |
| Reference-time reproduction mismatches (vs EIA local columns) | 0, after the MISO/LGEE fixed-EST override (before it: 38,586 local-time and 1,608 local-date mismatches, all MISO/LGEE) |

Quality and revision flags. EIA publishes no per-value quality flag, but three signals exist:

- **`Demand (MW) (Imputed)`**: EIA's replacement value. When it appears next to a reported value, EIA has rejected that value (e.g. AVA 2025-04-22: reported 11,359 MW, imputed 1,466 MW). These hours are treated as missing actuals, and the imputed value is never used. Selected BAs: PSCO 15, TVA 4, SOCO 3 hours.
- **Revisions**: files are regenerated in place (all dated 2026-09-24) and the file does not record forecast vintage or resubmission.
- **Non-positive values**: selected BAs have 6 non-positive forecast hours, all PSCO, treated as missing.

**Observed source pattern:** PJM's actual and forecast values are blank for the whole of 5 of the 6 DST transition days in the window (2023-11-05, 2024-03-10, 2024-11-03, 2025-11-02, 2026-03-08). The rows exist but the values are empty. PSCO and SOCO also lose single hours on transition days. DST-day performance is therefore under-observed for PJM.

## Coverage table: all 55 candidate BAs

Bold = selected. "Min monthly" and "Months <95%" are paired coverage by reference-time month.

| BA | Name | Expected hrs | Actual hrs | Forecast hrs | Paired hrs | Actual % | Forecast % | Paired % | Gate | Min monthly paired % | Months <95% |
|---|---|--:|--:|--:|--:|--:|--:|--:|---|--:|--:|
| **AECI** | Associated Electric Cooperative, Inc. | 26,304 | 26,304 | 26,304 | 26,304 | 100.00 | 100.00 | 100.00 | PASS | 100.00 | 0 |
| AVA | Avista Corporation | 26,304 | 26,294 | 26,280 | 26,270 | 99.96 | 99.91 | 99.87 | PASS | 96.77 | 0 |
| AZPS | Arizona Public Service Company | 26,304 | 26,286 | 26,304 | 26,286 | 99.93 | 100.00 | 99.93 | PASS | 97.92 | 0 |
| BANC | Balancing Authority of Northern California | 26,304 | 26,286 | 26,211 | 26,194 | 99.93 | 99.65 | 99.58 | PASS | 93.00 | 2 |
| BHBA | Black Hills Energy | 26,304 | 2,184 | 2,184 | 2,160 | 8.30 | 8.30 | 8.21 | FAIL | 0.00 | 34 |
| **BPAT** | Bonneville Power Administration | 26,304 | 26,304 | 26,304 | 26,304 | 100.00 | 100.00 | 100.00 | PASS | 100.00 | 0 |
| CHPD | Public Utility District No. 1 of Chelan County | 26,304 | 26,303 | 26,304 | 26,303 | 100.00 | 100.00 | 100.00 | PASS | 99.87 | 0 |
| CISO | California Independent System Operator | 26,304 | 26,176 | 26,184 | 26,080 | 99.51 | 99.54 | 99.15 | PASS | 89.88 | 4 |
| CPLE | Duke Energy Progress East | 26,304 | 26,279 | 25,799 | 25,799 | 99.90 | 98.08 | 98.08 | PASS | 64.29 | 2 |
| CPLW | Duke Energy Progress West | 26,304 | 26,279 | 25,679 | 25,679 | 99.90 | 97.62 | 97.62 | PASS | 51.61 | 2 |
| DOPD | PUD No. 1 of Douglas County | 26,304 | 26,304 | 26,304 | 26,304 | 100.00 | 100.00 | 100.00 | PASS | 100.00 | 0 |
| DUK | Duke Energy Carolinas | 26,304 | 26,279 | 26,255 | 26,255 | 99.90 | 99.81 | 99.81 | PASS | 96.43 | 0 |
| EPE | El Paso Electric Company | 26,304 | 26,253 | 26,280 | 26,229 | 99.81 | 99.91 | 99.71 | PASS | 93.55 | 1 |
| ERCO | Electric Reliability Council of Texas, Inc. | 26,304 | 26,256 | 26,256 | 26,232 | 99.82 | 99.82 | 99.73 | PASS | 90.32 | 1 |
| FMPP | Florida Municipal Power Pool | 26,304 | 26,232 | 25,779 | 25,712 | 99.73 | 98.00 | 97.75 | PASS | 66.02 | 3 |
| FPC | Duke Energy Florida, Inc. | 26,304 | 26,279 | 26,254 | 26,254 | 99.90 | 99.81 | 99.81 | PASS | 96.43 | 0 |
| FPL | Florida Power & Light Co. | 26,304 | 26,169 | 26,181 | 26,073 | 99.49 | 99.53 | 99.12 | PASS | 89.46 | 1 |
| GCPD | Public Utility District No. 2 of Grant County, Washington | 26,304 | 26,302 | 26,264 | 26,264 | 99.99 | 99.85 | 99.85 | PASS | 94.89 | 1 |
| GVL | Gainesville Regional Utilities | 26,304 | 25,962 | 26,164 | 25,888 | 98.70 | 99.47 | 98.42 | PASS | 86.42 | 4 |
| HST | City of Homestead | 26,304 | 26,300 | 26,231 | 26,227 | 99.98 | 99.72 | 99.71 | PASS | 96.43 | 0 |
| IID | Imperial Irrigation District | 26,304 | 25,839 | 26,011 | 25,644 | 98.23 | 98.89 | 97.49 | PASS | 86.55 | 8 |
| IPCO | Idaho Power Company | 26,304 | 26,304 | 26,304 | 26,304 | 100.00 | 100.00 | 100.00 | PASS | 100.00 | 0 |
| **ISNE** | ISO New England | 26,304 | 26,302 | 26,304 | 26,302 | 99.99 | 100.00 | 99.99 | PASS | 99.85 | 0 |
| JEA | JEA | 26,304 | 26,279 | 26,034 | 26,010 | 99.90 | 98.97 | 98.88 | PASS | 62.55 | 1 |
| LDWP | Los Angeles Department of Water and Power | 26,304 | 26,251 | 26,154 | 26,126 | 99.80 | 99.43 | 99.32 | PASS | 86.55 | 2 |
| LGEE | Louisville Gas and Electric Company and Kentucky Utilities Company | 26,304 | 26,287 | 26,304 | 26,287 | 99.94 | 100.00 | 99.94 | PASS | 97.85 | 0 |
| MISO | Midcontinent Independent System Operator, Inc. | 26,304 | 26,243 | 26,256 | 26,195 | 99.77 | 99.82 | 99.59 | PASS | 93.55 | 1 |
| NEVP | Nevada Power Company | 26,304 | 26,268 | 26,304 | 26,268 | 99.86 | 100.00 | 99.86 | PASS | 99.44 | 0 |
| NWMT | NorthWestern Corporation | 26,304 | 26,290 | 26,304 | 26,290 | 99.95 | 100.00 | 99.95 | PASS | 99.60 | 0 |
| NYIS | New York Independent System Operator | 26,304 | 26,293 | 26,189 | 26,178 | 99.96 | 99.56 | 99.52 | PASS | 96.64 | 0 |
| PACE | PacifiCorp East | 26,304 | 26,303 | 26,209 | 26,208 | 100.00 | 99.64 | 99.64 | PASS | 87.23 | 1 |
| PACW | PacifiCorp West | 26,304 | 26,304 | 26,304 | 26,304 | 100.00 | 100.00 | 100.00 | PASS | 100.00 | 0 |
| PGE | Portland General Electric Company | 26,304 | 26,304 | 26,304 | 26,304 | 100.00 | 100.00 | 100.00 | PASS | 100.00 | 0 |
| **PJM** | PJM Interconnection, LLC | 26,304 | 26,185 | 26,183 | 26,183 | 99.55 | 99.54 | 99.54 | PASS | 96.53 | 0 |
| **PNM** | Public Service Company of New Mexico | 26,304 | 26,304 | 26,304 | 26,304 | 100.00 | 100.00 | 100.00 | PASS | 100.00 | 0 |
| **PSCO** | Public Service Company of Colorado | 26,304 | 26,289 | 26,298 | 26,283 | 99.94 | 99.98 | 99.92 | PASS | 99.17 | 0 |
| PSEI | Puget Sound Energy, Inc. | 26,304 | 26,304 | 26,304 | 26,304 | 100.00 | 100.00 | 100.00 | PASS | 100.00 | 0 |
| SC | South Carolina Public Service Authority | 26,304 | 26,242 | 26,227 | 26,170 | 99.76 | 99.71 | 99.49 | PASS | 93.33 | 2 |
| SCEG | Dominion Energy South Carolina, Inc. | 26,304 | 25,871 | 25,557 | 25,389 | 98.35 | 97.16 | 96.52 | PASS | 70.93 | 9 |
| SCL | Seattle City Light | 26,304 | 26,300 | 26,277 | 26,274 | 99.98 | 99.90 | 99.89 | PASS | 96.91 | 0 |
| SEC | Seminole Electric Cooperative | 26,304 | 25,886 | 26,133 | 25,768 | 98.41 | 99.35 | 97.96 | PASS | 89.03 | 4 |
| **SOCO** | Southern Company Services, Inc. - Trans | 26,304 | 26,301 | 26,301 | 26,298 | 99.99 | 99.99 | 99.98 | PASS | 99.55 | 0 |
| SPA | Southwestern Power Administration | 26,304 | 26,226 | 24,243 | 24,175 | 99.70 | 92.16 | 91.91 | FAIL | 67.74 | 14 |
| SRP | Salt River Project Agricultural Improvement and Power District | 26,304 | 26,253 | 26,256 | 26,205 | 99.81 | 99.82 | 99.62 | PASS | 87.10 | 1 |
| SWPP | Southwest Power Pool | 26,304 | 26,279 | 25,824 | 25,799 | 99.90 | 98.18 | 98.08 | PASS | 48.39 | 2 |
| SWPW | Southwest Power Pool West Balancing Authority Area | 26,304 | 3,671 | 3,240 | 3,239 | 13.96 | 12.32 | 12.31 | FAIL | 0.00 | 32 |
| TAL | City of Tallahassee | 26,304 | 26,304 | 26,302 | 26,302 | 100.00 | 99.99 | 99.99 | PASS | 99.87 | 0 |
| TEC | Tampa Electric Company | 26,304 | 26,295 | 26,302 | 26,294 | 99.97 | 99.99 | 99.96 | PASS | 99.06 | 0 |
| TEPC | Tucson Electric Power | 26,304 | 26,183 | 26,176 | 26,103 | 99.54 | 99.51 | 99.24 | PASS | 86.67 | 3 |
| TIDC | Turlock Irrigation District | 26,304 | 26,253 | 26,301 | 26,253 | 99.81 | 99.99 | 99.81 | PASS | 96.77 | 0 |
| TPWR | City of Tacoma, Department of Public Utilities, Light Division | 26,304 | 26,304 | 26,304 | 26,304 | 100.00 | 100.00 | 100.00 | PASS | 100.00 | 0 |
| **TVA** | Tennessee Valley Authority | 26,304 | 26,300 | 26,304 | 26,300 | 99.98 | 100.00 | 99.98 | PASS | 99.73 | 0 |
| WACM | Western Area Power Administration - Rocky Mountain Region | 26,304 | 22,465 | 22,448 | 22,377 | 85.41 | 85.34 | 85.07 | FAIL | 0.00 | 6 |
| WALC | Western Area Power Administration - Desert Southwest Region | 26,304 | 26,249 | 26,256 | 26,201 | 99.79 | 99.82 | 99.61 | PASS | 95.83 | 0 |
| WAUW | Western Area Power Administration - Upper Great Plains West | 26,304 | 22,632 | 22,632 | 22,632 | 86.04 | 86.04 | 86.04 | FAIL | 0.00 | 5 |
